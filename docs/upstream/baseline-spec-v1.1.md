# 实验对比基线实现规范 v1.1

> 配套《面向生活辅助的具身智能体系统研究》第 7.2 节「算法范式对比」。
> 平台：Claude Code（code-as-policy）+ AgileX PiPER 6-DoF + MuJoCo；任务族 T1–T7 / A1 助餐 / A2 取物。
> **v1.1 修订依据**：`D:/skill/paper/` 下 9 篇 PASD 参考文献原文已逐篇核对，勘误详见同目录《PASD参考文献原文核对与勘误.md》。

---

## 0　v1.0 → v1.1 变更摘要

| # | v1.0 | v1.1 | 原因 |
|---|---|---|---|
| 1 | 基线名单按 PASD 文献列表的缩写与归类 | 按 9 篇原文实际机制重新分组 | 8 篇归类/展开名有误 |
| 2 | Reflection = 「最近 k 条自然语言教训」 | 升级为 PRAGMABOT 式 STM/LTM + RAG + VLM 成功检测 | APR 不是过程奖励，原文是双层记忆检索 |
| 3 | NEERL / APR / SSS 三个「失败驱动」代理 | 删除该组设定，重排为免训练组与需训练组 | NEERL 是终身学习；SSS 是完整修复闭环 |
| 4 | SkillBank 统一「只存成功、不验证」 | 拆为 TGL 式（验证后入库）与 Uni-Skill 简化代理（无验证） | TGL 有五项准入检查与失败/修复记录 |
| 5 | 副表 C 一张表放全部跨范式代理 | 拆为 C1（免训练）/ C2（需训练） | 训练与数据预算不可比 |
| 6 | 第 6 节声明「缩写未核对原文」 | 改为「9 篇已核对，仍为机制等价代理」 | 原文已提供 |
| 7 | `MemoryPlugin` 只有两个注入点 | 增加可选 `on_step_end` 钩子（默认 no-op） | PRAGMABOT 的 STM 是 episode 内逐步反馈 |
| 8 | 公平性清单 12 条 | 16 条，新增训练预算、FM 判官调用、人工监督、写入时机 | 新基线引入新混淆变量 |

**最重要的一条**：v1.0 把 SSS 当作「自监督失败预测」、把 TAG 当作「抓取专项」，等于把最强竞品和本平台最近邻放到了错误位置。v1.1 把 **SSS（技能空间射击）与 TGL（Teach-and-Grow）提升为主表对照组**，并据此收窄 PASD 的新颖性主张。

---

## 1　两个设计缺口（v1.0 只发现了一个）

### 1.1 对比轴不同

| 组 | 回答 | 对比轴 | 能否同表比较 |
|---|---|---|---|
| 记忆结构对比 | RQ1 | 同一策略生成器、同一执行平台，只换「经验怎么存、怎么取」 | 能，主表 A |
| 算法范式对比 | RQ3 | 各范式原生形态不同：有的改策略、有的需训练、有的只做抓取/插入 | 不能直接用原生形态 |
| 消融 | RQ1/RQ2 | 同一系统内逐个摘除组件 | 能，主表 B |

### 1.2 训练预算不同（v1.1 新增）

原文核对后，9 篇可按「是否更新策略权重」分成两类：

| 免训练（training-free） | 需梯度训练 |
|---|---|
| PRAGMABOT（VLM 提示 + 记忆）、TGL（θ 固定）、IROSA（免微调）、Uni-Skill（检索 + few-shot 代码生成）、PASD | SSS（DAgger 式 imitation learning）、SOAR（自监督策略改进）、ARMADA（部署数据后训练）、NEERL（低秩持续学习）、RLingua（TD3 + actor 正则） |

把两类放进同一张表做显著性检验，差异会来自示教数量、GPU 时长与环境交互步数，而不是经验机制。**必须分表**，并把额外预算写进实验配置。

### 1.3 解决办法（不变）

