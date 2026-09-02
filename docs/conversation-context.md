# Conversation context and memory policy

The assistant persists the complete conversation for session continuity, replay,
audit, and the member interface. Persisting a message does not automatically put
that message into every model request. Provider calls are deliberately supplied
with a smaller working context selected for the current turn.

## Context supplied on every semantic turn

The current POC sends the model:

- the current member utterance;
- the active task, or the queued task awaiting permission to start;
- the task's goal, status, accepted inputs, missing field, and pending question;
- the task's complete input schema and field descriptions;
- relevant transition, resume, and sentiment state; and
- the eight most recent member or assistant messages, with each message bounded
  to 500 characters.

The eight-message window is a POC default chosen to cover ordinary local
references such as “the second one,” “use that account,” and “make it two
hundred.” It is not the assistant's authoritative memory and it is not a promise
that every useful fact will always remain inside the window.

Authoritative task memory lives in durable structured state. Values understood
from the original request are attached to the appropriate active or queued goal.
The recent-message window is used for conversational interpretation and recovery,
not as a substitute for persisting accepted task inputs.

## Why the full transcript is not sent on every turn

Sending every prior message appears comprehensive, but it makes interpretation
less predictable as a conversation grows:

- Old and superseded values compete with the member's current instruction.
- Values from completed or unrelated goals can be assigned to the current task.
- Earlier goals can pull routing back toward work the member has already finished.
- Prompt size, latency, and model cost grow for the lifetime of the session.
- More member data is repeatedly disclosed to the model than the current task
  requires, conflicting with data-minimization goals.
- A prompt instruction such as “ignore unrelated history” is probabilistic; it is
  not an enforcement boundary.

For those reasons, the platform combines bounded recent dialogue with durable,
task-scoped state instead of treating the raw transcript as model memory.

## Reusing a value from history

A model may recover a still-missing value from recent history only through the
structured `context_recovery` binding. The update must identify the target field,
pass the field's schema validation, exceed the confidence threshold, and include
an exact evidence span from a prior member message. Assistant wording cannot be
used as evidence.

The intended policy is:

| Situation | Behavior |
|---|---|
| Same goal, unambiguous member evidence, field still missing | Recover the value and continue validation. |
| Same goal, ambiguous field or role | Ask a targeted clarification instead of guessing. |
| Different goal, member explicitly refers to the earlier value now | Interpret the new reference and validate it for the current goal. |
| Different goal, no explicit current reference | Do not silently reuse it; ask before copying it. |
| Value was corrected or superseded | Do not recover the older value. |

Consequential workflows retain their normal review and explicit confirmation
requirements after slot collection. That final confirmation does not make an
unsupported cross-goal slot assignment safe; the assignment itself must first
meet the context and evidence rules.

## Evolution beyond the POC

If conversations routinely exceed the recent-message window, increasing the
window indefinitely is not the preferred solution. The next step is task-scoped
semantic memory containing candidate facts with:

- task or goal identity;
- candidate field and normalized value;
- source message identifier and evidence span;
- confidence;
- accepted, rejected, or superseded status; and
- whether member clarification is required before use.

Older context could then be retrieved by task and evidence rather than replaying
the complete transcript. The recent-message limit should eventually become a
configuration value and be evaluated with conversation-length, cross-goal
contamination, recovery, latency, token-use, and privacy tests.
