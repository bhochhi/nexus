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
| Multiple objectives and streaming | `Check my checking balance and transfer $25 from checking to savings` | The read-only balance goal is completed first; the consequential transfer is explicitly offered next. In the WebSocket client, point out the ordered durable stream: the balance result arrives as a member-visible event before the transfer-continuation prompt, rather than waiting for one monolithic reply. The same event log can be replayed after reconnect. |
| Slot correction and continuity | Start a transfer; provide slots across several turns; at review say `Actually make it $200` | The same transfer plan stays active, replaces the amount, and requires a new confirmation. |
| Runtime skill addition | `I forgot my online ID` (before installation), install `online_id_recovery`, then repeat the request | The first request stays safely unsupported. The registered skill becomes routable without a process restart or graph recompilation. |
| Version upgrade and rollback | With online-ID `3.0.0` active, publish `3.0.1` with the visible response-copy change below; repeat `I forgot my online ID`; then reactivate `3.0.0` and repeat it once more | `active.yaml` moves to a new version/hash and catalog revision. New requests use `3.0.1`; the earlier immutable version remains available for rollback and for in-flight tasks. |
| Live MSR assignment | In the MSR UI, join `banking`. In the Member UI, ask for a person, answer `yes`, explain `My credit card balance is wrong`, and choose `banking` if asked. | The case is automatically assigned, the MSR receives a system summary, and both UIs switch to human-chat mode. |
| Live sentiment | While connected, send `I am so frustrated that my balance is still wrong`. | The MSR sentiment rail lights `Frustrated` and the trace records the classification without sending the utterance back through the conversational agent. |
| End and resume | Send `/end` from either UI. | The MSR tab closes, the member returns to the virtual assistant, and the assistant asks what else it can help with. |

## Live MSR setup

Install the UI extra, then start the API, Member UI, and MSR UI in separate
terminals:

```bash
python -m pip install -e '.[dev,ui]'
MODEL_PROVIDER=mock member-assistant-server --db data/live-demo.db
member-assistant-member-ui
member-assistant-msr-ui
```

Use `http://localhost:8501` for the member and `http://localhost:8502` for the
MSR. Reuse the same Member ID in a second member window to demonstrate durable
history and shared real-time responses. Start with no matching MSR online to
show the waiting and Cancel live support states, then bring an MSR online to
show automatic assignment.

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
