# Paper outline (SCI submission)

Title (CN): 失败签名簇驱动的有界经验蒸馏：面向桌面助餐与取物的人机共域具身智能体
Title (EN): Bounded, Verified, and Safe Experience Distillation for Human-in-the-Loop Assistive Embodied Agents

1. Introduction — problem: experience reuse in human-shared space; contribution paragraph (see claims.md)
2. Related Work — 5 regrouped clusters per docs/05 (NOT the PASD list), patents & FTO
3. Method
   3.1 Failure-signature clusters as the sole experience unit (C1), upper bound |B_t| <= k
   3.2 Three-gate lifecycle + safety envelope as promotion criterion (C2)
   3.3 Unified evaluation protocol S3R / Delta + offline simulator-parameter loop (C3)
4. System Implementation — Claude Code code-as-policy, PiPER, MuJoCo, interface protocol (docs/01)
5. Experiments — E1..E7, tables A/B/C1/C2/D, fairness 16 items, statistics
6. Results — C1 convergence curve, C2 safety ablation, C3 SRCC/Delta
7. Discussion & Limitations — see docs/07 section 5
8. Conclusion

Writing rules: main claims ONLY from table A/B; C1/C2 trends only; always cite and
delimit TGL (arXiv:2608.17209) and SSS (arXiv:2609.38178); report SSS 0.70-0.77.
