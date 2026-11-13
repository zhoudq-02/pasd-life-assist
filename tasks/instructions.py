"""Three instruction classes: simple 7 / implicit 4 / composed 13 (An et al. [4])."""
from __future__ import annotations

INSTRUCTIONS = {
    "A1": {
        "simple": ["把水杯递到嘴边"],
        "implicit": ["帮我喝点汤"],
        "composed": ["先舀一勺再递过来"],
    },
    "A2": {
        "simple": ["把水杯拿给我"],
        "implicit": ["我有点渴"],
        "composed": ["把药盒和温水一起放到我右手边"],
    },
}
# TODO(scaffold): expand to the full 7 / 4 / 13 instruction sets with fixed IDs.
