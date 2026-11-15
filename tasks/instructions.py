"""Three instruction classes: simple 7 / implicit 4 / composed 13 (An et al. [4], docs/02 §2).

NOTE: these are PLACEHOLDER instructions generated to the 7/4/13 protocol counts; the exact
wording must be verified against the An et al. [4] original before the paper. Each instruction
carries a stable ID for reproducibility (fairness #10). Implicit instructions require intent
resolution: intent_confidence < 0.6 -> INTENT_AMBIGUOUS -> clarify (never auto-promote).
"""
from __future__ import annotations

SIMPLE, IMPLICIT, COMPOSED = 7, 4, 13

INSTRUCTIONS = {
    "A1": {
        "simple": {
            "A1_s1": "把水杯递到嘴边",
            "A1_s2": "把勺子递到我手边",
            "A1_s3": "把碗端到我面前",
            "A1_s4": "把药片放到我手心",
            "A1_s5": "把吸管插进水杯",
            "A1_s6": "把餐盘推到我面前",
            "A1_s7": "把杯子里的水倒掉",
        },
        "implicit": {
            "A1_i1": "帮我喝点汤",
            "A1_i2": "我有点渴了",
            "A1_i3": "我饿了，想吃点东西",
            "A1_i4": "该吃药了",
        },
        "composed": {
            "A1_c1": "先舀一勺再递过来",
            "A1_c2": "先倒半杯水，再递到我嘴边",
            "A1_c3": "把碗里的粥搅一搅，再舀一勺喂我",
            "A1_c4": "先帮我擦擦嘴，再把杯子递过来",
            "A1_c5": "把桌上的药和一杯温水一起拿给我",
            "A1_c6": "先盛一碗汤，放凉一点再递给我",
            "A1_c7": "把水果切成小块，再用叉子喂我",
            "A1_c8": "把面包掰成小块，蘸点牛奶再给我",
            "A1_c9": "先给我倒杯水，再帮我把药拿过来",
            "A1_c10": "把餐盒打开，把饭菜分好递给我",
            "A1_c11": "先递纸巾，再递水杯",
            "A1_c12": "把吸管插好，再把杯子放到我嘴边",
            "A1_c13": "把药和温水一起放到我右手边",
        },
    },
    "A2": {
        "simple": {
            "A2_s1": "把水杯拿给我",
            "A2_s2": "把桌上的手机递给我",
            "A2_s3": "把遥控器拿给我",
            "A2_s4": "把钥匙递给我",
            "A2_s5": "把书递给我",
            "A2_s6": "把眼镜拿给我",
            "A2_s7": "把笔递给我",
        },
        "implicit": {
            "A2_i1": "我有点渴",
            "A2_i2": "我看不太清",
            "A2_i3": "该给家人回个电话了",
            "A2_i4": "我想看会儿书",
        },
        "composed": {
            "A2_c1": "把药盒和温水一起放到我右手边",
            "A2_c2": "把手机和充电器一起拿给我",
            "A2_c3": "先把桌上的杂物移开，再把水杯拿给我",
            "A2_c4": "把书和眼镜一起放到我左手边",
            "A2_c5": "把掉在地上的笔捡起来，放到桌上",
            "A2_c6": "把抽屉里的药盒拿出来递给我",
            "A2_c7": "先把书合上，再把眼镜递过来",
            "A2_c8": "把纸巾盒和水杯一起拿过来",
            "A2_c9": "把充电线插上，再把手机递给我",
            "A2_c10": "先找遥控器，再把它放到我手边",
            "A2_c11": "把杯子和药一起端过来",
            "A2_c12": "把桌上的药和手机一起放到托盘里",
            "A2_c13": "把钥匙放到盒子里，再把水杯递给我",
        },
    },
}
