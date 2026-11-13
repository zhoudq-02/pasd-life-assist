# PASD 构想文档参考文献：原文核对与勘误

> 核对对象：`D:/skill/paper/` 下 9 篇 PDF，对应资料库《PASD：失败签名驱动的经验蒸馏》第 2 章相关工作表与文末参考文献列表。
> 核对时间：2026-11-10。方法：全文文本提取后逐篇核对题名、摘要、方法章节与实验表格。
> 用途：修正《面向生活辅助的具身智能体系统研究》相关工作章节，并修订《实验对比基线实现规范》v1.0。

---

## 0　总结论（先看这一段）

**PASD 构想文档的参考文献列表不是规范引用，而是「缩写 + 推测性展开名」。9 篇里 8 篇的展开名或类别归属与原文不符，其中 5 篇连缩写展开名都是错的；剩下 1 篇（uniskill）类别大体成立但描述失真。**

| 判定 | 数量 | 文献 |
|---|---|---|
| 缩写展开名错误（硬错） | 5 | APR、ARMADA、NEERL、SSS、TAG |
| 展开名未给、类别归属错误 | 3 | AIIFS(SOAR)、IROSA、RLingua |
| 类别大体对但描述失真 | 1 | uniskill |
| 未提供原文、仍为二手 | 2 | Voyager/Reflexion、OpenVLA/RT-2（PASD 列表另两条） |

更实质的影响有两条：

1. **PASD「双闸门是独有创新」的主张无法成立**。9 篇里至少 6 篇有显式验证/准入机制：SOAR 的 VLM 成功检测、PRAGMABOT 的 VLM 成功检测器与「任务完成后才写 LTM」、ARMADA 的 FLOAT 阈值与人工接管、SSS 的 value model + VLM judge + 只保留 accepted repairs、TGL 的 pass/fail/inconclusive 与五项准入检查、IROSA 的「validated parameterized function」保护性抽象层。
2. **最强竞品被误判、最近邻平台被漏掉**。SSS 实际是「失败检测 → 技能空间搜索修复 → 验证 → DAgger 式策略更新」的完整闭环，与 PASD 高度同构；TAG/TGL 实际就是「Claude Code / Codex 作为智能体 + 工具化机器人控制 + 结构化经验记忆 + 验证后入库 + 免训练」，与本项目「Claude Code + PiPER + 白名单 RobotAPI + PASD」几乎是同一架构。二者在 PASD 文档里分别被写成「自监督失败」和「抓取专项」，等于把最需要划界的两篇文献放错了位置。

---

## 1　逐篇核对表

### 1.1 勘误总表

| 文件缩写 | PASD 文献列表写法 | PASD 第 2 章归类 | 原文实际是什么 | 判定 |
|---|---|---|---|---|
| AIIFS | 「AIIFS」 | 语言动作 / 技能·语言策略，无双闸门验证 | SOAR：自主数据收集 + 自监督策略改进（CoRL 2024） | 类别错、描述失真 |
| APR | 「APR: Active Process Reward」 | 过程奖励 / 奖励建模，非结构化签名 | PRAGMABOT：VLM 自我反思 + STM/LTM + RAG | **展开名错、类别错** |
| ARMADA | 「ARMADA: Language Model Action Recognition」 | 语言动作 / 技能·语言策略 | 在线失败检测 FLOAT + 多机器人共享控制 + 后训练 | **展开名错、类别错** |
| IROSA | 「IROSA（IEEE RA-L 已接受）」 | 抓取专项 / 任务·抓取模型 | LLM 工具调用参数化 KMP 技能适配（非抓取专项） | 类别错 |
| NEERL | 「NEERL: Navigation Error Recovery / Failure Recovery」 | 失败驱动 / 从失败恢复，无簇去重与仿真晋升 | 终身/持续具身学习 NBCagent，抗灾难性遗忘 | **展开名错、类别错** |
| RLingua | 「RLingua」 | 语言动作 / 技能·语言策略 | LLM 规则控制器引导 TD3，降低 RL 样本复杂度 | 类别错 |
| SSS | 「SSS: Self-Supervised Failure」 | 失败驱动 / 从失败恢复 | Skill-Space Shooting：失败检测 → 技能修复 → 验证 → DAgger 更新 | **展开名错、类别错，且是最强竞品** |
| TAG | 「TAG: Task-Agnostic Grasping」 | 抓取专项 / 任务·抓取模型 | Teach-and-Grow (TGL)：免训练 Skill Block + 经验记忆 + Claude Code 架构 | **展开名错、类别错，且是平台最近邻** |
| uniskill | 「uniskill: Unified Skill Learning」 | 语言动作 / 技能·语言策略，无双闸门验证 | Uni-Skill：SkillFolder 自演化技能库（VerbNet 层级 + 视频检索） | 类别大体对、描述失真 |