把所有基线统一「翻译」为 `MemoryPlugin`，只问同一个问题：**如果让这个范式来充当系统的记忆/学习模块，它在「失败后写什么、规划前读什么」上会怎么做？** 策略生成器、执行器、成功判据、评测代码保持不变。

---

## 2　统一适配层（v1.1 接口）

### 2.1 接口定义

```python
# integration/baselines/base.py
from dataclasses import dataclass
from typing import Protocol

@dataclass
class RepairHint:
    text: str                       # 注入 Claude Code prompt 的自然语言片段
    executable: dict | None         # 可选：给 Executor 的机器可执行修复
    verified: bool                  # 是否经过某种验证/准入
    verified_by: str                # "simulation" | "vlm_judge" | "admission_check" | "human" | "none"
    source: str                     # 来源：签名/簇 ID、反思序号、技能 ID

class MemoryPlugin(Protocol):
    name: str
    def retrieve(self, ctx: SceneContext) -> list[RepairHint]:
        """规划前的唯一记忆注入点。No-Memory 恒返回 []。"""
    def on_episode_end(self, trace: Trace) -> None:
        """episode 末的唯一写库点。所有持久化写库动作只允许发生在这里。"""
    def on_step_end(self, feedback: StepFeedback) -> None:
        """可选 episode 内钩子，默认 no-op。供 PRAGMABOT 式 STM 收集逐步反馈。
        所有基线必须实现该方法（哪怕是空实现），禁止在基线内部另写执行循环。"""
    def snapshot(self) -> dict:
        """必须含：library_size, verified, requires_training,
        human_budget, extra_demos, fm_calls，供公平性审计。"""
```

`verified_by` 是 v1.1 的关键修正：v1.0 假设「PASD 之外一律无验证」，但原文里 PRAGMABOT、TGL、SSS、ARMADA、SOAR、IROSA 都有各自的验证/准入机制。统一填 `verified=False` 会人为削弱对照组。

### 2.2 共享 EpisodeRunner

```python
# integration/runner.py
def run_episode(policy_gen, memory: MemoryPlugin, env, task, seed):
    ctx = env.reset(task, seed)
    hints = memory.retrieve(ctx)                      # ① 唯一读点
    code = policy_gen.generate(task, ctx, hints)      # Claude Code，仅调 RobotAPI 五个原语
    try:
        obs = Executor(env).run(code, step_cb=memory.on_step_end)  # ② 逐步反馈钩子
        trace = Trace.from_success(task, obs, ctx)
    except PiPERError as e:
        trace = Trace.from_error(task, e, ctx)        # ③ 唯一失败输入
    success = judge(task, env.state)                  # 自动成功判据，所有方法同一份
    if ctx.split == "dev":
        memory.on_episode_end(trace)                  # ④ 唯一写点
    log(trace, success, memory.snapshot())
    return success, trace
```

PASD 的 `observe_failure`（Gate1）、`verify_gate2`（Gate2）、`verify_gate3`（Gate3）、`retrieve_repair` 全部折叠进 `retrieve` / `on_episode_end`，不额外开后门；其 `on_step_end` 为空实现。

### 2.3 代码落点（更新）

| 文件 | 职责 |
|---|---|
| `integration/baselines/base.py` | `MemoryPlugin` / `RepairHint` / `StepFeedback` |
| `integration/baselines/{no_memory,trajectory,episodic,pasd}.py` | 主表 A 核心基线 |
| `integration/baselines/pragmabot.py` | PRAGMABOT 式 STM/LTM/RAG（替代 v1.0 的 reflection.py） |
| `integration/baselines/tgl_skill.py` | TGL 式 Skill Block + Experience Memory + 准入检查 |
| `integration/baselines/uniskill_proxy.py` | Uni-Skill 简化代理（无 SkillFolder） |
| `integration/baselines/{sss,soar,armada,neerl,rlingua,vla_proxy}.py` | 需训练组代理，副表 C2 |
| `integration/baselines/irosa_interface.py` | 接口设计对照，不参与 SR 主表 |
| `integration/runner.py` / `judge.py` / `metrics.py` / `robot_api.py` | 共享循环、判据、指标、白名单 API |

