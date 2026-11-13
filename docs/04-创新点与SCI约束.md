# 04　SCI 创新点与写作约束

## 1　主论点（Abstract 末句 / Introduction 贡献段首句）

> 现有经验驱动方法优化的是**经验能否被记住并复用**；而在人机共域的生活辅助中，决定能否部署的是**经验能否以有界规模、可验证的可信度、且不牺牲人身安全地被复用**。本文提出以失败签名簇为唯一经验单元的「精炼—验证—安全」三闸门经验生命周期，把三个约束编码进同一个经验单元与同一套评测口径，并在 PiPER 真机的桌面助餐与取物双任务上给出同时报告精炼性、可信性、安全性三类指标的首个实证。

## 2　三条贡献与代码锚点

| | 贡献 | 现有工作为何做不到 | 代码锚点 | 核心证据 |
|---|---|---|---|---|
| **C1** | 以**失败签名簇**为唯一经验单元的有界蒸馏 | TGL 存 episode 记录且 scaling hypothesis 假设经验累积增长；SSS 累积 repair 片段做 DAgger；PRAGMABOT 只有文本摘要 | `pasd_core.py::OnlineClusterer` / `SkillLibrary.size` / `gates.py::gate1` | 纯度 1 时 `\|B_t\| ≤ k`，与 t 无关；E1 240→9 簇；去 Gate1 复现 211 膨胀 |
| **C2** | **人身安全写进经验单元并作为晋升必要条件** | 9 篇原文 + 4 件专利任务对象都是物体；ARMADA 的人工接管服务于数据质量，不是人身安全 | `schema.py::SafetyEnvelope` / `safety.py` / `gates.py::promote` | `trigger_task/human/safety`；安全包络否决 Gate2 达标但危险的修复；去 Gate3 消融 |
| **C3** | 评测输出驱动**离线**仿真参数分布闭环 + `S³R` 统一协议 | SSS 改训练数据、SOAR 改任务数据、NEERL 改权重，都不改仿真器物理参数分布；现有只报 SR | `evaluation.py` / `domain_rand.py` | `q_t(c) → p_t(θ)`；`Δ = SR − S³R`；SRCC、长尾失败率 |

**耦合**：C1 的簇分布是 C3 的输入；C2 的安全包络进入 C1 的晋升判据；C3 的协议同时度量 C1/C2。这是单模块给不了的技术效果，也是论文立论的根基。

## 3　已被覆盖、**禁止再宣称**为创新的说法

「用失败经验改进策略」「失败后先验证再入库」「结构化记录诊断与修复」「LLM 通过工具白名单控制机器人」「免训练经验记忆」「双闸门独有」。
分别被 SOAR/SSS、SSS/TGL/PRAGMABOT、TGL、TGL/IROSA、TGL、至少 6 篇原文覆盖。

## 4　三条最近邻的划界（必须进主表实验，不能只写在文字里）

| 对照 | 与本文相同 | 本文真实差异 |
|---|---|---|
| **TGL (Teach-and-Grow)** | Claude Code 智能体、工具白名单、结构化经验记忆、验证后入库、免训练 | 经验单元是失败签名簇（有界）而非 episode 级 Skill Block（累积）；仿真定量成功率 + 假晋升率而非结构准入检查；安全包络进入晋升判据；任务对象是人 |
| **SSS (Skill-Space Shooting)** | 失败触发、修复、验证后保留、经验转能力、跨任务复用 | 本文**免梯度更新**、库有界、簇身份去重、仿真定量阈值；SSS 用 VLM judge + DAgger，修复成功率 0.70–0.77 |
| **PRAGMABOT** | VLM 反思、经验复用、检索注入、免训练 | 本文有显式签名结构、去重、仿真验证与晋升状态机；PRAGMABOT 只有 STM/LTM 文本摘要 + RAG |

## 5　题目与投稿

- 中文：《失败签名簇驱动的有界经验蒸馏：面向桌面助餐与取物的人机共域具身智能体》
- 英文：*Bounded, Verified, and Safe Experience Distillation for Human-in-the-Loop Assistive Embodied Agents*
- 原题《面向生活辅助的具身智能体系统研究》偏开题报告，**不宜直接用作 SCI 论文题**（资料库文档标题可保留，论文稿件须改名）。
- 期刊：RA-L（6–8 页，C1+C2 扎实、C3 压缩）／T-RO、Autonomous Robots（10–12 页，三条完整展开）／RAS、Frontiers（系统贡献友好）。

Contribution paragraph 三句骨架见 `paper/claims.md`。

## 6　审稿质疑 Q1–Q5 与回应要点

| 质疑 | 回应 |
|---|---|
| Q1 TGL 已有同构架构，只是换名字 | 经验单元不同、库有界性相反、验证性质不同、任务对象不同；**必须给 TGL 式基线的直接对比实验** |
| Q2 SSS 已有完整闭环，为何免训练 | 真机梯度更新成本高、不可审计、灾难性遗忘；用 SR–episode 曲线证明「免训练但样本效率不劣」；如实报告其 0.70–0.77 |
| Q3 S³R 是自证指标 | 由四个客观传感器/状态判据构成，无主观打分；报告与人类评估者一致性（Cohen's κ）或「SR 相同但 Δ 不同」的回放案例；保留 SR/ET/CR 不替换 |
| Q4 仅单臂、两任务、单用户 | 给 seen/unseen、跨任务签名复用率、多用户意图差异初步实验；Limitation 明写 |
| Q5 知识产权关系 | 见 `docs/07` FTO 边界；如实引用 SSS/TGL，不宣称优先权 |

## 7　时间线与风险

- SSS（2026-09）与 TGL（2026-08）均早于本方案记录时间（2026-11），投稿**必须正面引用划界**。
- 投稿前完成正式检索：arXiv / IEEE Xplore / Google Scholar，关键词 `failure signature clustering`、`verified experience distillation`、`assistive feeding robot safety`、`bounded skill library`、`simulation-gated repair`；并补 CN/IPC 专利检索。
- 若同时申请专利，权利要求须收窄到「簇身份去重 + 仿真定量阈值 + 安全包络进入晋升判据」组合，尽快固定申请日。
- 所有数值口径保持克制：E1/E2 已复现；E3–E7 待真机填充。
