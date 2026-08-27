from member_assistant.config import PROJECT_ROOT
from member_assistant.providers import (
    DeterministicProvider,
    GoalMatch,
    SkillGap,
    SlotUpdate,
    TurnAnalysis,
)


class _NoisyBalanceProvider(DeterministicProvider):
    """Simulates an LLM that speculatively fills account from the intent text."""

    def identify_goals(self, message, catalog, context=None):
        if "balance" in message.casefold():
            return [
                GoalMatch(
                    skill_name="guided_balance",
                    goal="check_account_balance",
                    confidence=0.99,
                    inputs={"account": "balance"},
                )
            ]
        return super().identify_goals(message, catalog, context)


class _GapAwareProvider(DeterministicProvider):
    def understand_turn(self, message, catalog, context=None):
        analysis = super().understand_turn(message, catalog, context)
        if not analysis.goals and "online id" in message.casefold():
            return TurnAnalysis(
                goals=[],
                skill_gap=SkillGap(
                    objective="recover your online ID",
                    category="online_id_recovery",
                    confidence=0.96,
                ),
            )
        return analysis


class _DisplayNameGoalProvider(DeterministicProvider):
    """Simulates a semantic model returning a friendly label as the goal ID."""

    def understand_turn(self, message, catalog, context=None):
        if "online id" in message.casefold():
            return TurnAnalysis(
                goals=[
                    GoalMatch(
                        skill_name="online_id_recovery",
                        goal="recover your online ID",
                        confidence=0.86,
                    )
                ]
            )
        return super().understand_turn(message, catalog, context)


class _NaturalTurnProvider(DeterministicProvider):
    """Models semantic multi-slot extraction and natural-number normalization."""

    def understand_turn(self, message, catalog, context=None):
        analysis = super().understand_turn(message, catalog, context)
        normalized = message.casefold()
        slot_updates = list(analysis.slot_updates)
        conversation_act = analysis.conversation_act
        relation = analysis.active_goal_relation
        if "from saving to checking" in normalized:
            slot_updates.extend(
                [
                    SlotUpdate("source_account", "savings", 1.0),
                    SlotUpdate("destination_account", "checking", 1.0),
                ]
            )
            conversation_act = "provide_information"
            relation = "continue"
        if "two hundred" in normalized:
            slot_updates.append(SlotUpdate("amount", "200.00", 1.0))
            conversation_act = (
                "correction" if "actually" in normalized else "provide_information"
            )
            relation = "continue"
        if "one hundreds" in normalized:
            slot_updates.append(SlotUpdate("amount", "100.00", 0.98))
            conversation_act = "provide_information"
            relation = "continue"
        if "checking ending in 1001" in normalized:
            slot_updates.extend(
                [
                    SlotUpdate("source_account", "checking", 0.99),
                    SlotUpdate("amount", "1001", 0.20),
                ]
            )
            conversation_act = "provide_information"
            relation = "continue"
        return TurnAnalysis(
            goals=analysis.goals,
            skill_gap=analysis.skill_gap,
            slot_updates=slot_updates,
            conversation_act=conversation_act,
            active_goal_relation=relation,
        )