---

### 1.2 逐篇细目

#### ① AIIFS = SOAR

- **原文**：Zhiyuan Zhou, Pranav Atreya, Abraham Lee, Homer Walke, Oier Mees, Sergey Levine (UC Berkeley). *Autonomous Improvement of Instruction Following Skills via Foundation Models*. CoRL 2024, arXiv:2407.20635v2. 方法名 **SOAR**。
- **机制**：把指令跟随拆成「语义任务提案（VLM）→ 语言条件图像生成（图像编辑扩散模型给子目标）→ 非语义目标到达」，用 VLM 做成功检测与语言标注，机器人集群自主采数据，再用自监督目标改进策略，**全程无人工参与**。
- **规模与结果**：5 台 WidowX、每台每天约 1K 轨迹、共 30.5K 自主轨迹 / 3M transitions、53 个物体 / 5 张桌面；未见环境上策略性能约 **2×** 于预训练；开源 SOAR-dataset 与代码。
- **记忆结构**：不是经验库，是**训练数据集**；验证信号是 VLM 成功标签。
- **与本项目关系**：对应研究方案里「自主化数据生成」（曹群等 3.3）与清华专利 CN118194966B 的虚拟环境自动标注，属于**数据上游**，不是记忆机制基线。
- **勘误**：不能写成「语言动作映射、无验证」。应归为「自主数据收集与自监督策略改进」。

#### ② APR = PRAGMABOT（不是 Active Process Reward）

