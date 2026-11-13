"""Six ablation switches for main table B (docs/03 section 2).

Each ablation clones PASDFullMemory and disables exactly one component:
- no_gate1: cluster-identity dedup removed (|B_t| grows linearly)
- no_gate2: Gate2 simulation verification removed (always passes)
- no_gate3: Gate3 real-robot + safety gate removed (promotes straight to SAFE)
- no_task_level_signature: interaction/safety stages collapse back to the 4 originals
- no_directional_rounding: threshold extraction without q_dir (strategy=observed)
- no_eval_driven_randomisation: the offline q_t(c)->p_t(theta) loop is external to the
  MemoryPlugin (applied at the experiment/domain_rand level, not here)
"""
from __future__ import annotations

from src.pasd_life.gates import gate1_observe_failure, promote, propose_repair
from src.pasd_life.pasd_core import Extractor
from src.pasd_life.schema import FailureSignature, Skill, Trace
from .pasd_full import PASDFullMemory

ABLATIONS = (
    "no_gate1", "no_gate2", "no_gate3", "no_task_level_signature",
    "no_directional_rounding", "no_eval_driven_randomisation",
)


class _ObservedExtractor(Extractor):
    """no_directional_rounding: keep the raw threshold (no q_dir directional rounding)."""

    def extract(self, trace, strategy="observed"):
        return super().extract(trace, strategy="observed")


class _FourStageExtractor(Extractor):
    """no_task_level_signature: collapse interaction/safety back to the 4 original stages."""

    def extract(self, trace, strategy="margin"):
        sig = super().extract(trace, strategy)
        if sig.stage in ("interaction", "safety"):
            stage = "execution" if sig.stage == "safety" else "perception"
            sig = FailureSignature(stage, sig.error_code, sig.conditions, sig.description)
        return sig


class _AlwaysPassSimRunner:
    def run(self, skill) -> bool:
        return True


class AblationMemory(PASDFullMemory):
    name = "ablation"
    requires_training = False
    table = "B"

    def __init__(self, ablation: str, **kwargs) -> None:
        if ablation not in ABLATIONS:
            raise KeyError(ablation)
        if ablation == "no_directional_rounding":
            kwargs["extractor"] = _ObservedExtractor()
        elif ablation == "no_task_level_signature":
            kwargs["extractor"] = _FourStageExtractor()
        super().__init__(**kwargs)
        self.ablation = ablation
        self._counter = 0

    def on_episode_end(self, trace: Trace) -> None:
        if not trace.error_code:
            return
        self.fm_calls += 1
        if self.ablation == "no_gate1":
            self._episode_no_gate1(trace)
        elif self.ablation == "no_gate2":
            self._episode_no_gate2(trace)
        elif self.ablation == "no_gate3":
            self._episode_no_gate3(trace)
        else:
            # component-level ablations (extractor overrides already applied in __init__)
            super().on_episode_end(trace)

    def _episode_no_gate1(self, trace: Trace) -> None:
        sig = self.extractor.extract(trace)
        if sig.is_empty:
            return
        repair = propose_repair(trace)
        if repair is None:
            return
        self._counter += 1
        skill = Skill(sigma=sig, applicable={"task": trace.task, "split": trace.split},
                      repair=repair, verification={"gate2_rate": 1.0},
                      identity=(sig.stage, sig.error_code, self._counter),
                      state="VERIFIED", tag=trace.task)
        self.library.ingest(skill)

    def _episode_no_gate2(self, trace: Trace) -> None:
        candidate = gate1_observe_failure(trace, self.extractor, self.clusterer, self.library)
        if candidate is None:
            return
        promote(candidate, sim_runner=_AlwaysPassSimRunner(), features=trace.features,
                envelope=self.envelope, human_confirmed=self.human_confirmed)

    def _episode_no_gate3(self, trace: Trace) -> None:
        candidate = gate1_observe_failure(trace, self.extractor, self.clusterer, self.library)
        if candidate is None:
            return
        promote(candidate, sim_runner=self.sim_runner, features=trace.features,
                envelope=self.envelope, real_log={"consecutive_success": 8},
                human_confirmed=True)


def build_ablation(name: str, **kwargs):
    if name not in ABLATIONS:
        raise KeyError(name)
    return AblationMemory(name, **kwargs)
