# 启动 Prompt（复制给 Claude Code）

> 用法：在**目标 Linux 机器**的仓库根目录启动 Claude Code（`cd ~/pasd-life-assist && claude`），把下面「─── 提示词开始 ───」到「─── 提示词结束 ───」之间的内容整段粘贴进去。
> 若你用的是新会话且 Claude Code 没有自动加载 `CLAUDE.md`，在提示词最前面加一句：`请先完整读取 CLAUDE.md 与 docs/ 下全部 .md 文件（含 08-Linux部署与迁移.md），再执行以下任务。`
> 迁移与一键部署见 `docs/08`；本机（打包端）只做 `python3 deploy/make_dist.py`，不要在本机建 venv、装依赖或连硬件。

---

## ─── 提示词开始 ───

你正在 `pasd-life-assist` 仓库中工作，**目标环境是一台 Linux 主机（Python ≥ 3.11，一律用 `python3`）**。这是一个准备投 SCI 的具身智能体研究项目：Claude Code 作为 code-as-policy 智能体，驱动 AgileX PiPER 6-DoF 机械臂完成**桌面助餐（A1）**与**桌面取物（A2）**；核心机制是把失败 `Trace` 蒸馏为 `⟨σ, C, π, V⟩` 四要素技能，经 Gate1 簇身份去重 → Gate2 仿真定量验证 → Gate3 人机安全闸门晋升，下一会话由 `retrieve` 注入你的 prompt。`CLAUDE.md` 与 `docs/` 是唯一权威契约，冲突时以 `CLAUDE.md` 第 3 节的裁决为准。

**第一步（必做，不要跳过）**：完整读取 `CLAUDE.md`、`docs/00`–`docs/08`、`README.md`，然后输出一份不超过 30 行的「框架复述」，包含：四层架构、三闸门判据、三条 SCI 贡献及其耦合关系、主表 A 必须包含的基线、三条口径裁决、硬约束、`docs/08` 的 Linux 部署约束（默认 `mock`、三重真机确认、零依赖底线）。复述有误我会纠正，纠正后再动手写代码。

**第二步：盘点仓库**。运行 `python3 deploy/doctor.py`、`python3 scripts/contract_tests.py`、`python3 scripts/run_smoke.py`、`python3 scripts/fairness_audit.py`、`python3 scripts/run_backend_probe.py`（全部零依赖、无需联网、不动硬件；也可用 `make check`），列出当前哪些文件是 `✅` 可运行、哪些是 `🧩 TODO(scaffold)`，并指出契约文档与现有代码之间的任何不一致（尤其是签名、字段名、状态机命名、后端工厂）。**只报告，不要改代码。**

**第三步：按 `docs/06` 第 2 节的顺序补全仓库**。默认从「主表 A 补全」开始（`trajectory` / `episodic` / `pragmabot` / `tgl_skill`，TGL 优先）。每完成一层：
1. 跑 `python3 scripts/contract_tests.py` 与 `python3 scripts/fairness_audit.py`，把输出贴给我；
2. 在回复里说明改了哪些文件、为什么这么改、有没有偏离契约；
3. 停下来等我确认，再进入下一层。

**实现时的强制要求**：
- 不改 `docs/01` 定义的任何签名、字段名、调用顺序；只补内部实现。
- 所有阈值来自 `src/pasd_life/config.py`；所有路径用 `pathlib.Path` / `repo_root()` / `PASD_HOME`，禁止硬编码绝对路径。
- 新增基线必须同步 `integration/baselines/registry.py`、`configs/baselines.yaml`、`docs/06`，并补一条参数化测试。
- 基线一律实现 `MemoryPlugin`；`snapshot()` 六字段齐全；`verified_by` 按实际机制填，不许一律 `False`。
- `baselines/pasd.py` 保持原版双闸门与四类错误码，Gate3 只属于 `pasd_full.py`。
- `domain_rand.py` 只做离线仿真参数分布更新，禁止在线微调与推理指针切换。
- 不编造实验结果：E1/E2 是已复现数值，E3–E7 只能生成协议与 `--dry-run` 骨架。
- 所有跨范式基线保留 `proxy` 标记；论文措辞用「统一插件接口下的机制等价参照」。
- 术语以 `docs/05` 为准：PRAGMABOT、SOAR、Skill-Space Shooting、Teach-and-Grow (TGL)、NBCagent；禁止使用 PASD 构想文档里的错误缩写展开名。
- 涉及后端 / 依赖 / 路径 / 部署的改动，先读 `docs/08`；新增后端必须走 `make_backend()` 并由 `GuardedBackend` 包装，不得新增控制原语。
- 上游依据只读 `docs/upstream/`，不要引用 `D:/...` 或仓库父目录。

