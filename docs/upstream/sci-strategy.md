# SCI 投稿版创新点重构与论证

> 适用：《面向生活辅助的具身智能体系统研究》（资料库节点 `w90lFuGDObXwGlK7X5UoKO`）。
> 触发原因：2026-11-10 逐篇核对 `D:/skill/paper/` 下 9 篇 PASD 参考文献原文后，发现 TGL 与 SSS 已公开与本方案高度同构的机制，原第 8 章创新点口径不足以支撑 SCI 新颖性。
> 配套文件：《PASD参考文献原文核对与勘误.md》《实验对比基线实现规范.md》v1.1。

---

## 0　为什么必须重构

核对后的竞争格局（详见勘误表）：

| 方法 | 失败检测 | 经验/修复 | 验证与准入 | 策略更新 | 任务对象 |
|---|---|---|---|---|---|
| PRAGMABOT (APR) | VLM 逐步成功检测 | STM 反思 / LTM 摘要 + RAG | 任务完成后才写 LTM | 免训练，提示 | 桌面物体 |
| TGL (TAG) | Skill Block pass/fail/inconclusive | Skill Block 七元组 + Experience Memory 七元组（含 diagnosis/repair/evidence） | 五项准入检查 | 免训练，`θ` 固定 | 仿真 LIBERO 物体 |
| SSS | value model 预判 `V<τ` | 技能空间搜索修复片段 | FM judge + 重试上限，只留 accepted repairs | DAgger 式 imitation learning | 4 个真机物体任务 |
| SOAR (AIIFS) | VLM 成功标签 | 30.5K 自主轨迹 | VLM 标注 | 自监督训练 | 集群桌面物体 |
| ARMADA | FLOAT（OT 轨迹匹配）阈值 | 人工纠正数据 | 人工接管确认 | 部署数据后训练 | 多机器人物体 |
| Uni-Skill | 技能缺失检测 | SkillFolder 自演化技能库 | 检索示例语义监督 | few-shot 代码生成 | RLBench / 真机 |
| IROSA | — | 工具参数化技能适配 | validated functions + 保护性抽象层 | 免训练 | 工业插入 |
| NEERL / RLingua | — | 权重内化 | — | 持续学习 / TD3 | 家庭 / RLBench |

**结论**：以下说法已不能作为贡献——「用失败经验改进策略」「失败后先验证再入库」「结构化记录诊断与修复」「LLM 通过工具白名单控制机器人」「免训练经验记忆」。前四项分别被 SOAR/SSS、SSS/TGL/PRAGMABOT、TGL、TGL/IROSA 覆盖。原 8.1 表中「双闸门为独有创新」的表述必须作废。

**仍然成立的空白**（9 篇 + 4 件专利均未覆盖）：
1. 经验的**有界性 / 收敛性**：现有方法都假设经验库随任务累积增长（TGL 的 scaling hypothesis 明确以经验量 `X` 增长为前提；SSS 累积 repair 片段；PRAGMABOT 累积 LTM），无人把「簇身份去重后的库规模上界」作为可证明、可测量的对象。
2. **人身安全作为经验晋升判据**：所有方法的任务对象都是物体，人工介入（ARMADA）服务于数据质量与监控成本，不是人身安全；助餐的口部接近、意图不确定性、误喂、食物温度、接触力未被编码进经验单元。
3. **仿真定量晋升与假晋升率**：现有验证是 VLM judge（软判定）、结构准入检查、OT 分布阈值或人工确认，没有「修复在仿真中重复执行并统计成功率 ≥ 阈值」的物理验证，也没有把「误把无效修复晋升为可信」当作可优化的误差率。
4. **评测→仿真物理参数分布的闭环**：SSS 改变训练数据（加修复片段）、SOAR 改变任务数据分布、NEERL 改权重，均不改变仿真器物理参数分布。
5. **区分「结果成功」与「过程稳定且安全」的评测口径**：现有工作主要报 SR / 成功率。

---

## 1　主论点（一句话贡献声明）

> 现有经验驱动方法优化的是**经验能否被记住并复用**；而在人机共域的生活辅助中，决定能否部署的是**经验能否以有界规模、可验证的可信度、且不牺牲人身安全地被复用**。本文提出以失败签名簇为唯一经验单元的「精炼—验证—安全」三闸门经验生命周期，把这三个约束编码进同一个经验单元与同一套评测口径，并在 PiPER 真机的桌面助餐与取物双任务上给出同时报告精炼性、可信性、安全性三类指标的首个实证。

这句话可以同时充当 Abstract 末句与 Introduction 的 contribution paragraph 首句。三条贡献由此展开，且彼此耦合：C1 的签名簇分布是 C3 的输入；C2 的安全包络进入 C1 的晋升判据；C3 的评测协议同时度量 C1 与 C2。

