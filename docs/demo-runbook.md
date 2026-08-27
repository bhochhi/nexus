# Conversation-first demo runbook

Use a fresh session for each numbered scenario. The assistant can recognize an
objective conversationally, but it may only complete work through an active,
governed skill. Unsupported requests receive controlled lane-setting copy; FAQ
answers are rendered only from approved knowledge retrieved by the FAQ skill.

| Demo | Suggested member utterances | What to point out |
| --- | --- | --- |
| Warm, in-lane conversation | `Hi` then `Can you help me plan a vacation?` | Friendly USAA-style reception; it does not invent travel advice or claim an action. It advertises only active capabilities. |
| Safety-critical skill gap | `I need to report fraud on my account` then `yes` | The platform acknowledges the unavailable fraud-reporting objective, writes a privacy-safe `skill_gap` event, and immediately offers the governed live-agent handoff. It does not investigate or provide fraud instructions without a registered fraud skill. |
| Four-turn escalation | Send four unrelated unsupported requests, such as `Tell me a joke`, `What is the weather?`, and `Can you plan my trip?` | The first three remain in lane. The fourth offers—not starts—a live-agent handoff. A recognized goal resets the counter. Set `HANDOFF_OFFER_TURN_THRESHOLD` to tune this by environment. |
| Declarative, grounded FAQ | `How does overdraft protection work?` | `approved_knowledge` retrieves an approved answer and includes its KB source/disclosure. |
| Guided skill | `What's my balance?` then `checking` | The assistant asks only for the required account, retains context, and calls the read-only balance capability. |
| Deterministic skill | `Transfer $50 from checking to savings` then `yes` | It presents an explicit review and does not submit until confirmation. |
| Interruption and resume | Start `I want to make a transfer`; then ask `What's my checking balance?`; then say `resume` | The transfer is paused, balance is completed, and the exact paused workflow resumes. |
| Multiple objectives | `Check my checking balance and transfer $25 from checking to savings` | The read-only balance goal is completed first; the consequential transfer is explicitly offered next. |
| Slot correction and continuity | Start a transfer; provide slots across several turns; at review say `Actually make it $200` | The same transfer plan stays active, replaces the amount, and requires a new confirmation. |
| Runtime skill addition | `I forgot my online ID` (before installation), install `online_id_recovery`, then repeat the request | The first request stays safely unsupported. The registered skill becomes routable without a process restart or graph recompilation. |
| Version upgrade and rollback | With online-ID `3.0.0` active, publish `3.0.1` with the visible response-copy change below; repeat `I forgot my online ID`; then reactivate `3.0.0` and repeat it once more | `active.yaml` moves to a new version/hash and catalog revision. New requests use `3.0.1`; the earlier immutable version remains available for rollback and for in-flight tasks. |

## Presenter guardrails

- Do not describe model goal recognition as permission to answer. It only routes
  toward the active catalog.
- Show the catalog revision or active-skill list before and after installing the
  online-ID skill.
- For the version-upgrade demo, change the unpublished source artifact's
  `metadata.version` from `3.0.0` to `3.0.1` and make this response-template
  change before publishing:

  ```yaml
  response_template: "Use the upgraded approved online-ID recovery page: {url}. I won't display or infer your ID here."
  ```

  The changed member-visible wording is an intentional demo marker. Keep
  `config.destination: online_id_recovery` unchanged: the approved navigation
  adapter, not a business-authored skill, owns the destination-to-URL mapping.
- Never edit a published `skills/catalog/.../SKILL.md` directly. The publisher
  rejects changed content at an existing version. Publish the new version from
  `skills/available/.../SKILL.md`, then use the skill lifecycle command to
  activate or roll back a specific immutable artifact.
- For consequential work, emphasize the policy and confirmation gates as well
  as the conversational behavior.