- **原文**：Kaixian Qu, Guowei Lan, Rene Zurbrugg, Changan Chen, Christopher E. Mower, Haitham Bou-Ammar, Marco Hutter (ETH Zurich / Huawei Noah's Ark Lab / UCL). *A Pragmatist Robot: Learning to Plan Tasks by Experiencing the Real World*. arXiv:2507.16713v2. 缩写 APR 来自题名 **A P**ragmatist **R**obot。
- **机制**：verbal RL 范式。VLM 同时作「大脑」与「眼睛」：执行每一步后由 VLM 成功检测器 `R(o_t,a_t,o_{t+1})` 给反馈，**失败反思累积进短期记忆 STM**，任务完成后由 VLM 经验总结器 `S(m)` 把 STM 摘要写入**长期记忆 LTM**；新任务用 `(指令, 初始观测)` 作 key 做 **RAG top-k 检索**（余弦相似度）注入规划器。另有按需图像标注工具支持 3D 接地。（Algorithm 1，ref2.md:133–137）
- **结果**：4 个任务上 STM 自我反思使成功率 **35% → 84%**；12 个真实场景（含 8 个未见任务）上 LTM 单次成功率 **22% → 80%**，RAG 显著优于朴素提示。
- **记忆结构**：STM（episode 内轨迹与反馈）+ LTM（键值对 `(K=指令+场景描述, E=经验摘要)`）+ RAG 检索；这是**双层记忆 + 检索**，比「最近 k 条自然语言教训」强得多。
- **勘误**：这是 **Reflection / 经验记忆类**的正确代表，不是过程奖励。PASD 与我的 v1.0 规范里「APR 式 = 子目标过程奖励」的设定必须删除。同时 v1.0 的 `ReflectionMemory` 应升级为 PRAGMABOT 式实现，否则会低估对照组。

#### ③ ARMADA（不是 Language Model Action Recognition）

- **原文**：Wenye Yu, Jun Lv, Zixi Ying, Yang Jin, Chuan Wen, Cewu Lu (SJTU / Shanghai Innovation Institute / Noematrix). *ARMADA: Autonomous Online Failure Detection and Human Shared Control Empower Scalable Real-world Deployment and Adaptation*. arXiv:2510.02298v1. 全称是 **A**utonomous **R**eal-world **M**ulti-robot system with hum**a**n Assistance for **D**eployment and **A**daptation。
- **机制**：核心是 **FLOAT 在线失败检测器**——对当前 rollout 与专家示教的 **policy embedding 做 Optimal Transport 轨迹匹配**，取最小 OT 代价为 FLOAT index，在全部成功 rollout 上标定**通用阈值**；超阈值判失败，触发 adaptive rewinding（回退到场景被扰动前的时间步）并分配空闲人工操作员接管；接管产生的纠正数据用于策略后训练。支持多机器人并行 rollout。
- **结果**：4 个真机任务，FLOAT 平均近 **95%** 检测准确率，超此前 SOTA **20%+**；三轮 rollout 后成功率提升 **4× 以上**，人工干预率降低 **2× 以上**。
- **勘误**：应归为「在线失败检测 + 人在环自适应」，与「语言动作识别」无关。它有**通用阈值型闸门**（虽非仿真验证），且是本项目 Gate3 / 人机接管 / 安全切换的近邻，值得单独做安全侧对照。

#### ④ IROSA（不是抓取专项）

- **原文**：Markus Knauer, Samuel Bustamante, Thomas Eiband, Alin Albu-Schäffer, Freek Stulp, João Silvério (DLR / TUM). *IROSA: Interactive Robot Skill Adaptation using Natural Language*. IEEE RA-L, 2026 年 2 月接受，DOI 10.1109/LRA.2026.3671560，arXiv:2603.03897v3。
- **机制**：**LLM 不直接碰硬件**，通过 function calling 从经过验证的工具箱里选择并参数化修改原语（速度调制 Speed Modulation、Via-Point Insertion、Repulsion Point 避障、Respond to User），底层是 **KMP（Kernelized Movement Primitives）** 概率运动基元（2–5 条示教即可），保护性抽象层保证可解释、可验证、零样本、免微调。
- **平台**：7-DoF 力矩控制 DLR SARA，工业轴承环插入任务。
- **勘误**：不是抓取专项，是**语言驱动的技能参数化适配**。它与本项目「Claude Code + 白名单 RobotAPI 原语」在架构思想上最同源（工具化隔离），应作为**接口设计对照**，而不是 T1/T2 抓取子任务基线。

#### ⑤ NEERL（不是 Navigation Error Recovery）

- **原文**：Wenqi Liang, Gan Sun, Qian He, Yu Ren, Jiahua Dong, Yang Cong (中科院沈阳自动化所 / 华南理工). *Never-Ending Embodied Robot Learning*. arXiv:2403.00336v1。问题名为 **NERL**（Never-ending Embodied Robot Learning），模型为 **NBCagent**。
- **机制**：**持续学习 / 抗灾难性遗忘**，不是失败恢复。三模块：skill-specific evolving planner（在低秩潜空间解耦并增量嵌入新技能知识）、skill-shared semantics rendering（NeRF + 视觉基础模型在 3D voxel 空间补全共享语义）、skill-shared representation distillation（新旧模型表征对齐）。底座是 PerAct 式语言条件 3D 体素行为克隆。
- **贡献**：提出面向家庭场景（厨房 / 客厅）的持续具身操作 benchmark。
- **勘误**：应归为「终身学习 / 抗遗忘」，对应曹群等综述的「终身学习、灾难性遗忘、增量式更新」，也对应鹏城实验室专利 CN122735765A 的在线增量微调。v1.0 里「NEERL 式 = (state → recovery_action) 查表」的代理设定**完全不成立**，必须删除。

#### ⑥ RLingua

- **原文**：Liangliang Chen, Yutian Lei, Shiyu Jin, Ying Zhang, Liangjun Zhang (Baidu Research / Georgia Tech). *RLingua: Improving Reinforcement Learning Sample Efficiency in Robotic Manipulations With Large Language Models*. arXiv:2403.06420v2。
- **机制**：提示工程让 LLM 生成**不完美但零样本的规则控制器**；rollout 时以**衰减概率**用该控制器产生动作样本存入 `R_LLM`，与在线策略数据 `R_RL` 分开；TD3 的 actor loss 加模仿正则 `ℓ_actor = ℓ_RL + λ_IM·ℓ_IM`，把策略向 LLM 控制器拉近；再用 RL 反过来改进该控制器。
- **实验**：panda_gym 4 任务、RLBench 12 个稀疏奖励任务（标准 TD3 失败）、Franka Panda 上 Sim2Real 真机验证；LLM 为 GPT-4。
- **勘误**：应归为「LLM 先验 + RL 样本效率」，**需要梯度训练**，不是语言—动作映射或技能库。在我的 v1.0 规范里**完全没有出现**，属漏项。

#### ⑦ SSS = Skill-Space Shooting（最强竞品）

- **原文**：Zihang Rui, Renhao Wang, Haoxu Huang, Yang Gao (清华 / UC Berkeley / 上海期智研究院). *Skill-Space Shooting for Autonomous Robot Policy Improvement*. arXiv:2609.38178v1。
- **机制（与 PASD 最同构）**：
  1. **失败预判**：value model `V_φ(o_t, a_{t:t+H-1})` 对「当前观测 + 策略提出的 H 步动作块」打分，`V < τ` 触发；DINOv2 图像特征 + 动作 token → flow-matching head；训练目标成功 `+0.5`、失败前一动作域 `-0.5`；`H=16`、`τ=0` 全任务通用，检测器初始标定后冻结。
  2. **技能空间搜索**：基础模型（Gemini 2.5 Pro）根据场景、指令与可用技能选一个短时域技能，从策略当前失败状态接管执行。
  3. **验证修复**：连续 `c` 次非负检查或执行 `M=100` 个动作后，由 FM 判定该阶段是否修好；`c=8`（Stack-3 / Drawer / Sweeping）、`c=16`（Coffee）；最多 3 次重试，耗尽则丢弃该 rollout。
  4. **DAgger 式更新**：**只保留被接受的技能修复片段**（排除策略自身的错误动作与被拒试验），relabel 任务指令后与初始示教合并 `D_{k+1} = D_0 ∪ ⋃R_j`， imitation learning 更新策略，进入下一轮自主采集。
  5. **技能库跨任务共享**：技能由 UMI 手持示教训练，与任务策略同为 π0.5 类 VLA，动作接口兼容，可无缝交接。
- **结果**（4 个真机任务 Table 2）：value model 触发准确率 0.71–0.83；judge 技能选择准确率 0.90–1.00；**技能修复成功率 0.70–0.77**；judge 完成判定准确率 0.90–0.95。共享技能数据可减少新任务所需示教。
- **勘误**：不是「Self-Supervised Failure」，也不是「从失败恢复但无验证晋升」。它**有失败检测、有修复验证、有准入（accepted repairs only）、有经验转策略更新的闭环**。PASD 文档把它列为「缺少簇身份去重与仿真晋升」的弱对照，会严重低估竞品。

#### ⑧ TAG = Teach and Grow / TGL（平台最近邻）

- **原文**：Chang Nie, Zhe Liu, Hesheng Wang (上海交通大学). *Teach and Grow: An Agent-Centered Architecture for General Robot Learning*. arXiv:2608.17209v3。缩写来自 **T**each **a**nd **G**row，方法名 **TGL**（Teach-and-Grow Learning）。
- **机制**：**training-free**（`θ_{n+1}=θ_n`，无梯度更新、无微调、无 RL），把少量成功示范抽象为可复用的 **Skill Block**：
  `b_i = ⟨g_i, S_i, ρ_i, γ_i, Π_i, v_i, R_i⟩`（目标状态变化 / 适用范围 / 复用策略 / 观测接地 / 兼容执行器 / pass-fail-inconclusive 判据 / 有界恢复选项）。
  另有结构化 **Experience Memory**：`μ_j = ⟨task, context, blocks, outcome, diagnosis, repair, evidence⟩`，记录结果、诊断与成功修复。
  **验证后入库**：block 进入 Skill Library 前须通过 scope、executor compatibility、outcome test、recovery behavior、provenance 五项准入检查；执行时逐块「运行 → 验证效果 → 决定下一步」。
- **架构**：明确以 **Coding agents such as Codex and Claude Code** 为智能体核心，摄像机观测即状态，机器人工具（度量几何、碰撞检查、接触处理、连续控制）即操作，测量的变化即结果；实现用 GPT-6 Astra 做多模态推理、Codex 连接机器人工具。
- **结果**：LIBERO 四套件平均 **99.9%**，LIBERO-Plus 七类扰动 **92.4%**，权重固定；受控实验显示 taught blocks 能保持并改善相关任务。
- **勘误**：不是「Task-Agnostic Grasping」，更不是抓取专项；它是**与本项目同构的免训练智能体架构**，且已明确记录 failures / repairs 到经验记忆。这直接冲击「Claude Code + 工具白名单 + 失败签名经验库」这一组合的新颖性表述，必须在论文相关工作里正面划界。

#### ⑨ uniskill = Uni-Skill

- **原文**：Senwei Xie, Yuntian Zhang, Ruiping Wang, Xilin Chen (中科院计算所 / 国科大). *Uni-Skill: Building Self-Evolving Skill Repository for Generalizable Robotic Manipulation*. arXiv:2603.02623v1。
- **机制**：**技能感知规划**（发现缺失技能并生成高层描述）+ **自动技能演化**。构建 **SkillFolder**：VerbNet 启发的层级技能分类库，从大规模无结构机器人视频自动标注，含 **>10,000 技能轨迹 / 106 个 VerbNet 类 / 1,659 种技能表述**；缺失技能时按语义检索相似技能轨迹作为行为模式与空间轨迹参考，**few-shot 生成新技能实现（策略代码）**，无需部署时示教。
- **结果**：RLBench 上超出预定义技能的任务零样本成功率比 MOKA 高 **31.0%**；真机长时序任务 **+20.0%**、未见技能 **+34.0%**。
- **勘误**：类别（技能/语言策略）大体对，但「固定技能库、无验证」的描述失真——它是**自演化技能库**，且新技能实现有检索示例的语义监督。v1.0 的 `SkillBank`（只存成功、不去重、不验证）可作为其**简化版对照**，但必须标 `proxy` 并说明舍弃了 SkillFolder 层级检索。

---

## 2　对《面向生活辅助的具身智能体系统研究》的实质影响

### 2.1 相关工作章节必须重写

建议按原文实际机制重新分组，替换 PASD 第 2 章那张表：

| 组 | 应归入的文献 | 与本项目/PASD 的真实关系 |
|---|---|---|
| 经验记忆与自反思（免训练） | PRAGMABOT(APR)、TGL(TAG) | **最近邻**，需正面比较记忆结构与验证准入 |
| 失败驱动的自主改进（需训练） | SSS、ARMADA、SOAR(AIIFS) | **最强竞品**，需说明 PASD 免训练与簇去重的差异 |
| 技能库与技能演化 | Uni-Skill、IROSA、TGL | 工具化/技能表示对照 |
| 终身学习与样本效率 | NEERL(NBCagent)、RLingua | 对应鹏城专利的在线增量更新与训练侧迁移 |
| 端到端 VLA | OpenVLA / RT-2（未提供原文） | 保留降级为文献数值参照 |

### 2.2 PASD 新颖性划界要收窄

原文核对后，下面这些**不能**再作为 PASD 的独有主张：

- 「用失败经验改进策略」（SOAR / SSS / ARMADA 都有）
- 「失败后先验证再入库」（PRAGMABOT 的 VLM 成功检测、SSS 的 accepted repairs、TGL 的五项准入检查、ARMADA 的 FLOAT 阈值都有）
- 「结构化记录诊断与修复」（TGL 的 `μ_j` 七元组已经做了）
- 「LLM/智能体通过工具白名单控制机器人」（TGL、IROSA 都做了）

仍能成立、且值得写进权利要求与创新点的是**更窄的组合**：

1. **簇身份去重**：以失败签名的簇身份而非状态相似度做经验去重（E1 已复现 240→9 簇、纯度 1.0、去重率 96%），这是 9 篇里没有的精炼性机制；
2. **仿真定量晋升阈值 + 假晋升率度量**：现有方法用 VLM judge / 人工接管 / OT 阈值，PASD 用 Gate2 仿真成功率阈值（研究方案里 ≥0.80）并把「假晋升率」作为可优化指标；
3. **免梯度更新**：相对 SSS / SOAR / ARMADA / NEERL / RLingua 这些需要 imitation learning 或 RL 后训练的方法，PASD 与 TGL 同属 training-free，需靠前两条区分；
4. **面向生活辅助的安全闸门**：口部位置、人机距离、末端速度、接触力、食物温度等 `trigger_safety` 与 Gate3 真机确认，9 篇均未涉及（ARMADA 的人工接管最接近但服务于数据质量而非人身安全）。

### 2.3 实验基线的三处结构性改动

1. **Reflection 基线升级**为 PRAGMABOT 式 STM/LTM + RAG（含 VLM 成功检测），纯 Reflexion 保留为下界，否则对照组被人为削弱。
2. **TGL 与 SSS 进主表**（不是副表 C 的 `proxy` 趋势行）：前者与本平台同构，后者是最强竞品，二者是审稿人一定会问的对照。
3. **拆开「需训练」与「免训练」两组**：数据/算力预算不可比，同表做显著性检验无效。

---

## 3　建议采用的规范引用条目

按 arXiv 编号与原文首页信息整理，投稿前请在 arXiv / 会议官网核对卷期、页码与 DOI：

1. Zhou Z, Atreya P, Lee A, Walke H, Mees O, Levine S. **Autonomous Improvement of Instruction Following Skills via Foundation Models (SOAR)**. 8th Conference on Robot Learning (CoRL), 2024. arXiv:2407.20635.
2. Qu K, Lan G, Zurbrugg R, Chen C, Mower C E, Bou-Ammar H, Hutter M. **A Pragmatist Robot: Learning to Plan Tasks by Experiencing the Real World (PRAGMABOT)**. arXiv:2507.16713, 2025.
3. Yu W, Lv J, Ying Z, Jin Y, Wen C, Lu C. **ARMADA: Autonomous Online Failure Detection and Human Shared Control Empower Scalable Real-world Deployment and Adaptation**. arXiv:2510.02298, 2025.
4. Knauer M, Bustamante S, Eiband T, Albu-Schäffer A, Stulp F, Silvério J. **IROSA: Interactive Robot Skill Adaptation using Natural Language**. IEEE Robotics and Automation Letters, 2026 (accepted). DOI: 10.1109/LRA.2026.3671560. arXiv:2603.03897.
5. Liang W, Sun G, He Q, Ren Y, Dong J, Cong Y. **Never-Ending Embodied Robot Learning (NBCagent)**. arXiv:2403.00336, 2024.
6. Chen L, Lei Y, Jin S, Zhang Y, Zhang L. **RLingua: Improving Reinforcement Learning Sample Efficiency in Robotic Manipulations With Large Language Models**. arXiv:2403.06420, 2024.
7. Rui Z, Wang R, Huang H, Gao Y. **Skill-Space Shooting for Autonomous Robot Policy Improvement**. arXiv:2609.38178, 2026.
8. Nie C, Liu Z, Wang H. **Teach and Grow: An Agent-Centered Architecture for General Robot Learning (TGL)**. arXiv:2608.17209, 2026.
9. Xie S, Zhang Y, Wang R, Chen X. **Uni-Skill: Building Self-Evolving Skill Repository for Generalizable Robotic Manipulation**. arXiv:2603.02623, 2026.

---

## 4　边界与待核验事项

- 本次核对基于本地 PDF 的**文本提取内容**，部分插图未导出；公式与表格数值取自可读文本，个别表格数值（SSS Table 2 等）建议对照原版 PDF 版面再确认一次。
- APR / NEERL / SSS / TAG 的缩写拆解系按题名与方法名推断，原文未逐字母定义缩写；ARMADA 的全称见原文引言，缩写拆解仍属推断。
- 部分论文涉及的模型版本号较新（TGL 的 GPT-6 Astra、SSS 的 Gemini 2.5 Pro / π0.5 类 VLA、IROSA 的 RA-L 2026 卷期），引用前建议在 arXiv 摘要页或出版方页面核对版本、卷期与 DOI。
- **Voyager / Reflexion / OpenVLA / RT-2 四篇原文未提供**，仍是二手描述；v1.1 规范中保留其「公开方法」标注，但不声称已核对原文。
- 本勘误不改变此前关于 4 件专利的 FTO 结论，但**可能改变 PASD 相关创新点的新颖性论证**；若拟据此申请专利，需补做针对 SSS 与 TGL 的权利要求比对（二者均早于本方案构思时间）。