---

## 2　三条创新点

### C1　以失败签名簇为唯一经验单元的有界经验蒸馏（方法核心）

**要解决的问题**：经验库随部署线性膨胀，检索污染、误触发、存储与审计成本同步上升；现有方法没有把「经验单元如何压缩」当作研究对象。

**技术方案**：
- 经验单元不是 episode、轨迹或文本反思，而是**失败签名簇**：`c = ⟨stage, trigger, features_signature, repair_π, confidence, safety_envelope⟩`。
- Gate1 以簇身份去重（有向取整 + 强归因），Gate2 在仿真中重复执行修复并统计成功率（阈值 ≥0.80），Gate3 真机连续 ≥8 次 + 首次人工确认；三级状态机 `OBSERVED → CANDIDATE → VERIFIED → SAFE`。
- 三级状态与假晋升率作为一等对象记录，而非事后统计。

**可形式化的一点**（SCI 需要理论增量，哪怕很小）：
设失败由 `k` 个潜在物理/交互原因生成，签名映射 `φ` 到原因的簇纯度为 1（E1 已复现 240 次失败 → 9 簇、纯度 1.0、去重率 96%）。则经验库规模 `|B_t| ≤ k`，与 episode 数 `t` 无关；收敛判据可取「连续 `N` 个 episode 无新簇且 `FTR` 落入稳定区间」。给出该上界 + 违反纯度假设时的松弛形式，配合 `|B_t|` 随 `t` 的实测曲线，即可构成可证伪的理论主张。这是 TGL 的 scaling hypothesis（经验越多越好）与本文（经验必须收敛）之间最干净的对照。

**与最近邻划界**：
- vs TGL：经验单元是 episode 级 `μ_j`（累积），且 scaling hypothesis 以 `X` 增长为前提；本文是签名簇（有界），并显式证明上界。
- vs SSS：SSS 把 accepted repair 片段加入 `D_{k+1}` 做梯度更新，库随迭代增长；本文免训练、库有界，修复以可执行提示形式注入。
- vs PRAGMABOT：LTM 是文本摘要 + RAG，无簇结构、无定量验证、无晋升状态机。

**验证指标与实验**：库规模—episode 曲线（对比 TGL 式 / SSS 式 / 去 Gate1 / 本文）、去重率、簇纯度、`FTR`、检索 precision@k、误触发率、收敛所需 episode 数；消融「去 Gate1」应复现 211 膨胀。E1 数据可直接作为预实验。

### C2　面向人机共域的「安全可判定」失败签名（场景 + 方法）

**要解决的问题**：助餐的任务对象是人，不是物体。现有方法的失败定义里没有「意图不确定」「口部接近不安全」「食物温度/盛装量」「接触力」等维度，也没有把安全写进经验质量。

**技术方案**：
- 扩展签名触发维度：`trigger_task`（子目标序号、完成占比）、`trigger_human`（口部位置、意图置信度）、`trigger_safety`（人机距离、末端速度、接触力、食物温度、勺体倾角与盛装量）；环节扩为六类。
- **关键机制**：安全约束不是事后急停，而是写入签名并参与晋升——一个修复即便 Gate2 仿真成功率达标，若违反安全包络（如 `MOUTH_APPROACH_UNSAFE`、`FOOD_SPILL`）也不得进入 `SAFE` 状态；`INTENT_AMBIGUOUS` 强制反问澄清，禁止自动晋升。
- Gate3 把「首次人工确认」变成可审计的部署闸门，而非持续人工监控（区别于 ARMADA 的全时监视 / 按需接管）。

**新颖性论证**：9 篇原文的任务对象均为物体（抽屉、轴承环、海绵、方块等），4 件专利 likewise；ARMADA 的人工接管用于提升数据质量与降低监控成本，不进入经验单元。把人身安全包络作为**经验晋升的必要条件**，在检索到的相关工作中未见。

**验证指标与实验**：最小人机距离、危险接近次数、急停次数、误喂率、意图澄清成功率、Gate3 拦截率、`Δ` 安全代价；消融「去 Gate3」应显著增加危险事件（这是最能打动审稿人的一张图）。需给出真人参与时的伦理/安全说明（假人头部模型或模拟口部位置先做，真人实验须有停机协议）。

### C3　评测输出驱动仿真参数分布更新的闭环 + 统一评测协议（系统与度量）

**要解决的问题**：单一 SR 掩盖「结果成功但过程不稳」；Sim-to-Real 的随机化范围靠人工调参，仿真性能差异部署后并不一致（Kadian 等 SRCC）。