---

## 3　免训练组（主表 A / 副表 C1）

### 3.1 PRAGMABOT 式 STM / LTM / RAG（替换 v1.0 的 Reflection）

原文要点：VLM 成功检测器 `R(o_t,a_t,o_{t+1})` 逐步给反馈；失败反思累积进 STM；**任务完成后**才把 STM 摘要 `S(m)` 写入 LTM；新任务用 `(指令, 初始观测)` 作 key 做 RAG top-k 检索注入规划器（Algorithm 1）。实测 STM 35%→84%、LTM 22%→80%。

```python
# integration/baselines/pragmabot.py
class PragmabotMemory:
    """PRAGMABOT 式：episode 内 STM + 任务完成后 LTM + RAG 检索。"""
    def __init__(self, vlm, encoder, k=5):
        self.vlm, self.enc, self.k = vlm, encoder, k
        self.stm: list[tuple] = []          # [(action, feedback, reflection)]
        self.ltm: list[tuple] = []          # [(key_vec, summary_text)]

    def on_step_end(self, fb: StepFeedback):
        r = self.vlm.success_detect(fb.obs_before, fb.action, fb.obs_after)  # 共享预算
        refl = None if r.success else self.vlm.reflect(fb, max_tokens=128)
        self.stm.append((fb.action, r, refl))

    def on_episode_end(self, trace: Trace):
        if trace.success:                                   # 原文：完成后才入 LTM
            summary = self.vlm.summarize(self.stm, max_tokens=128)
            self.ltm.append((self.enc(trace.instruction + trace.scene_summary), summary))
        self.stm.clear()

    def retrieve(self, ctx):
        rag = cosine_top_k(self.ltm, self.enc(ctx.instruction + ctx.scene_summary), self.k)
        recent = [x[2] for x in self.stm if x[2]][-self.k:]
        hints = [RepairHint(t, None, False, "none", f"rag#{i}") for i, t in enumerate(rag)]
        hints += [RepairHint(t, None, False, "none", f"stm#{i}") for i, t in enumerate(recent)]
        return hints[:self.k]

    def snapshot(self):
        return {"library_size": len(self.ltm), "verified": 0, "requires_training": False,
                "human_budget": 0, "extra_demos": 0, "fm_calls": self.vlm.call_count}
```

**公平项**：VLM 成功检测与反思生成的调用次数、`max_tokens` 必须与 PASD 的 `propose_repair` 对齐；RAG 的 `k` 与 PASD `retrieve` 返回上限一致。纯 Reflexion（只存最近 k 条教训、无 RAG、无成功检测）保留为**下界**，放副表 C1，不要与 PRAGMABOT 合并计数。

### 3.2 TGL 式 Skill Block + Experience Memory（平台同构，必须进主表 A）

原文要点：training-free；Skill Block 七元组 `⟨g,S,ρ,γ,Π,v,R⟩`；Experience Memory 七元组 `⟨task,context,blocks,outcome,diagnosis,repair,evidence⟩`；逐块「运行 → 验证效果（pass/fail/inconclusive）→ 决定下一步」；入库前有 scope、executor compatibility、outcome test、recovery behavior、provenance 五项准入检查；实现用 Claude Code / Codex 连接机器人工具。实测 LIBERO 99.9%、LIBERO-Plus 92.4%。

