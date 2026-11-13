"""Policy execution with AST whitelist validation. Contract: docs/01 section 3/8."""
from __future__ import annotations

import ast
from typing import Callable, Protocol

from .robot_api import ALLOWED, MockPiPER, RobotAPI, WhitelistViolation
from .schema import Observation, PiPERError, StepFeedback
from .config import MAX_STEPS

Policy = Callable[[RobotAPI], Observation]


class Executor:
    def __init__(self, api: RobotAPI) -> None:
        self.api = api

    def _compile(self, source: str) -> Policy:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
                raise WhitelistViolation("imports and globals are forbidden in policies")
            if isinstance(node, ast.Call):
                fn = node.func
                ok = (
                    isinstance(fn, ast.Attribute)
                    and isinstance(fn.value, ast.Name)
                    and fn.value.id == "robot"
                    and fn.attr in ALLOWED
                )
                if not ok:
                    raise WhitelistViolation("only robot.<whitelisted primitive>() is allowed")
        namespace: dict = {"robot": self.api, "__builtins__": {}}
        exec(compile(tree, "<policy>", "exec"), namespace)
        return namespace["run"]

    def run(self, policy: Policy | str, step_cb: Callable[[StepFeedback], None] | None = None,
            max_steps: int = MAX_STEPS) -> Observation:
        fn = self._compile(policy) if isinstance(policy, str) else policy
        obs_before = self.api.get_observation()
        obs = fn(self.api)
        if isinstance(obs, dict):
            state = obs.get("state")
            steps = obs.get("steps")
            obs = Observation(state=state if isinstance(state, dict) else {},
                              steps=steps if isinstance(steps, int) else 0,
                              success=obs.get("success", True))
        if obs.steps > max_steps:
            raise PiPERError("STEP_LIMIT_EXCEEDED", {}, "exceeded 30-step budget")
        if step_cb is not None:
            step_cb(StepFeedback(obs_before, {"policy": getattr(fn, "__name__", "generated")},
                                 dict(obs.state), 0))
        return obs


class MockSimRunner:
    """Gate2 simulation backend for the offline scaffold.

    TODO(scaffold): replace rollout with MuJoCo parallel environments; calibrate
    finger friction and grip force on the real arm first (docs/07 section 5).
    """

    def __init__(self, base_scene: dict) -> None:
        self.base_scene = dict(base_scene)

    def run(self, skill) -> bool:
        approach = str(skill.repair.get("approach", "top"))
        scene = {**self.base_scene, "approach": approach}
        api = RobotAPI(MockPiPER(scene))
        try:
            api.move_to_pose({"approach": approach, "target": [0.3, 0.0, 0.15]})
            api.open_gripper()
            api.close_gripper(width=0.022)
            return True
        except PiPERError:
            return False