**技术方案**：
- **闭环**：定义失败签名簇上的分布 `q_t(c)`，映射为仿真随机化参数分布 `p_t(θ)`（摩擦、质量、光照纹理、传感器噪声、执行延迟）；以仿真—真实轨迹差异（SRCC 类指标）闭环更新 `p_t`，对长尾簇对应样本重加权，收敛后输出 `p*` 用于批量训练。严格限定**离线训练阶段**，排除「偏差→增量数据→在线微调→推理指针切换」链（CN122735765A 边界）。
- **统一评测协议**：提出复合指标 **S³R（Safe-and-Stable Success Rate）**——只有同时满足「任务完成 + 过程无未恢复失败 + 安全包络不越界 + 无危险接近」的 episode 才计为成功；定义隐性不稳定度 `Δ = SR − S³R`。协议固定三类指令（简单 7 / 隐式 4 / 组合 13 条）、每条 50 独立回合、30 步上限、均值 ± 样本标准差，并把 SR / ET / CR / 过程指标 / 安全代价 / 精炼性指标收编进同一份日志格式。

**划界**：SSS 的 DAgger 改变训练数据内容，SOAR 改变任务数据分布，NEERL 改权重，均不改变仿真器物理参数分布；`Δ` 指标是本文新提，需给出构造性论证（与人类评估者判断的一致性，或至少给出「SR 相同但 Δ 不同」的回放案例），避免被质疑为自证指标。

**验证指标与实验**：SRCC、真实域 SR 与 S³R、仿真—真实性能落差、长尾失败率、收敛所需真实样本数、`Δ` 在各基线与本文之间的差异；消融「去评测驱动随机化」（固定均匀采样）。

---

## 3　最小可发表实验矩阵

| 实验 | 目的 | 方法 | 回合/重复 | 主指标 |
|---|---|---|---|---|
| E1 签名审计（已有） | C1 前提 | 四档阈值策略 | 240 次失败 | 簇数 / 纯度 / 去重率 |
| E2 库规模收敛 | C1 主结论 | 本文 / TGL 式 / SSS 式 / 去 Gate1 / No-Memory | 每方法 200 episode，3 seeds | `|B_t|` 曲线、FTR、precision@k |
| E3 双任务端到端 | C1+C2+C3 | 主表 A 全部免训练基线 | A1 助餐 / A2 取物，三类指令各 50 回合，3 seeds | SR、S³R、ET、CR、Δ |
| E4 安全消融 | C2 主结论 | 去 Gate3 / 完整系统（假人头部先做） | 同上 | 最小人机距离、危险接近、急停、误喂 |
| E5 泛化 | RQ4 | seen/unseen 物体、跨任务签名复用 | 每类 50 回合 | 零样本 SR、簇复用率 |
| E6 迁移闭环 | C3 主结论 | 自适应随机化 vs 固定均匀采样 | 3 轮迭代 | SRCC、真实域落差、长尾失败率 |
| E7 跨范式定位 | 划界 | 副表 C2 需训练组（标注预算） | 只报趋势 | 定性 + 文献数值参照 |

统计：配对 bootstrap 95% CI（或 Wilcoxon signed-rank，多方法比较用 Holm 校正）；所有指标由同一份 `metrics.py` 计算；公开任务配置、随机种子表、复位脚本与日志 schema。真机 PiPER 实验需报告标定参数与复位耗时，避免吞吐差异混入结论。

**基线分组必须按 v1.1 规范**：主表 A 只放免训练方法（含 **TGL 式与 SSS 式的免训练等价实现**，但 SSS 原式需训练，故其原实现放 C2、免训练等价实现放 A 并明确标注差异）；副表 C1/C2 分开；公平性清单 16 条逐项自检。审稿人一定会问「为什么不比 TGL / SSS」，必须在主表里正面回答。

---

## 4　论文定位

**建议题目**（中文）：《失败签名簇驱动的有界经验蒸馏：面向桌面助餐与取物的人机共域具身智能体》
**英文**：*Bounded, Verified, and Safe Experience Distillation for Human-in-the-Loop Assistive Embodied Agents*
原题《…系统研究》偏开题报告，不宜直接用作 SCI 论文题。

**目标期刊**（按篇幅与证据强度选）：
- IEEE Robotics and Automation Letters（RA-L，6–8 页）：需把 C1+C2 做扎实、真机证据强，C3 压缩为一段；
- IEEE Transactions on Robotics / Autonomous Robots（10–12 页）：三条贡献可完整展开，含形式化上界与完整消融；
- Robotics and Autonomous Systems / Frontiers in Robotics and AI：对系统贡献与协议更友好，适合先投 preprint 再投。