```python
# integration/baselines/tgl_skill.py
class TGLSkillMemory:
    """标注为机制等价代理：复现 Block/Experience 结构与准入逻辑，不复现 GPT-6 Astra 实现。"""
    def __init__(self, encoder, k=3):
        self.enc, self.k = encoder, k
        self.blocks: list[dict] = []      # g,S,rho,gamma,Pi,v,R
        self.experience: list[dict] = []  # task,context,blocks,outcome,diagnosis,repair,evidence

    def on_episode_end(self, trace: Trace):
        # 关键差异：成败都记录，诊断与修复进 Experience Memory
        self.experience.append({
            "task": trace.task.tag, "context": trace.scene_summary,
            "blocks": [b["id"] for b in trace.used_blocks],
            "outcome": "pass" if trace.success else "fail",
            "diagnosis": trace.error_code, "repair": trace.applied_repair,
            "evidence": trace.obs_refs,
        })
        for cand in trace.candidate_blocks:
            if admission_checks(cand, trace):    # 五项准入，见原文 IV 节
                self.blocks.append(cand)

    def retrieve(self, ctx):
        ranked = cosine_top_k(self.blocks, self.enc(ctx.instruction), self.k)
        lessons = match_experience(self.experience, ctx)[:self.k]
        return [RepairHint(fmt_block(b), None, True, "admission_check", b["id"]) for b in ranked] + \
               [RepairHint(fmt_lesson(e), None, False, "none", "exp") for e in lessons]

    def snapshot(self):
        return {"library_size": len(self.blocks), "verified": len(self.blocks),
                "requires_training": False, "human_budget": self.teaching_calls,
                "extra_demos": self.demo_count, "fm_calls": self.fm_calls}
```

**这是与本项目最同构的基线**：Claude Code 智能体、工具白名单、结构化经验记忆、验证后入库、免训练全部重合。论文必须在相关工作与讨论章节正面比较，不能用 `proxy` 一行带过。PASD 的区分点只能是簇身份去重、仿真定量阈值、假晋升率度量与生活辅助安全闸门。

### 3.3 Uni-Skill 简化代理（副表 C1）

原文 SkillFolder 含 >10,000 技能轨迹 / 106 VerbNet 类 / 1,659 技能表述，从无结构视频自动标注并按层级检索生成新技能实现。本平台不迁移该数据资产，代理只保留「按指令检索技能代码 + 缺失时请求新技能」：

- `retrieve`：按指令 embedding 取 top-k 技能代码注入；缺失技能时生成一条 `SkillRequest` 文本。
- `on_episode_end`：只存成功轨迹对应的技能代码，无 Gate1 去重、无 Gate2 验证。
- 必须显式标注舍弃了 SkillFolder 层级检索与视频语义监督，`verified_by="none"`。

### 3.4 IROSA 工具化接口对照（不进 SR 主表）

原文是 LLM 通过 function calling 选择并参数化**经过验证的** KMP 修改工具（速度调制、via-point、斥力场避障），保护性抽象层隔离 LLM 与硬件。它与本项目 `RobotAPI` 白名单同一设计思想，用于支撑「接口标准化」论证与权利要求撰写，**不作为性能基线**（原任务是 7-DoF 工业插入，与桌面助餐/取物任务错配）。

---

## 4　需训练组（副表 C2，必须标注预算）

### 4.1 SSS 技能空间射击（最强竞品）

原文闭环：value model `V_φ(o_t, a_{t:t+H-1}) < τ` 预判失败（`H=16, τ=0`）→ 基础模型从技能库选修复行为 → 连续 `c` 次非负检查或 `M=100` 动作后由 FM 判定修复是否成立，最多 3 次重试 → **只保留 accepted repair 片段**，relabel 后与初始示教合并做 DAgger 式 imitation learning 更新策略 → 技能库跨任务共享。实测（4 个真机任务）：触发准确率 0.71–0.83、技能选择准确率 0.90–1.00、修复成功率 0.70–0.77、完成判定 0.90–0.95。

**落地方案（二选一）**：

