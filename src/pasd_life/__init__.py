"""PASD-Life-Assist core. See CLAUDE.md and docs/ for the authoritative contract."""
from .schema import (Condition, FailureSignature, Skill, Trace, SceneContext,
                     StepFeedback, RepairHint, Observation, PiPERError)
from .robot_api import RobotAPI, MockPiPER, WhitelistViolation, ALLOWED
from .pasd_core import Extractor, OnlineClusterer, SkillLibrary, Retriever
from .gates import (gate1_observe_failure, gate2_verify, gate3_verify,
                    promote, propose_repair)
from .safety import SafetyEnvelope, EmergencyStop

__all__ = [
    "Condition", "FailureSignature", "Skill", "Trace", "SceneContext",
    "StepFeedback", "RepairHint", "Observation", "PiPERError",
    "RobotAPI", "MockPiPER", "WhitelistViolation", "ALLOWED",
    "Extractor", "OnlineClusterer", "SkillLibrary", "Retriever",
    "gate1_observe_failure", "gate2_verify", "gate3_verify", "promote",
    "propose_repair", "SafetyEnvelope", "EmergencyStop",
]
