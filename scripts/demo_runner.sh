#!/usr/bin/env bash
# Drop-in Guide — interactive demo runner.
# Walks through the 12-shot storyboard one beat at a time, pausing for
# you (the operator) between each beat so you can:
#   - watch the robot respond
#   - adjust the next utterance to match what the robot actually said
#   - screen-record cleanly
#
# Usage:
#   1. In one terminal:     ./.venv/bin/dimos log -f     # tail the log
#   2. In another terminal: ./.venv/bin/dimos-viewer ... # rerun viewer for audit panel
#   3. Start screen recording (macOS: Cmd+Shift+5)
#   4. Run this script:     bash scripts/demo_runner.sh
#   5. Hit ENTER to advance through each shot. Hit Ctrl+C to abort.

set -euo pipefail

DIMOS_BIN="${DIMOS_BIN:-${HOME}/Downloads/robotics/dimos/.venv/bin/dimos}"

# --- helpers ------------------------------------------------------------
say() {
  echo
  echo "=========================================================="
  echo "  $1"
  echo "=========================================================="
}

wait_user() {
  echo
  echo "  Next: $1"
  echo -n "  Press ENTER to send, or Ctrl+C to abort. > "
  read -r _
}

send() {
  local msg="$1"
  echo "  → agent-send: $msg"
  "$DIMOS_BIN" agent-send "$msg" >/dev/null
}

call() {
  # Direct MCP call (bypasses the agent), for skills like note_tagged
  # that we want to invoke without burning Claude tokens during a test.
  local skill="$1"; shift
  local args=("$@")
  echo "  → mcp call: $skill ${args[*]}"
  "$DIMOS_BIN" mcp call "$skill" "${args[@]}" >/dev/null
}

# --- preflight ----------------------------------------------------------
say "Drop-in Guide — Demo Runner"
echo
if ! "$DIMOS_BIN" status >/dev/null 2>&1; then
  echo "  ❌ No DimOS instance running. Start one with:"
  echo "       $DIMOS_BIN --replay --viewer none run drop-in-guide --daemon"
  echo "     or with --robot-ip 192.168.12.1 for real hardware."
  exit 1
fi
echo "  Daemon detected. Begin recording, then continue."
wait_user "begin the demo"

# --- SHOT 1-2: COLD OPEN + ROBOT ACCEPTS MISSION ------------------------
say "SHOT 1-2: Operator says 'Let's learn this place.'"
wait_user 'send the opening prompt'
send "Let's learn this place. Look around and tell me what you see, then I will help you label it."

# --- SHOT 3: PROPOSAL ---------------------------------------------------
say "SHOT 3: Robot describes scene + proposes a tag"
echo "  Watch the log for the proposal. When the robot has spoken, advance."
wait_user 'confirm the first tag with the right name'
echo
echo "  Hint: type the name the robot actually proposed. Examples:"
echo "    - 'Yes, call it the trash bin.'"
echo "    - 'Yes, but call it the recycle bin.'"
echo "    - 'Skip it.'"
echo
echo -n "  Your response > "
read -r RESPONSE_1
send "$RESPONSE_1"

# --- SHOT 4: CORRECTION -------------------------------------------------
say "SHOT 4: Operator corrects/skips a second proposal"
wait_user 'move the robot or ask it to look again, then respond'
send "Now look around for another notable object and propose a tag."
echo
echo "  Wait for robot to describe + propose, then..."
echo -n "  Your response (correction or skip) > "
read -r RESPONSE_2
send "$RESPONSE_2"

# --- SHOT 5: SKIP -------------------------------------------------------
say "SHOT 5: Operator skips a third proposal"
wait_user 'ask for a third look'
send "What else do you see? Propose one more tag."
echo
echo "  Wait for proposal, then say 'skip' to demonstrate the note_skipped path."
echo -n "  Your response (recommend: 'Skip this one.') > "
read -r RESPONSE_3
send "$RESPONSE_3"

# --- SHOT 6: PRIMING ENDS ----------------------------------------------
say "SHOT 6: End priming + list what's known"
wait_user "wrap priming"
send "That's enough priming. What did you learn?"

# --- SHOT 7: GUIDANCE WITH AUDIT ----------------------------------------
say "SHOT 7: Visitor asks for a destination — robot speaks grounding"
wait_user 'send a navigation request'
echo
echo "  Hint: phrase it like a visitor's request. Examples:"
echo "    - 'Take me to the trash bin.'"
echo "    - 'Where's the recycle bin?'"
echo
echo -n "  Your request > "
read -r DEST
send "$DEST"
echo
echo "  WATCH for the log_nav_decision call + the speak with grounding."
echo "  The Rerun viewer should show the audit panel at /audit/nav_decisions."

# --- SHOT 8: LEAD-WITH-FOLLOW PAUSE (REPLAY DEMO ONLY) ------------------
say "SHOT 8: Lead-with-follow — pause + 'I'll wait for you'"
echo "  In replay this is hard to demonstrate authentically because there's"
echo "  no visitor camera signal to lose. On real hardware this shot fires"
echo "  when the visitor falls behind. For now we'll skip the live beat."
wait_user 'skip to Shot 9'

# --- SHOT 9: ARRIVAL ---------------------------------------------------
say "SHOT 9: Robot arrives + asks what's next"
wait_user 'simulate arrival'
send "Pretend you've arrived. Speak the arrival line."

# --- SHOT 10: Q&A CALLBACK ---------------------------------------------
say "SHOT 10: Visitor asks about what was skipped"
wait_user 'send the Q&A callback question'
send "Earlier you skipped something. What was it?"

# --- (BONUS) TOUR MODE --------------------------------------------------
say "BONUS: Narrate a quick tour"
wait_user "ask for a tour"
send "Give me a quick tour of what you know."

# --- SHOT 11-12: CLOSE -------------------------------------------------
say "SHOT 11-12: Close"
wait_user 'send the close'
send "Thanks. That's it for now."

echo
echo "=========================================================="
echo "  Demo complete. Stop recording."
echo "  Inspect the audit trail at:"
echo "    assets/output/drop_in_guide/nav_trace.jsonl"
echo "=========================================================="