- **方案 A（推荐）**：作为**文献数值参照 + 定性划界**，不进显著性检验。理由：其策略是 π0.5 类 VLA + UMI 示教，与本平台 code-as-policy / PiPER 的动作接口、示教预算、训练算力均不可对齐。
- **方案 B（若坚持上机）**：实现插件等价代理，并给**所有免训练基线等量示教预算**（同 N 条），否则结论无效；且需单独列 C2 表，注明 `proxy`。

```python
# integration/baselines/sss.py —— 仅在方案 B 启用
class SSSProxy:
    def __init__(self, fm, skills, k=1):
        self.fm, self.skills = fm, skills
        self.accepted: list[dict] = []       # 只存被接受的修复片段
        self.pending_retries = 0

    def on_episode_end(self, trace: Trace):
        if trace.repair_verified:             # FM judge 判定，verified_by="vlm_judge"
            self.accepted.append(trace.repair_segment)
        # 真实 SSS 在此处做 D_k+1 = D_0 ∪ ⋃R_j 的 imitation learning 更新；
        # 本代理不做梯度更新，须在表中注明，否则与免训练组混淆

    def retrieve(self, ctx):
        if risk_score(ctx) < TAU: return []
        skill = self.fm.select_skill(ctx, self.skills)
        return [RepairHint(f"建议调用技能修复：{skill}", {"skill": skill},
                           False, "none", "skill_space_shooting")]

    def snapshot(self):
        return {"library_size": len(self.accepted), "verified": len(self.accepted),
                "requires_training": True, "human_budget": self.demo_count,
                "extra_demos": self.demo_count, "fm_calls": self.fm.call_count}
```

### 4.2 其余四个代理（表格实现约定）

| 基线 | 原文机制 | `on_episode_end` 写什么 | `retrieve` 返回什么 | 需对齐的预算 | 检验 PASD 哪部分 |
|---|---|---|---|---|---|
| SOAR | 自主数据收集 + VLM 成功标签 + 自监督策略改进（30.5K 轨迹、2× 提升） | VLM 标注后的轨迹（不是经验条目） | 恒 `[]`（无外部记忆） | 机器人日采样量、GPU 训练时长 | 「数据上游 vs 经验蒸馏」的分工 |
| ARMADA | FLOAT（OT 轨迹匹配）+ 通用阈值失败检测 + 自适应回退 + 人工接管 + 后训练（约 95% 准确率、成功率 4×） | 人工纠正片段 | 失败风险提示 + 回退建议 | **人工干预次数**、示教数量 | Gate3 安全闸门与人机接管 |
| NEERL | NBCagent 终身学习 / 抗遗忘（低秩 planner + 语义渲染 + 表征蒸馏） | 新技能训练样本（非文本经验） | 恒 `[]`，差异在权重 | 训练步数、旧任务回放预算 | 「显式经验库 vs 权重内化」与遗忘率 |
| RLingua | LLM 规则控制器以衰减概率产样本 + TD3 actor 正则 | `R_LLM` 与 `R_RL` 两个 replay buffer | 恒 `[]` | **环境交互步数**、RL 更新次数 | code-as-policy 的样本效率 |

四者都 `requires_training=True`，`snapshot()` 必须返回实际用量；结果表须在表头注明各自的额外预算，且**不与主表 A 做同一显著性检验**。

### 4.3 VLA 端到端（OpenVLA / RT-2 类）—— 沿用 v1.0 的降级结论

本平台无法公平原生复现（无适配 PiPER 的 checkpoint、需大规模示教与微调、动作 token 与 `RobotAPI` 原语不同），只做协议对照与文献数值参照，或标注 `proxy` 的轻量 LoRA 代理。若坚持纳入主表，必须给其余所有基线等量示教预算。原文未提供，仍为二手描述。

---

## 5　与 PASD 划界的三条基线（必须写进论文）

