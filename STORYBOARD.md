# 90-second demo storyboard

Built for the **muShanghai 2026** hackathon (Agents track submission). 12 shots, ~90 seconds total.

---

## ACT I — PRIMING (0–35s)

| Shot | Sec | Action | Skills fired |
|---|---|---|---|
| 1 | 0–5 | Cold open. Operator: *"Hey — let's learn this place."* | (Whisper → `agent_send`) |
| 2 | 5–10 | Robot: *"Got it. I'll explore and ask you about what I see."* | `speak` |
| 3 | 10–18 | Robot looks at a tall white machine. *"I see a tall white machine to my right. Is this a printer?"* Operator: *"Yes — that's a printer."* | `describe_scene` → `speak` → `tag_location` + `note_tagged` |
| 4 | 18–26 | **Correction beat.** Robot near a copier: *"Is this another printer?"* Operator: *"No — that's a copier."* | `describe_scene` → `speak` → `tag_location("copier")` + `note_tagged` |
| 5 | 26–33 | Robot near a green plant: *"Is this important?"* Operator: *"Skip it."* | `describe_scene` → `speak` → `note_skipped("a green plant")` |
| 6 | 33–35 | Operator: *"That's enough."* Robot: *"I learned 2 places."* PIP shows scene map with 2 pins. | `speak` |

## ACT II — GUIDANCE (35–75s)

| Shot | Sec | Action | Skills fired |
|---|---|---|---|
| 7 | 35–42 | Visitor: *"Take me to the copier."* Robot: *"Going to the copier — tagged a minute ago, confidence 0.91."* Rerun PIP shows audit panel updating. | `log_nav_decision(query, "tagged", 0.91, "copier")` → `speak` → `navigate_with_text("copier")` |
| 8 | 42–55 | Visitor stops to read a sign and falls behind. Robot detects drop, pauses, speaks *"I'll wait for you."* Visitor catches up. | `lead_to` (combines `navigate_with_text` + `follow_person` state monitoring) |
| 9 | 55–65 | Robot arrives at copier: *"Here's the copier. Anything else?"* | `speak` |

## ACT III — Q&A CALLBACK + CLOSE (65–90s)

| Shot | Sec | Action | Skills fired |
|---|---|---|---|
| 10 | 65–77 | Visitor: *"Earlier you skipped something — what was it?"* Robot: *"I skipped one object during priming: a green plant. Want me to revisit it?"* | `what_did_you_skip` → `speak` |
| 11 | 77–85 | Visitor: *"Maybe next time. Thanks."* Robot: *"You're welcome."* | `speak` |
| 12 | 85–90 | End card: **Drop-in Guide · dimOS · Unitree Go2 · muShanghai 2026** + GitHub URL | — |

---

## Audio script (memorize for the take)

| Shot | Robot says |
|---|---|
| 2 | *"Got it. I'll explore and ask you about what I see."* |
| 3 | *"I see a tall white machine to my right. Is this a printer?"* |
| 4a | *"I see another machine. Is this another printer?"* |
| 4b | *"Got it. Tagging the copier."* |
| 5a | *"I see a green plant on a stand. Is this important?"* |
| 5b | *"Skipping."* |
| 6 | *"I learned 2 places."* |
| 7 | *"Going to the copier — I tagged it a minute ago, confidence 0.91."* |
| 8 | *"I'll wait for you."* |
| 9 | *"Here's the copier. Anything else you want to know?"* |
| 10 | *"I skipped one object during priming — a green plant on a stand. Want me to revisit it?"* |
| 11 | *"You're welcome."* |

---

## Hierarchy of importance (if cutting for time)

1. **Shot 3, 4, 7** — the thesis carriers (proposal, correction, grounded narration). Cannot cut.
2. **Shot 8** — the defining emotional moment. Cut only if hardware fails.
3. **Shot 10** — proves memory is queryable. Strong but cuttable.
4. **Shot 1, 5, 6** — voice trigger, skip beat, transition. Polish.

In a worst-case forced 60s edit: 1, 3, 4, 7, 9, 10, 12.

## Optional beats (if time/material allows)

- **Tour mode**: visitor says "give me a quick tour" → robot calls `narrate_tour` → speaks: *"Here's the tour. I know 2 places: the printer, and the kitchen — both tagged a minute ago. Just say the word."* Adds a proactive feel.
- **Confidence beat**: visitor asks about a place that wasn't tagged → robot calls `express_uncertainty` → speaks: *"I'm not sure about the bathroom — I haven't tagged it. Want me to make a best guess, or wait?"* Demonstrates calibrated honesty.
- **Time-aware memory**: list_tagged_places now says "tagged about a minute ago" instead of just "tagged". Subtle but reinforces persistence.
