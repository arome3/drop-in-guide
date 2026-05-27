# AGENTS.md — Drop-in Guide

A guide for AI coding agents (Cursor, Claude Code, Codex, etc.) and human collaborators picking up this codebase. Keep it under 200 lines.

## What this is

Drop-in Guide is an **interaction-intelligence layer on top of [dimOS](https://github.com/dimensionalOS/dimos)** for the Unitree Go2 quadruped. It teaches the robot to:

1. **Prime** an unfamiliar building by asking the operator to verify AI-proposed labels (generative priming).
2. **Guide** visitors through it via natural-language commands, with grounded narration before every action.
3. **Audit** every navigation decision into a JSONL trace — falsifiable evidence the agent did what it said.
4. **Adapt**: pause + speak *"I'll wait for you"* when a visitor falls behind; calibrate uncertainty before acting on weak matches.

Submitted to the **Agents track** of the muShanghai 2026 hackathon. Companion to dimOS PR 2245 (`danvi/experimental/route-replay-through-SHM`, the team's macOS branch).

## Architecture

```
drop_in_guide/
├── blueprint.py                  ← dimOS Blueprint + Claude Sonnet 4.6 wiring + system prompt
├── scene_caption_skill.py        ← describe_scene  (OpenAI Vision)
├── reactive_qa_skills.py         ← note_tagged, note_skipped, list_tagged_places,
│                                    what_did_you_skip, narrate_tour, express_uncertainty
├── decision_audit_skill.py       ← log_nav_decision, recent_nav_decisions  (JSONL trace)
├── lead_with_follow_skill.py     ← lead_to  (the defining gesture)
└── drop_in_guide_speak.py        ← (in progress) WebRTC AUDIO_HUB_REQ bridge for Go2 speaker
```

Everything runs **inside the dimOS package tree** — copy these files under `dimos/experimental/` and the blueprint under `dimos/robot/unitree/go2/blueprints/agentic/drop_in_guide.py`. See [INSTALL.md](INSTALL.md).

## How the pieces connect

```
┌──────────────────────────────────────────────────────────────┐
│  blueprint.py (drop_in_guide)                                │
│  autoconnect(                                                │
│    unitree_go2,                  ◀── dimOS base (skips      │
│                                       CUDA-only SecurityModule)│
│    SpatialMemory.blueprint(),    ◀── tag_location, etc.     │
│    SceneCaptionSkill,            ◀── describe_scene (ours)  │
│    ReactiveQASkills,             ◀── note_*/list_*/tour     │
│    DecisionAuditSkill,           ◀── log_nav_decision       │
│    LeadWithFollowSkill,          ◀── lead_to                │
│    McpServer,                    ◀── tools at :9990         │
│    McpClient(model="anthropic:claude-sonnet-4-6",           │
│              system_prompt=DROP_IN_GUIDE_SYSTEM_PROMPT),    │
│    _common_agentic,              ◀── Nav + PersonFollow +   │
│  )                                    UnitreeSkillContainer  │
└──────────────────────────────────────────────────────────────┘
```

The **system prompt** (in `blueprint.py`) is where the workflow lives. It defines three phases:
- **Phase 1** — Generative priming: `describe_scene` → `speak` proposal → confirm/correct/skip → `tag_location` + `note_tagged` OR `note_skipped`.
- **Phase 2** — Guided navigation: `log_nav_decision` → `speak` grounding → `lead_to` (visitor) or `navigate_with_text` (delivery).
- **Phase 3** — Reactive Q&A: `list_tagged_places`, `what_did_you_skip`, `narrate_tour`, or `express_uncertainty` → `speak`.

## Adding a new skill (recipe)

1. Create a new `Module` subclass in `drop_in_guide/`.
2. Decorate methods with `@skill` (from `dimos.agents.annotation`). Each `@skill` MUST have:
   - A complete docstring (becomes the LLM tool description).
   - Type annotations on every parameter.
   - A `str` return (returning `None` shows up to the LLM as a noisy "It has started. You will be updated later.").
3. Inject dependencies via `Spec` Protocols if you need to call other modules (e.g. `_navigation: NavigationInterfaceSpec`).
4. Add the module to `autoconnect(...)` in `blueprint.py`. Bump `n_workers` by 1.
5. Update `DROP_IN_GUIDE_NARRATION_POLICY` in `blueprint.py` to teach Claude when to call your skill.
6. Regenerate the dimOS blueprint registry:
   ```bash
   ./.venv/bin/python -m pytest dimos/robot/test_all_blueprints_generation.py
   ```
   (Test "fails" intentionally to remind you to commit — that's fine.)
7. Restart daemon: `./.venv/bin/dimos restart`. Confirm tool count in logs (expect +1).

## Skill design principles (learned the hard way)

- **Sync over async for short queries.** dimOS's stock `observe` returns an `Image` asynchronously via `tool_update`; Claude doesn't wait for the result and retries. Our `describe_scene` is synchronous (OpenAI Vision blocking call, ~3s on a Mac with native internet) and returns a description STRING. Claude can use the result directly.
- **Return strings the LLM can speak.** `list_tagged_places` returns *"I know 2 places: the printer (tagged a minute ago), and the kitchen..."* — not a JSON blob. Claude then chooses to `speak()` (or paraphrase) without parsing.
- **Track session state in the module.** `ReactiveQASkills` keeps `_tagged: list[dict]` and `_skipped: list[dict]` in memory. `DecisionAuditSkill` also appends to a JSONL file at `assets/output/drop_in_guide/nav_trace.jsonl`. SpatialMemory's vector store doesn't expose a "list everything" — we maintain a parallel log for human-readable summaries.
- **Skill names matter.** The LLM picks skills by docstring + name. We named ours so the right one fires from a natural utterance (e.g. *"what did you skip?"* → `what_did_you_skip()`).

## Non-obvious gotchas

- **First `tag_location` is slow** (~30–120s) because ChromaDB lazy-loads its embedding model. Subsequent calls <1s. We do *not* pre-warm; mention this in the demo narration if needed.
- **macOS needs `sudo route delete -interface en0 && sudo route add -interface lo0` for the 224.0.0.0/4 multicast range** before dimos can start — otherwise the LCM bus can't bind to loopback.
- **`--robot-ip` is a global flag, NOT a `run` flag.** Use `dimos --robot-ip 192.168.12.1 run drop-in-guide --daemon`.
- **`SpeakSkill` in `_common_agentic` plays through local `sounddevice`** (Mac speakers via UTM forwarding or directly). For Go2 onboard speaker, swap to `DropInGuideSpeakSkill` (untested at time of writing — see `drop_in_guide_speak.py`).
- **Pytest "fails" on the blueprint registry test** is expected behavior — it's the test telling you to commit the regenerated `all_blueprints.py`.

## Where to look next

- [`blueprint.py`](drop_in_guide/blueprint.py) — start here. The system prompt is the contract for everything else.
- [`STORYBOARD.md`](STORYBOARD.md) — 12-shot demo plan, with which skills fire in each shot.
- [`INSTALL.md`](INSTALL.md) — from-scratch setup on macOS or Ubuntu, including the SOCKS-proxy fallback for split-network venues.
- [dimOS upstream AGENTS.md](https://github.com/dimensionalOS/dimos/blob/main/AGENTS.md) — for the Module / Blueprint / `@skill` / RPC patterns this project builds on.

## Editing this file

Keep it under ~200 lines. If a section grows, factor it into a dedicated doc and link it. The point of `AGENTS.md` is to give a fresh agent (human or AI) enough to be productive within 5 minutes of opening the repo. Anything longer belongs in `INSTALL.md`, `STORYBOARD.md`, or a new `docs/` file.