| 对照 | 与 PASD 相同 | PASD 的真实差异 | 论文必须声明 |
|---|---|---|---|
| **SSS** | 失败触发、修复、验证后保留、经验转能力、跨任务复用 | PASD **免梯度更新**（SSS 需 DAgger 式训练）；PASD 以**簇身份去重**压缩经验库（240→9 簇、纯度 1.0、去重率 96%）；PASD 用**仿真定量阈值**与**假晋升率**度量可信性，SSS 用 VLM judge；PASD 有生活辅助安全闸门 | 不得再写「已有方法无验证晋升」；须引用其修复成功率 0.70–0.77 作对照 |
| **TGL** | Claude Code 智能体、工具白名单、结构化经验记忆、验证后入库、免训练 | PASD 存的是**失败签名簇与可执行修复**而非通用 Skill Block；有簇身份去重、仿真 Gate2、Gate3 真机连续确认；面向助餐/取物的人身安全约束 | 二者架构同构，相关工作须正面比较，不能用「抓取专项」带过 |
| **PRAGMABOT** | VLM 反思、经验复用、检索注入、免训练 | PASD 有显式签名结构、去重、仿真验证与晋升状态机；PRAGMABOT 只有 STM/LTM 文本摘要 + RAG | 作为「结构化签名 vs 自然语言反思」的强对照，比纯 Reflexion 更有说服力 |

---

## 6　公平性控制清单（16 条，新增 13–16）

| # | 控制项 | 具体做法 |
|---|---|---|
| 1 | 同一动作空间 | 全部经白名单 `RobotAPI` 五原语；禁止基线自带控制接口 |
| 2 | 同一策略生成器 | 同一 Claude Code 配置、同一 system prompt 模板、同一 temperature |
| 3 | 同一任务与划分 | 同一 T1–T7 / A1 / A2，同一 seen/unseen 物体与场景划分 |
| 4 | 同一成功判据 | 同一 `judge()`、30 步上限、自动判定 + 自动复位 |
| 5 | 同一 episode 预算 | 每方法 200 episode 学习曲线；A1/A2 三类指令（7/4/13 条）各 50 独立回合 |
| 6 | 同一 LLM 调用与 token 预算 | PRAGMABOT / SSS / TGL / PASD 的失败后生成次数与 `max_tokens` 上限一致 |
| 7 | 同一数据预算 | 任一基线用 N 条示教，其余基线须可等量访问同 N 条数据 |
| 8 | 同一注入长度 | `retrieve` 返回条数上限 k 与截断策略一致 |
| 9 | 同一防污染约束 | 白名单 API 禁仿真真值；开发集可写库、留出集只记录 |
| 10 | 同一随机种子序列与复位脚本 | 固定种子表，脚本化复位 |
| 11 | 同一指标计算代码 | 全部走 `integration/metrics.py` |
| 12 | 同一硬件/仿真标定 | 摩擦与夹持力标定冻结后共用 |
| **13** | **训练/免训练分组隔离** | `snapshot()["requires_training"]` 决定进 C1 还是 C2，两类不同表做显著性 |
| **14** | **FM/VLM 判官调用预算对齐** | PRAGMABOT 成功检测、SSS 修复判定、TGL outcome check、PASD Gate2 仿真调用次数统一记账 |
| **15** | **人工监督预算对齐** | ARMADA 接管次数、TGL 示教次数、PASD Gate3 首次人工确认须分别列明并折算 |
| **16** | **经验写入时机对齐** | episode 内 STM vs 任务完成后 LTM、成功才写 vs 成败都写，须在表中标注，避免「写得多」被误读为「学得好」 |

第 6、7、13 三条最容易被忽略，也是这类对比最常出问题的地方。

---

## 7　结果表分层与统计口径（更新）

