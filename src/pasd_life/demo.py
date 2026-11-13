"""End-to-end smoke loop: failure -> Gate1 -> Gate2 -> retrieve -> repaired success.

Reproduces the PASD reference case (slender rod, aspect_ratio=5.3, top grasp).
"""
from __future__ import annotations

from .executor import MockSimRunner
from .gates import gate3_verify, promote
from .pasd_core import Extractor, OnlineClusterer, SkillLibrary
from .policy_gen import StubPolicyGenerator
from .robot_api import MockPiPER, RobotAPI
from .safety import SafetyEnvelope
from .schema import SceneContext
from integration.runner import run_episode
from integration.baselines.registry import build


class MockEnv:
    def __init__(self, scene: dict | None = None, split: str = "dev") -> None:
        self.base_scene = dict(scene or {"aspect_ratio": 5.3, "target_width": 0.022,
                                        "approach": "top", "ground_truth_mass": 0.12})
        self.split = split
        self.api = RobotAPI(MockPiPER(self.base_scene))
        self.state: dict = {}

    def reset(self, task: str, seed: int) -> SceneContext:
        self.api = RobotAPI(MockPiPER(self.base_scene))
        self.state = {}
        return SceneContext(instruction=task, scene_summary="slender rod on table",
                            split=self.split, features=dict(self.base_scene))


def run_demo(verbose: bool = True) -> dict:
    scene = {"aspect_ratio": 5.3, "target_width": 0.022, "approach": "top",
             "ground_truth_mass": 0.12}
    sim = MockSimRunner(scene)
    memory = build("pasd_full", extractor=Extractor(), clusterer=OnlineClusterer(),
                   library=SkillLibrary(), sim_runner=sim, envelope=SafetyEnvelope())
    policy = StubPolicyGenerator()
    env = MockEnv(scene)
    results = []
    for seed in (0, 1):
        ok, trace = run_episode(policy, memory, env, "T1", seed)
        results.append((ok, trace.error_code or "OK"))
        if verbose:
            print(f"episode seed={seed}: success={ok} error={trace.error_code or '-'} "
                  f"library={memory.library.size} verified={memory.library.verified_count}")

    # Gate3 demonstration: 8 consecutive real successes + first human confirmation -> SAFE
    skills = memory.library.all()
    for skill in skills:
        if skill.state == "VERIFIED":
            ok = gate3_verify(skill, {"consecutive_success": 8}, human_confirmed=True,
                              envelope=SafetyEnvelope(), features={"min_human_dist": 0.4})
            if ok:
                skill.state = "SAFE"
            if verbose:
                print(f"gate3: {skill.sigma.error_code} -> {skill.state}")
            # Safety veto must override a Gate2-passing repair
            vetoed = promote(
                _fresh_candidate(skill), sim_runner=sim,
                features={"min_human_dist": 0.05}, envelope=SafetyEnvelope(),
            )
            if verbose:
                print(f"safety veto: {vetoed.state} ({vetoed.verification.get('veto')})")
    return {"episodes": results, "final_library_size": memory.library.size,
            "states": [s.state for s in skills]}


def _fresh_candidate(template: "Skill"):
    from dataclasses import replace
    return replace(template, state="CANDIDATE", verification={})


if __name__ == "__main__":
    run_demo()