def test_grounded_faq_uses_approved_source(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat("faq", "How does overdraft protection work?")

    assert "linked savings account" in reply.text
    assert "KB-001" in reply.text
    assert reply.outcome["grounded"] is True
    assert reply.selected_skill == "approved_knowledge"


def test_speculative_model_slot_uses_neutral_elicitation_then_validates_reply(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NoisyBalanceProvider())

    prompt = runtime.chat("neutral-slot", "What about balance?")

    assert "Which account would you like" in prompt.text
    assert "couldn't match" not in prompt.text

    invalid = runtime.chat("neutral-slot", "my mystery account")
    assert "I couldn't match that account" in invalid.text

    completed = runtime.chat("neutral-slot", "2002")
    assert "$8,250.25" in completed.text


def test_balance_clarification_and_durable_resume_after_restart(runtime_factory):
    first_runtime = runtime_factory(db_name="durable.db")

    prompt = first_runtime.chat("balance", "What is my account balance?")
    assert "Which account" in prompt.text
    saved = first_runtime.inspect_state("balance")
    assert saved["pending_clarification"]["field"] == "account"
    first_runtime.close()

    second_runtime = runtime_factory(db_name="durable.db")
    answer = second_runtime.chat("balance", "saving 2002")

    assert "$8,250.25" in answer.text
    assert second_runtime.inspect_state("balance")["active_task"] is None


def test_transfer_requires_immediate_confirmation(runtime_factory):
    runtime = runtime_factory()

    review = runtime.chat("transfer", "Transfer $50 from checking to savings")

    assert "Review mock transfer" in review.text
    assert "yes or no" in review.text
    assert runtime.tools.transfers.submission_count == 0
    assert runtime.inspect_state("transfer")["confirmation_status"] == "pending"

    completed = runtime.chat("transfer", "yes")

    assert "Mock transfer completed" in completed.text
    assert "MOCK-" in completed.text
    assert runtime.tools.transfers.submission_count == 1
    audits = runtime.store.audit_events("transfer")
    assert any(event["event_type"] == "policy_approved" for event in audits)
    assert any(event["payload"].get("status") == "completed" for event in audits)


def test_pending_transfer_confirmation_survives_restart(runtime_factory):
    first_runtime = runtime_factory(db_name="confirmation.db")
    first_runtime.chat("confirmation", "Transfer $12 from checking to savings")
    first_runtime.close()

    second_runtime = runtime_factory(db_name="confirmation.db")
    completed = second_runtime.chat("confirmation", "yes")

    assert "Mock transfer completed" in completed.text
    assert second_runtime.tools.transfers.submission_count == 1


def test_multi_goal_orders_read_only_before_consequential(runtime_factory):
    runtime = runtime_factory()

    first = runtime.chat(
        "multi", "Check my balance and transfer $25 from checking to savings"
    )
    assert "$2,450.75" in first.text
    assert "I'll start by helping you check an account balance" in first.text
    assert "Would you like me to continue and make an internal transfer" in first.text
    assert "Review mock transfer" not in first.text
    assert runtime.tools.transfers.submission_count == 0
    state = runtime.inspect_state("multi")
    assert state["active_task"] is None
    assert state["queued_tasks"][0]["skill_name"] == "internal_transfer"
    assert state["pending_task_transition"] is not None

    second = runtime.chat("multi", "yes")
    assert "Review mock transfer" in second.text
    state = runtime.inspect_state("multi")
    assert state["active_task"]["skill_name"] == "internal_transfer"
    assert state["active_task"]["status"] == "awaiting_confirmation"

    third = runtime.chat("multi", "yes")
    assert "Mock transfer completed" in third.text
    assert runtime.tools.transfers.submission_count == 1


def test_member_can_decline_the_next_planned_goal(runtime_factory):
    runtime = runtime_factory()
    first = runtime.chat(
        "multi-decline", "Check my checking balance and transfer $25 to savings"
    )
    assert "$2,450.75" in first.text
    assert "Would you like me to continue" in first.text

    declined = runtime.chat("multi-decline", "no")

    assert "won't continue" in declined.text
    state = runtime.inspect_state("multi-decline")
    assert state["active_task"] is None
    assert state["queued_tasks"] == []
    assert state["pending_task_transition"] is None
    assert runtime.tools.transfers.submission_count == 0


def test_planned_goal_transition_survives_restart(runtime_factory):
    first_runtime = runtime_factory(db_name="planned-transition.db")
    first_runtime.chat(
        "multi-durable",
        "Check my checking balance and transfer $25 from checking to savings",
    )
    first_runtime.close()

    second_runtime = runtime_factory(db_name="planned-transition.db")
    continued = second_runtime.chat("multi-durable", "yes")

    assert "Review mock transfer" in continued.text
    assert second_runtime.inspect_state("multi-durable")["active_task"][
        "skill_name"
    ] == "internal_transfer"


def test_live_agent_handoff(runtime_factory):
    runtime = runtime_factory()

    offer = runtime.chat("handoff", "This is not helping—get me a person")

    assert "Would you like me to connect" in offer.text
    assert runtime.inspect_state("handoff")["pending_handoff_offer"] is not None
    assert runtime.inspect_state("handoff")["handoff_status"] is None

    reply = runtime.chat("handoff", "yes")

    assert "mock live agent" in reply.text
    assert "CASE-" in reply.text
    assert reply.outcome["status"] == "queued"
    assert "Goal:" in reply.outcome["summary"]
    assert runtime.inspect_state("handoff")["handoff_status"] == "queued"


def test_greeting_loads_mock_member_profile_and_explains_capabilities(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat("reception", "hello")

    assert reply.text.startswith("Hi Jordan.")
    assert "check an account balance" in reply.text
    assert "make an internal transfer" in reply.text
    assert "live agent" not in reply.text
    state = runtime.inspect_state("reception")
    assert state["member_profile"]["preferred_name"] == "Jordan"
    assert state["greeted"] is True


def test_reception_only_advertises_currently_installed_skills(runtime_factory):
    runtime = runtime_factory()

    before = runtime.chat("before-install", "hello")
    assert "recover your online ID" not in before.text

    runtime.catalog.install(
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )

    after = runtime.chat("after-install", "hello")
    assert "recover your online ID" in after.text


def test_no_goal_uses_friendly_catalog_aware_reception(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat("unavailable-online-id", "recover my online id")

    assert reply.text.startswith("Hi Jordan. Thanks for explaining.")
    assert "check an account balance" in reply.text
    assert "recover your online ID" not in reply.text


def test_clear_unsupported_objective_is_acknowledged_and_audited(runtime_factory):
    runtime = runtime_factory(provider=_GapAwareProvider())

    reply = runtime.chat("skill-gap", "recover my online id")

    assert "I understand that you'd like to recover your online ID" in reply.text
    assert "don't currently have the ability" in reply.text
    gap_events = [
        event
        for event in runtime.store.audit_events("skill-gap")
        if event["event_type"] == "skill_gap"
    ]
    assert len(gap_events) == 1
    assert gap_events[0]["payload"]["category"] == "online_id_recovery"
    assert gap_events[0]["payload"]["objective"] == "recover your online ID"
    assert gap_events[0]["payload"]["confidence"] == 0.96
    assert "member_message" not in gap_events[0]["payload"]


def test_fraud_reporting_gap_offers_handoff_immediately(runtime_factory):
    runtime = runtime_factory()

    reply = runtime.chat("fraud-gap", "I need to report fraud on my account")

    assert "report suspected fraud" in reply.text
    assert "Would you like me to connect" in reply.text
    assert runtime.inspect_state("fraud-gap")["pending_handoff_offer"] is not None
    gap_events = runtime.store.audit_events("fraud-gap")
    assert any(
        event["event_type"] == "skill_gap"
        and event["payload"]["category"] == "fraud_reporting"
        for event in gap_events
    )


def test_skill_gap_during_slot_collection_preserves_the_active_goal(runtime_factory):
    runtime = runtime_factory(provider=_GapAwareProvider())
    runtime.chat("gap-interruption", "check my balance")

    reply = runtime.chat("gap-interruption", "recover my online id")

    assert "I understand that you'd like to recover your online ID" in reply.text
    assert "Your current request is still here" in reply.text
    state = runtime.inspect_state("gap-interruption")
    assert state["active_task"]["skill_name"] == "guided_balance"
    assert state["active_task"]["status"] == "awaiting_input"


def test_installed_skill_is_not_reported_as_a_gap(runtime_factory):
    runtime = runtime_factory(provider=_GapAwareProvider())
    runtime.catalog.install(
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )

    reply = runtime.chat("gap-closed", "recover my online id")

    assert reply.selected_skill == "online_id_recovery"
    assert "approved online-ID recovery page" in reply.text
    assert not any(
        event["event_type"] == "skill_gap"
        for event in runtime.store.audit_events("gap-closed")
    )


def test_display_name_goal_is_canonicalized_without_false_clarification(
    runtime_factory,
):
    runtime = runtime_factory(provider=_DisplayNameGoalProvider())
    runtime.catalog.install(
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )

    reply = runtime.chat("goal-alias", "What is my online ID?")

    assert reply.selected_skill == "online_id_recovery"
    assert "approved online-ID recovery page" in reply.text
    assert runtime.inspect_state("goal-alias")["pending_goal_clarification"] is None


def test_persisted_duplicate_goal_clarification_recovers_on_yes(runtime_factory):
    runtime = runtime_factory(provider=_DisplayNameGoalProvider())
    runtime.catalog.install(
        PROJECT_ROOT
        / "skills"
        / "available"
        / "online_id_recovery"
        / "SKILL.md"
    )
    state = runtime.inspect_state("old-goal-alias")
    state["pending_goal_clarification"] = {
        "candidates": [
            {
                "skill_name": "online_id_recovery",
                "goal": "recover your online ID",
                "confidence": 0.86,
                "inputs": {},
            },
            {
                "skill_name": "online_id_recovery",
                "goal": "recover_online_id",
                "confidence": 0.84,
                "inputs": {},
            },
        ],
        "question": "Did you want to recover your online ID or recover your online ID?",
    }
    runtime.store.save("old-goal-alias", state)

    reply = runtime.chat("old-goal-alias", "yes")

    assert reply.selected_skill == "online_id_recovery"
    assert "approved online-ID recovery page" in reply.text
    assert runtime.inspect_state("old-goal-alias")["pending_goal_clarification"] is None


def test_repeated_no_goal_turns_offer_but_do_not_auto_start_handoff(runtime_factory):
    runtime = runtime_factory()

    for index in range(3):
        reply = runtime.chat("no-goal", "unsupported topic {}".format(index))
        assert "Would you like me to connect" not in reply.text
    offer = runtime.chat("no-goal", "still unsupported")

    assert "Would you like me to connect" in offer.text
    state = runtime.inspect_state("no-goal")
    assert state["pending_handoff_offer"] is not None
    assert state["handoff_status"] is None

    declined = runtime.chat("no-goal", "no")
    assert "won't connect" in declined.text
    assert runtime.inspect_state("no-goal")["pending_handoff_offer"] is None


def test_unsupported_turn_counter_is_not_reset_by_a_greeting(runtime_factory):
    runtime = runtime_factory()

    for index in range(3):
        runtime.chat("no-goal-greeting", "unsupported topic {}".format(index))
    runtime.chat("no-goal-greeting", "hello")
    offer = runtime.chat("no-goal-greeting", "one more unsupported topic")

    assert "Would you like me to connect" in offer.text


def test_ambiguous_goals_are_clarified_and_answer_is_durable(runtime_factory):
    first_runtime = runtime_factory(db_name="goal-clarification.db")

    question = first_runtime.chat("ambiguous", "balance transfer")

    assert "Did you want to" in question.text
    state = first_runtime.inspect_state("ambiguous")
    assert len(state["pending_goal_clarification"]["candidates"]) == 2
    first_runtime.close()

    second_runtime = runtime_factory(db_name="goal-clarification.db")
    selected = second_runtime.chat("ambiguous", "balance")
    assert "Which account" in selected.text
    assert second_runtime.inspect_state("ambiguous")["selected_skill"] == "guided_balance"


def test_natural_slot_answers_continue_transfer_without_reclassifying(runtime_factory):
    runtime = runtime_factory()

    source = runtime.chat("natural-slots", "I want to make a transfer")
    assert "money come from" in source.text

    destination = runtime.chat("natural-slots", "checking in 1001")
    assert "receive the money" in destination.text

    amount = runtime.chat("natural-slots", "saving 2002")
    assert "How much" in amount.text

    review = runtime.chat("natural-slots", "$25 please")
    assert "Review mock transfer" in review.text
    assert "Checking ending in 1001" in review.text
    assert "Savings ending in 2002" in review.text


def test_semantic_turn_understanding_collects_multiple_slots_and_word_amount(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NaturalTurnProvider())

    source = runtime.chat("semantic-slots", "I want to make a transfer")
    assert "money come from" in source.text

    accounts = runtime.chat("semantic-slots", "from saving to checking")
    assert "How much" in accounts.text
    assert "source account and destination account" in accounts.text
    state = runtime.inspect_state("semantic-slots")
    assert state["active_task"]["inputs"]["source_account"] == "savings"
    assert state["active_task"]["inputs"]["destination_account"] == "checking"
    assert state["no_goal_turn_count"] == 0

    review = runtime.chat("semantic-slots", "two hundred")
    assert "$200.00" in review.text
    assert "Savings ending in 2002" in review.text
    assert "Checking ending in 1001" in review.text
    assert "live agent" not in review.text


def test_semantic_turn_understanding_normalizes_disfluent_word_amount(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NaturalTurnProvider())
    runtime.chat("semantic-disfluency", "I want to make a transfer")
    runtime.chat("semantic-disfluency", "from saving to checking")

    review = runtime.chat("semantic-disfluency", "one hundreds dollar")

    assert "$100.00" in review.text
    assert "Review mock transfer" in review.text


def test_uninterpreted_word_amount_is_reelicited_not_reported_as_over_limit(
    runtime_factory,
):
    runtime = runtime_factory()
    runtime.chat("amount-retry", "I want to make a transfer")
    runtime.chat("amount-retry", "checking")
    runtime.chat("amount-retry", "saving")

    retry = runtime.chat("amount-retry", "one hundreds dollar")

    assert "How much would you like to transfer" in retry.text
    assert "configured transfer limit" not in retry.text
    assert "amount" not in runtime.inspect_state("amount-retry")["active_task"]["inputs"]


def test_semantic_correction_revalidates_and_replaces_confirmation(runtime_factory):
    runtime = runtime_factory(provider=_NaturalTurnProvider())
    first_review = runtime.chat(
        "semantic-correction", "Transfer $50 from checking to savings"
    )
    assert "$50.00" in first_review.text

    corrected_review = runtime.chat(
        "semantic-correction", "actually make it two hundred"
    )

    assert "$200.00" in corrected_review.text
    assert "I've updated the amount" in corrected_review.text
    assert "Confirm this transfer" in corrected_review.text
    state = runtime.inspect_state("semantic-correction")
    assert state["confirmation_status"] == "pending"
    assert state["active_task"]["inputs"]["amount"] == "200.00"
    assert state["outcome"] is None


def test_semantic_understanding_continues_an_inflight_deactivated_version(
    runtime_factory,
):
    runtime = runtime_factory(provider=_NaturalTurnProvider())
    runtime.chat("semantic-pinned", "I want to make a transfer")
    runtime.catalog.deactivate("internal_transfer")

    reply = runtime.chat("semantic-pinned", "from saving to checking")

    assert "How much" in reply.text
    state = runtime.inspect_state("semantic-pinned")
    assert state["active_task"]["skill_version"] == "2.0.0"
    assert state["active_task"]["inputs"]["source_account"] == "savings"
    assert state["active_task"]["inputs"]["destination_account"] == "checking"


def test_low_confidence_account_suffix_is_not_accepted_as_amount(runtime_factory):
    runtime = runtime_factory(provider=_NaturalTurnProvider())
    runtime.chat("semantic-confidence", "I want to make a transfer")

    reply = runtime.chat("semantic-confidence", "checking ending in 1001")

    assert "receive the money" in reply.text
    state = runtime.inspect_state("semantic-confidence")
    assert state["active_task"]["inputs"]["source_account"] == "checking"
    assert "amount" not in state["active_task"]["inputs"]


def test_clear_new_goal_interrupts_slot_collection_then_offers_resume(runtime_factory):
    runtime = runtime_factory()
    runtime.chat("context-switch", "I want to make a transfer")

    balance = runtime.chat("context-switch", "What is my checking balance?")

    assert "$2,450.75" in balance.text
    assert "resume or discard" in balance.text
    state = runtime.inspect_state("context-switch")
    assert state["paused_tasks"][0]["skill_name"] == "internal_transfer"


def test_policy_denies_account_data_when_not_authenticated(runtime_factory):
    runtime = runtime_factory()
    runtime.authenticated = False

    reply = runtime.chat("signed-out", "What is my balance?")

    assert "sign in" in reply.text
    assert reply.outcome["status"] == "policy_denied"
    assert runtime.tools.transfers.submission_count == 0