**Contribution paragraph 骨架**（英文三句）：
1. We formulate experience distillation as a bounded-state problem and introduce failure-signature clusters as the sole experience unit, with a provable upper bound on library size under purity assumptions (validated by 240→9 clusters, purity 1.0).
2. We encode human-safety envelopes and intent uncertainty directly into the signature and make them a necessary condition for experience promotion, rather than an external runtime interlock.
3. We couple a unified evaluation protocol (S³R, Δ = SR − S³R) to offline simulation-parameter distribution updates, closing the loop between measured failure types and training distributions, and report the first real-robot study on assistive feeding and object retrieval that jointly measures compactness, trustworthiness and safety.

---

## 5　审稿人最可能的五个质疑与回应

| 质疑 | 回应要点 |
|---|---|
| Q1「TGL 已有 Claude Code + Skill Block + Experience Memory + 验证入库，只是换名字」 | 经验单元不同（episode 记录 vs 签名簇）、库规模有界性相反（TGL 假设经验累积增长）、验证性质不同（结构准入检查 vs 仿真定量成功率 + 假晋升率）、任务对象不同（物体 vs 人，安全进入晋升判据）。必须给 TGL 式基线的直接对比实验，不能只在文字里划界。 |
| Q2「SSS 已有失败检测→修复→验证→策略更新，为何还要免训练」 | 真机部署中梯度更新成本高、存在灾难性遗忘与不可审计问题，助餐场景尤其需要可解释、可回放的修复；用 SR–episode 曲线给出「免训练但样本效率不劣」的实证。明确 SSS 的修复成功率 0.70–0.77 作为参照，不回避。 |
| Q3「S³R 是自定义指标，是否自证」 | S³R 由四个客观状态/传感器判据构成，无主观打分；报告与人类评估者判断的一致性（Cohen's κ）或至少给出「SR 相同但 Δ 不同」的回放案例；同时保留 SR / ET / CR 等标准指标，不替换。 |
| Q4「仅双臂？仅两任务、单臂、单用户，泛化性不足」 | 给 seen/unseen 物体、跨任务签名复用率、多用户意图差异的初步实验；在 Limitation 明确写清单臂单人、未覆盖多机器人与长期居家部署。 |
| Q5「与 4 件国内专利及 SSS/TGL 的知识产权关系」 | FTO 边界：CN120134299B 权 1 已并入频域训练数据、冻结视觉/语言模型、投影器改造，FTO 以 B 文本为准；本方案严格限定离线训练阶段，排除 CN122735765A 的「在线微调 + 推理指针切换」。论文中如实引用 SSS/TGL，不宣称优先权。 |

---

## 6　新颖性风险与时间线

- **SSS（arXiv:2609.38178，2026-09）与 TGL（arXiv:2608.17209，2026-08）均早于本方案记录时间（2026-11）**，且已公开与本文高度相邻的机制组合。投稿时**必须正面引用并划界**，回避会被审稿人直接指出。若 PASD 构想文档有可证明的更早时间戳，可作为内部在先工作的说明，但通常只有公开预印本/会议论文才构成公开证据。
- 投稿前须完成一次正式检索：arXiv / IEEE Xplore / Google Scholar，关键词组合 `failure signature clustering`、`verified experience distillation`、`assistive feeding robot safety`、`bounded skill library`、`simulation-gated repair`；并补 CN/IPC 专利检索。
- 若同时计划申请专利，注意 SSS/TGL 已成为评价创造性的最接近现有技术，权利要求须收窄到「簇身份去重 + 仿真定量阈值 + 安全包络进入晋升判据」的组合，并尽快固定申请日。
- 本文所有数值口径保持克制：PASD 的 E1/E2（240→9 簇、纯度 1.0、去重率 96%、FTR 15%–26%）为已复现；E3–E7 为协议与预期，投稿前须以真机实验填充，不得预填成功率。

---

## 7　落地顺序

1. 按 v1.1 规范实现 `MemoryPlugin` 统一适配层与 TGL 式 / PRAGMABOT 式 / PASD 三个免训练基线（先跑通主表 A）；
2. 补 `|B_t|` 收敛曲线与形式化上界（C1 的核心证据，成本最低、说服力最强）；
3. 用假人头部完成 Gate3 安全消融（C2 的核心证据，先于真人实验）；
4. 实现 S³R 与统一日志 schema，把三条贡献纳入同一评测口径（C3 的底座）；
5. 离线随机化分布闭环（C3），注意与鹏城专利划界；
6. 真机双任务 3 seeds × 50 回合完整实验 → 统计检验 → 公开配置与代码 → 投稿。

**边界**：本方案基于所给 9 篇原文、5 篇中文文献与 4 件专利截图，未做外部专利库与文献库的系统检索；所有「空白」判断为相对上述材料而言。