**不要做的事**：不要重写 `RobotAPI`、不要新建第二套指标代码、不要把 `DEPLOYED` 当状态、不要删除 `TODO(scaffold)` 注释前先补实现、不要为了"让测试变绿"而放宽白名单或防污染约束、**不要在本机启用 `real` 后端或凭猜测调用 `piper_sdk`**。

**最终交付**（当我说「完成仓库」时）：一个 `contract_tests.py` 全绿、冒烟闭环可跑、16 条公平性自检全 PASS、`doctor.py` 无 FAIL 的仓库，外加 `paper/outline.md` 与 `paper/claims.md` 的投稿骨架，以及一份「已实现 / 待实现 / 需要真机才能验证」的三栏清单。

## ─── 提示词结束 ───

---

## 附：短版提示词（只要快速接续开发时）

```
读取 CLAUDE.md 与 docs/ 全部文件（含 08-Linux部署与迁移.md），先用 20 行复述框架与硬约束；
然后运行 make check 与 python3 deploy/doctor.py，列出 TODO(scaffold) 清单。
按 docs/06 第 2 节顺序补全下一层，改完贴测试输出并停下等我确认。
不得修改 docs/01 的签名，不得编造 E3–E7 实验结果，不得放宽白名单与防污染约束。
```

## 附：四个专用提示词

**① 只做 C1 证据（性价比最高）**
```
按 docs/03 的 E2 协议实现 experiments/e2_library_convergence.py 与 |B_t| 曲线脚本，
对比 pasd_full / tgl_skill / 去 Gate1 / no_memory（SSS 原式属 C2，若要进主表须新建
sss_trainingfree_proxy 并标注「非原式、无梯度更新」），每方法 200 episode × 3 seeds，
指标全部走 integration/metrics.py。
同时在 paper/claims.md 写出「纯度为 1 时 |B_t| ≤ k」的形式化证明与松弛形式。
--dry-run 只打印协议，不产出数值。
```

**② 只做 C2 安全证据**
```
完善 src/pasd_life/safety.py 的 SafetyEnvelope 与 docs/02 三条安全类签名，
实现 experiments/e4_safety_ablation.py（去 Gate3 vs 完整系统，假人头部模型优先）。
验证：Gate2 达标但违反安全包络的修复仍为 REJECTED；INTENT_AMBIGUOUS 转人工不晋升。
```

**③ 只做基线审查**
```
调用 .claude/skills/pasd-framework 技能，审查 integration/baselines/ 下所有实现：
逐条核对 docs/03 的 16 条公平性清单、docs/01 的 MemoryPlugin 签名、docs/05 的术语，
输出违规清单与最小修复补丁，不要顺手重构无关代码。
```

**④ Linux 部署与真机接入（新机器专用）**
```
先读 docs/08 与 docs/01 第 9 节。运行 python3 deploy/doctor.py --json 与
python3 scripts/run_backend_probe.py，判断这台 Linux 主机能否跑通离线全链路，
把 WARN 逐条给出修复命令（不要自动 sudo、不要 pip install、不要改 .env）。
随后按 docs/08 第 6 节的 6 项清单，为 PiperSDKAdapter 生成一份「需要现场核对」的
核对表与最小适配改动建议；在拿到真机 SDK 手册之前，禁止写出会驱动电机的调用。
最后确认：未满足三重确认时 make_backend("real") 必须抛 RealHardwareGuardError。
```
