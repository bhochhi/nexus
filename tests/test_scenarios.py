from member_assistant.config import PROJECT_ROOT
from member_assistant.providers import (
    DeterministicProvider,
    GoalAnalysis,
    GoalMatch,
    SkillGap,
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
    def analyze_message(self, message, catalog, context=None):
        analysis = super().analyze_message(message, catalog, context)
        if not analysis.goals and "online id" in message.casefold():
            return GoalAnalysis(
                goals=[],
                skill_gap=SkillGap(
                    objective="recover your online ID",
                    category="online_id_recovery",
                    confidence=0.96,
                ),
            )
        return analysis


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
    assert "Review mock transfer" in first.text
    assert first.text.index("$2,450.75") < first.text.index("Review mock transfer")
    assert runtime.tools.transfers.submission_count == 0
    state = runtime.inspect_state("multi")
    assert state["active_task"]["skill_name"] == "internal_transfer"
    assert state["active_task"]["status"] == "awaiting_confirmation"

    second = runtime.chat("multi", "yes")
    assert "Mock transfer completed" in second.text
    assert runtime.tools.transfers.submission_count == 1


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

    runtime.catalog.install(PROJECT_ROOT / "skills" / "available" / "online_id.json")

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
    runtime.catalog.install(PROJECT_ROOT / "skills" / "available" / "online_id.json")

    reply = runtime.chat("gap-closed", "recover my online id")

    assert reply.selected_skill == "online_id_recovery"
    assert "approved online-ID recovery page" in reply.text
    assert not any(
        event["event_type"] == "skill_gap"
        for event in runtime.store.audit_events("gap-closed")
    )


def test_repeated_no_goal_turns_offer_but_do_not_auto_start_handoff(runtime_factory):
    runtime = runtime_factory()

    runtime.chat("no-goal", "purple clouds")
    runtime.chat("no-goal", "still not that")
    offer = runtime.chat("no-goal", "nothing matched")

    assert "Would you like me to connect" in offer.text
    state = runtime.inspect_state("no-goal")
    assert state["pending_handoff_offer"] is not None
    assert state["handoff_status"] is None

    declined = runtime.chat("no-goal", "no")
    assert "won't connect" in declined.text
    assert runtime.inspect_state("no-goal")["pending_handoff_offer"] is None


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
