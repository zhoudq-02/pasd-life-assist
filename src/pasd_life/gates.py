"""Three-gate experience lifecycle. Contract: docs/00 section 3 / docs/01 section 5.

`promote` is the ONLY function allowed to mutate skill.state.
"""
from __future__ import annotations

from typing import Callable

from .config import (GATE2_REPEATS, GATE2_THRESHOLD, GATE3_CONSECUTIVE,
                     GATE3_REQUIRES_HUMAN_CONFIRM)
from .pasd_core import Extractor, OnlineClusterer, SkillLibrary
from .safety import SafetyEnvelope
from .schema import FailureSignature, Skill, Trace

NON_REPAIRABLE = frozenset({"IK_UNREACHABLE", "GRASP_IMPOSSIBLE", "INTENT_AMBIGUOUS"})

DEFAULT_REPAIRS: dict[str, dict] = {
    "GRASP_SLIP": {"fixes": "GRASP_SLIP", "approach": "side",
                   "text": "侧夹 + 手腕倾斜以抗滑落"},
    "POSE_LOW_CONFIDENCE": {"fixes": "POSE_LOW_CONFIDENCE", "text": "重感知 / 换视角 / 补深度"},
    "DETECTION_FAILED": {"fixes": "DETECTION_FAILED", "text": "重感知并补深度"},
    "OCCLUSION_RETRIEVE_FAIL": {"fixes": "OCCLUSION_RETRIEVE_FAIL", "text": "先移开遮挡物"},
    "PLACEMENT_OFFSET": {"fixes": "PLACEMENT_OFFSET", "text": "重定位再放"},
    "FOOD_SPILL": {"fixes": "FOOD_SPILL", "text": "降低倾角、分次少量、更换容器"},
    "MOUTH_APPROACH_UNSAFE": {"fixes": "MOUTH_APPROACH_UNSAFE",
                              "text": "降速 + 重规划接近方向 + 扩大安全区"},
    "SAFETY_VIOLATION": {"fixes": "SAFETY_VIOLATION", "text": "停机回退"},
}


def propose_repair(trace: Trace, generator=None) -> dict | None:
    """Single-arm non-repairable modes return None -- that is CORRECT behaviour."""
    if trace.error_code in NON_REPAIRABLE:
        return None
    if generator is not None:
        return generator.propose(trace)
    return DEFAULT_REPAIRS.get(trace.error_code)


def gate1_observe_failure(
    trace: Trace,
    extractor: Extractor,
    clusterer: OnlineClusterer,
    library: SkillLibrary,
    repair_fn: Callable[[Trace], dict | None] | None = None,
) -> Skill | None:
    signature: FailureSignature = extractor.extract(trace)
    if signature.is_empty:
        return None  # REJECTED: empty signature would be a "universal skill"
    cluster_id = clusterer.assign(signature, trace.scene)
    identity = (signature.stage, signature.error_code, cluster_id)
    existing = library.get(identity)
    if existing is not None:
        existing.hits += 1
        return None  # Gate1: cluster-identity deduplication
    repair = (repair_fn or propose_repair)(trace)
    if repair is None:
        return None
    skill = Skill(
        sigma=signature,
        applicable={"task": trace.task, "split": trace.split},
        repair=repair,
        verification={},
        identity=identity,
        state="CANDIDATE",
        tag=trace.task,
    )
    library.ingest(skill)
    return skill


def gate2_verify(skill: Skill, sim_runner, repeats: int = GATE2_REPEATS,
                 threshold: float = GATE2_THRESHOLD) -> bool:
    """Simulation must repeat the repair and reach a quantitative success rate."""
    if skill.repair.get("fixes") != skill.sigma.error_code:
        skill.verification["gate2_reject"] = "fixes_mismatch"
        return False
    passed = sum(1 for _ in range(repeats) if sim_runner.run(skill))
    rate = passed / repeats if repeats else 0.0
    skill.verification["gate2_rate"] = rate
    skill.verification["gate2_repeats"] = repeats
    return rate >= threshold


def gate3_verify(skill: Skill, real_log: dict, consecutive: int = GATE3_CONSECUTIVE,
                 human_confirmed: bool = GATE3_REQUIRES_HUMAN_CONFIRM,
                 envelope: SafetyEnvelope | None = None,
                 features: dict | None = None) -> bool:
    if skill.state != "VERIFIED":
        return False
    if envelope is not None and features is not None:
        violated, reason = envelope.violated(features)
        if violated:
            skill.verification["gate3_reject"] = reason
            return False
    return bool(human_confirmed) and int(real_log.get("consecutive_success", 0)) >= consecutive


def promote(
    skill: Skill,
    sim_runner,
    real_log: dict | None = None,
    features: dict | None = None,
    envelope: SafetyEnvelope | None = None,
    human_confirmed: bool = GATE3_REQUIRES_HUMAN_CONFIRM,
) -> Skill:
    """CANDIDATE -> VERIFIED -> SAFE (or REJECTED). Safety veto precedes Gate2.

    real_log=None means offline simulation only: the skill stops at VERIFIED and
    Gate3 is run later in the real-robot deployment flow.
    """
    if skill.state != "CANDIDATE":
        return skill
    if envelope is not None and features is not None:
        violated, reason = envelope.violated(features)
        if violated:
            skill.state = "REJECTED"
            skill.verification["veto"] = f"safety_envelope:{reason}"
            return skill
    if not gate2_verify(skill, sim_runner):
        skill.state = "REJECTED"
        skill.verification["veto"] = "gate2"
        return skill
    skill.state = "VERIFIED"
    if real_log is not None and gate3_verify(skill, real_log, human_confirmed=human_confirmed,
                                             envelope=envelope, features=features):
        skill.state = "SAFE"
    return skill