| 表 | 内容 | 用途 | 显著性主结论 |
|---|---|---|---|
| **主表 A** | No-Memory / Trajectory Storage / Episodic Replay / **PRAGMABOT 式** / **TGL 式** / PASD 原版 / 本系统（全部免训练） | RQ1 精炼性、RQ3 有效性 | 是 |
| **主表 B** | 消融：去 Gate1、去 Gate2、去 Gate3、去任务级签名扩展、去有向取整、去评测驱动随机化 | RQ1/RQ2 组件归因 | 是 |
| **副表 C1** | 纯 Reflexion 下界 / Uni-Skill 简化代理 / IROSA 接口对照 | 免训练范式定位 | 否，只报趋势 |
| **副表 C2** | SSS / SOAR / ARMADA / NEERL / RLingua 代理（表头注明训练与数据预算） | 需训练范式定位 | 否，只报趋势 |
| **副表 D** | 假晋升率、最小人机距离、急停次数、SRCC、长尾失败率、未见物体零样本成功率 | RQ2 安全、RQ4 泛化与迁移 | 是 |

统计口径沿用安冉等 [4]：三类指令分别计算均值 ± 样本标准差，每条 50 回合，SR 为 30 步内完成占比，ET 为输入指令到动作序列结束耗时，CR 为已完成子目标占比。

**`verified` 口径修正**：v1.0 规定「PASD 之外一律 False」不再成立。各基线按 `verified_by` 分别统计：仿真（PASD Gate2）、准入检查（TGL）、VLM judge（SSS）、人工接管（ARMADA）、无（Uni-Skill 代理、纯 Reflexion）。「假晋升率」只对**存在晋升状态机**的方法计算，其余记 N/A 并注明机制原因，不要填 0 充数。

**论文措辞**：主结论只由主表 A/B 支撑；副表 C1/C2 表述为「在统一记忆插件接口下的机制等价参照」，不得写成「复现了 SSS / TGL / PRAGMABOT」，除非真正移植了原实现。

---

## 8　落地顺序（更新）

1. `MemoryPlugin` 接口（含 `on_step_end` 与 `snapshot` 六字段）+ `EpisodeRunner` + `judge` + `metrics`
2. No-Memory / Trajectory Storage / Episodic / PASD（主表 A 核心，复用现有 `integration/pasd*.py`）
3. **TGL 式**（平台同构，审稿人必问，优先于其他跨范式基线）
4. **PRAGMABOT 式**（强 Reflection 对照，检验结构化签名）
5. 失败驱动需训练组代理（SSS 优先，其余按预算排期）
6. Uni-Skill 简化代理 / 纯 Reflexion 下界
7. VLA proxy 最后，仅在数据预算与算力允许时纳入副表

每完成一个基线，先跑一次 16 条公平性清单自检再进实验队列。

---

## 9　边界与核对状态（替换 v1.0 第 6 节）

- **9 篇 PASD 参考文献原文已逐篇核对**（`D:/skill/paper/`），缩写与类别勘误见《PASD参考文献原文核对与勘误.md》。v1.0 中「未给完整出处、无法核对」的表述已作废。
- 但本规范给出的仍是**适配到 code-as-policy 平台后的机制等价代理**，不是原实现移植：未迁移 SSS 的 π0.5 VLA / UMI 示教、TGL 的 GPT-6 Astra 与 LIBERO 环境、SOAR 的机器人集群与 30.5K 轨迹、Uni-Skill 的 SkillFolder、ARMADA 的多机器人共享控制。所有表格须保留 `proxy` 标注。
- Voyager / Reflexion / OpenVLA / RT-2 原文未提供，仍为二手描述。
- VLA 端到端原生复现在本平台不可公平实现，是有效性威胁，必须写进论文。
- PASD 文档中 E3–E6 为「协议 + 预期」，本规范不预设任何成功率数值；所有基线结果待大模型与真机接入后填充。
- **专利风险提示**：SSS 与 TGL 均早于本方案构思时间，且已公开「失败检测 → 修复验证 → 经验入库/策略更新」与「Claude Code + 工具白名单 + 结构化经验记忆」组合；若拟据此申请专利，需先做权利要求比对，并把创新点收窄到簇身份去重、仿真定量晋升与生活辅助安全闸门。
