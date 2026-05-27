#!/usr/bin/env python3
# Drop-in Guide reactive Q&A skills.
# Tracks the priming session (tagged + skipped objects) so visitors can ask
# the robot about its memory after priming completes. Pairs with the
# `tag_location` skill that already writes to dimOS spatial memory — these
# skills just maintain a parallel session log so we can answer summary
# questions like "what did you skip?" and "where can you take me?".

import time
from typing import Any

from dimos.agents.annotation import skill
from dimos.core.core import rpc
from dimos.core.module import Module
from dimos.utils.logging_config import setup_logger

logger = setup_logger()


class ReactiveQASkills(Module):
    """Session log + Q&A helpers for the priming workflow."""

    _tagged: list[dict[str, Any]] = []
    _skipped: list[dict[str, Any]] = []

    @rpc
    def start(self) -> None:
        super().start()
        self._tagged = []
        self._skipped = []

    @rpc
    def stop(self) -> None:
        super().stop()

    @skill
    def note_tagged(self, name: str) -> str:
        """Record that a location was tagged during priming. Call this RIGHT
        AFTER `tag_location` so we can later answer "where can you take me?"
        and "what places do you know?".

        Args:
            name: the name used in the corresponding tag_location call
                  (e.g. "printer", "the kitchen").
        """
        self._tagged.append({"name": name.strip(), "ts": time.time()})
        return f"Noted tagged location: {name}"

    @skill
    def note_skipped(self, description: str) -> str:
        """Record that the operator chose to skip a proposed object during
        priming. Call this when the operator says "skip" / "no important" /
        "next one" instead of confirming a tag. Used later to answer
        "what did you skip?".

        Args:
            description: short description of what was visible but not tagged
                         (e.g. "a green plant on a stand to my right").
        """
        self._skipped.append({"description": description.strip(), "ts": time.time()})
        return f"Noted skip: {description}"

    @skill
    def list_tagged_places(self) -> str:
        """List every place I've tagged so far in this session. Use this when
        someone asks "where can you take me?", "what places do you know?",
        "what did you tag?", or similar overview questions.
        """
        if not self._tagged:
            return "I haven't tagged any places yet in this session."
        names = [t["name"] for t in self._tagged]
        if len(names) == 1:
            return f"I know one place: {names[0]}. You can ask me to take you there."
        return (
            f"I know {len(names)} places: {', '.join(names)}. "
            f"You can ask me to take you to any of them."
        )

    @skill
    def what_did_you_skip(self) -> str:
        """Report the objects the operator chose to skip during priming. Use
        this when someone asks "what did you skip?", "what didn't you tag?",
        or "anything you saw but ignored?".
        """
        if not self._skipped:
            return "I didn't skip anything during this priming session."
        descs = [s["description"] for s in self._skipped]
        if len(descs) == 1:
            return f"I skipped one object during priming: {descs[0]}."
        return f"I skipped {len(descs)} objects during priming: " + "; ".join(descs) + "."
