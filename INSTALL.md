# Install — Drop-in Guide

Tested on **macOS 26 (Tahoe), Apple M4 Pro**. Also works on Ubuntu 22.04/24.04.

## 1. Prerequisites

```bash
# Homebrew + dependencies (macOS)
brew install gnu-sed gcc portaudio git-lfs libjpeg-turbo python@3.12 pre-commit

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

## 2. Clone dimOS (PR 2245 macOS branch)

```bash
cd ~/Downloads/robotics
GIT_LFS_SKIP_SMUDGE=1 git clone \
  -b danvi/experimental/route-replay-through-SHM \
  https://github.com/dimensionalOS/dimos.git
cd dimos

uv venv --python 3.12
uv sync --extra unitree --extra agents --extra web --extra perception --extra cpu --no-default-groups
uv pip install langchain-anthropic python-multipart pytest-xdist pytest-cov pytest-timeout
```

## 3. Drop in our files

Clone this repo (Drop-in Guide) alongside dimos:

```bash
cd ~/Downloads/robotics
git clone https://github.com/arome3/drop-in-guide.git
```

Copy the 4 skill files into dimOS's `dimos/experimental/`:

```bash
cp drop-in-guide/drop_in_guide/{scene_caption_skill,reactive_qa_skills,decision_audit_skill,drop_in_guide_speak}.py \
   dimos/dimos/experimental/
```

Copy the blueprint into dimOS's blueprint tree:

```bash
cp drop-in-guide/drop_in_guide/blueprint.py \
   dimos/dimos/robot/unitree/go2/blueprints/agentic/drop_in_guide.py
```

Regenerate dimOS's blueprint registry (the test "fails" deliberately to remind you to commit — that's expected):

```bash
cd dimos
./.venv/bin/python -m pytest dimos/robot/test_all_blueprints_generation.py
```

## 4. Configure API keys

```bash
cat > .env <<EOF
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
EOF
```

## 5. macOS-specific: LCM multicast routing

dimOS uses LCM with multicast. macOS by default claims `224.0.0.0/4` on your active WiFi interface (`en0`). dimOS needs it on `lo0`:

```bash
sudo route delete -net 224.0.0.0/4 -interface en0
sudo route add -net 224.0.0.0/4 -interface lo0
```

(One-time. To persist across reboots, install via a launchd plist.)

## 6. Run in replay mode (no robot)

```bash
cd dimos
set -a; source .env; set +a
./.venv/bin/dimos --replay --viewer none run drop-in-guide --daemon
```

Confirm:

```bash
./.venv/bin/dimos status
./.venv/bin/dimos log -n 50 | grep "Discovered tools"  # should show 25 tools
```

Test the priming dialogue:

```bash
./.venv/bin/dimos agent-send "Let's learn this place. What do you see?"
```

Watch logs:

```bash
./.venv/bin/dimos log -f
```

## 7. Run on real Unitree Go2

Same launch with `--robot-ip`:

```bash
./.venv/bin/dimos --robot-ip 192.168.12.1 --viewer none run drop-in-guide --daemon
```

Replace `192.168.12.1` with your Go2's actual IP.

## Known gotchas

- **First launch is slow** — ChromaDB lazy-loads its embedding model (~30–120s on first `tag_location` call on weak CPUs). Subsequent calls are <1s.
- **TTS plays through local `sounddevice`** (your Mac speakers, not the Go2's onboard speaker). To route audio to the Go2 speaker, use `drop_in_guide_speak.py` (untested at time of writing) which uploads audio via WebRTC `AUDIO_HUB_REQ`.
- **Pytest "fails" on `test_all_blueprints_is_current`** when you add new blueprints — that's intentional, it just means the registry was regenerated.
- **`sudo route` permissions** — macOS may prompt for password or Touch ID. Accept once.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Form data requires "python-multipart"` | Missing pip package | `uv pip install python-multipart` |
| `sudo route add ... returned non-zero status 1` | Existing route on en0 conflicts | Run the `route delete -interface en0` step from §5 |
| `tag_location` times out 120s | ChromaDB cold-load (slow CPU) | Wait, or pre-warm by calling once at startup |
| `No salient object visible` from `describe_scene` | Camera frame is blurred/blank | Move the robot to face something; describe_scene re-runs |
