"""code-as-policy generator (PLUGIN POINT). Contract: docs/00 section 2."""
from __future__ import annotations

import json
import os

from .config import LLM_MAX_TOKENS, LLM_MODEL_DEFAULT, LLM_TEMPERATURE
from .schema import Observation, SceneContext, RepairHint


_SYSTEM_PROMPT = """\
You generate Python code to control a 6-DoF assistive robot arm (AgileX PiPER).

Allowed actions only (SI units; gripper width in metres, range 0 to 0.070):
- robot.move_to_pose(pose, speed=...)   # pose is a dict with "approach" and "target" [x, y, z]
- robot.open_gripper()
- robot.close_gripper(width=...)        # width in metres
- robot.get_observation()               # returns a dict of observables
- robot.solve_ik(target_pose)           # returns a dict or None

Rules:
- Output ONLY one Python function `def run(robot):` and nothing else.
- No imports, no globals, no helper functions, no print.
- Call only the five robot.* methods listed above.
- Return a dict: {"steps": <int>, "state": {<observation fields>}}.
"""


def _extract_text(content) -> str:
    """Collect only text blocks; skip thinking/reasoning blocks."""
    parts = []
    for block in content or []:
        if getattr(block, "type", "text") == "text":
            text = getattr(block, "text", "") or ""
            parts.append(text if isinstance(text, str) else " ".join(str(x) for x in text))
    return "\n".join(parts)


def _strip_fence(text: str) -> str:
    """Strip a leading ```lang and trailing ``` if present."""
    lines = text.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _resolve_model() -> str:
    from .settings import _load_dotenv, repo_root  # local import: no heavy deps

    _load_dotenv(repo_root() / ".env")
    model = (os.environ.get("PASD_LLM_MODEL") or "").strip()
    if model:
        return model
    return (os.environ.get("ANTHROPIC_MODEL") or "").strip() or LLM_MODEL_DEFAULT


class StubPolicyGenerator:
    """Offline stand-in: chooses approach from injected RepairHints. Never calls an LLM."""

    name = "stub"

    def generate(self, task: str, ctx: SceneContext, hints: list[RepairHint]):
        approach = "top"
        for hint in hints:
            if "侧夹" in hint.text or (hint.executable or {}).get("approach") == "side":
                approach = "side"

        def run(robot) -> Observation:
            robot.move_to_pose({"approach": approach, "target": [0.3, 0.0, 0.15]})
            robot.open_gripper()
            robot.close_gripper(width=0.022)
            obs = robot.get_observation()
            return Observation(state={**obs, "success": True, "elapsed": 1.2,
                                      "subgoal_ratio": 1.0}, steps=3)

        return run


class ClaudeCodePolicyGenerator:
    """Generate run(robot) source and repair plans via the LLM.

    Keeps temperature / max_tokens fixed across baselines (fairness #2, #6).
    Generated source must pass Executor._compile. On this host the anthropic SDK is
    pointed at DeepSeek via ANTHROPIC_BASE_URL (see docs/08 / design spec).
    """

    name = "claude_code"

    def __init__(self, client=None, model=None, max_tokens=None, temperature=None) -> None:
        self._client = client
        self.model = model or _resolve_model()
        self.max_tokens = max_tokens if max_tokens is not None else LLM_MAX_TOKENS
        self.temperature = temperature if temperature is not None else LLM_TEMPERATURE

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError("anthropic not installed; run: pip install -e '.[agent]'") from e
        self._client = anthropic.Anthropic()
        return self._client

    def _build_user_message(self, task: str, ctx: SceneContext, hints: list[RepairHint]) -> str:
        parts = [
            f"task: {task}",
            f"instruction: {ctx.instruction}",
            f"scene_summary: {ctx.scene_summary}",
            f"features: {ctx.features}",
        ]
        if hints:
            parts.append("repair hints: " + "; ".join(h.text for h in hints))
        return "\n".join(parts)

    def generate(self, task: str, ctx: SceneContext, hints: list[RepairHint]) -> str:
        resp = self._get_client().messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": self._build_user_message(task, ctx, hints)}],
        )
        text = _extract_text(resp.content)
        src = _strip_fence(text)
        if not src.strip():
            raise RuntimeError(
                "model returned no usable code (empty or only thinking/fence); "
                "raise max_tokens or retry"
            )
        return src

    def propose(self, trace) -> dict | None:
        resp = self._get_client().messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system="You output a single JSON object and nothing else.",
            messages=[{
                "role": "user",
                "content": (
                    "Generate a repair plan for this failure.\n"
                    f"error_code: {trace.error_code}\n"
                    f"message: {trace.message}\n"
                    f"features: {trace.features}\n"
                    'Return ONLY a JSON object containing "fixes" equal to the error_code '
                    "plus any repair fields (e.g. approach, text)."
                ),
            }],
        )
        text = _extract_text(resp.content)
        if not text.strip():
            return None
        try:
            data = json.loads(_strip_fence(text))
        except (ValueError, TypeError):
            return None
        if not isinstance(data, dict) or data.get("fixes") != trace.error_code:
            return None
        return data
