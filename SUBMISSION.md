# Submission — muShanghai 2026 Hackathon (Agents track)

## 100-word description

**Drop-in Guide** is the interaction-intelligence layer for dimOS guidance. The robot enters an unfamiliar building, runs OpenAI Vision against its camera frame, and *proposes* labels to the operator — "I see a tall white machine, is this a printer?" The operator confirms, corrects, or skips. Every navigation decision then writes to a JSONL audit trail with grounding tier and confidence, so visitors hear *why* the robot chose its path: *"Going to the copier — tagged a minute ago, confidence 0.91."* `lead_to` pauses and waits when a visitor falls behind. `express_uncertainty` speaks honestly when the match is weak. Built natively on macOS + dimOS PR 2245.

(100 words exactly.)

## Tracks

- **Primary:** Agents
- **Secondary:** Autonomy & Navigation

## Hardware

Unitree Go2 (loaned by Dimensional), Apple M4 Pro running native dimOS.

## Links

- GitHub: https://github.com/arome3/drop-in-guide
- Storyboard (12-shot demo plan): [STORYBOARD.md](STORYBOARD.md)
- Install (reproducible from scratch): [INSTALL.md](INSTALL.md)
- Onboarding (5-min for AI agents & humans): [AGENTS.md](AGENTS.md)

## Six custom skills (all live in `drop_in_guide/`)

1. `describe_scene` — synchronous OpenAI Vision caption of current camera frame
2. `note_tagged` / `note_skipped` — session log of confirms and skips during priming
3. `list_tagged_places` / `what_did_you_skip` / `narrate_tour` — reactive scene-memory Q&A
4. `log_nav_decision` / `recent_nav_decisions` — falsifiable audit trail (JSONL)
5. `lead_to` — visitor-aware guidance that pauses and speaks "I'll wait for you"
6. `express_uncertainty` — calibrated honesty when matches are weak

## Thesis

Existing guidance systems (AGIBOT's Guidance Assistance pillar, hospital wayfinders, museum guides) require **pre-mapped environments** and **operator-authored knowledge bases**. Drop-in Guide inverts that: the robot authors its own scene memory from a 5-minute walkthrough, asking the operator to verify AI-proposed labels. Then it guides any visitor through it using natural-language commands, with every navigation decision **legible and audit-grounded**. The methodology is a direct port of the operator-grounded verification pattern from Rehnova into physical space.

## Three intelligences

| Layer | Provided by | Role |
|---|---|---|
| Motion | Unitree Go2 + dimOS nav stack | Locomotion, obstacle avoidance |
| Task | dimOS skill runtime + Claude Sonnet 4.6 via MCP | Decide which skill to call when |
| **Interaction** ⭐ | **This project** | Generative priming + grounded narration + audit trail |
