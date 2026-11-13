# CLAUDE.md — PASD-Life-Assist 仓库根上下文

> 本文件是 Claude Code 进入本仓库时自动读取的唯一权威上下文。所有实现、扩写、重构都必须遵守此处的**硬约束**与 `docs/` 下的契约。
> 若当前 Claude Code 版本不支持 `@` imports，请在开始工作前显式读取 `docs/` 下全部 `.md` 文件。
> **目标运行环境是一台全新的 Linux 主机**（见第 7 节）；本机只用于打包与编辑。

## 0　项目是什么（30 秒版）

一个**准备投 SCI 的具身智能体研究项目 + 可运行真机系统**：

- **论文题目（投稿版）**：《失败签名簇驱动的有界经验蒸馏：面向桌面助餐与取物的人机共域具身智能体》
  *Bounded, Verified, and Safe Experience Distillation for Human-in-the-Loop Assistive Embodied Agents*
- **实物**：AgileX PiPER 6-DoF 机械臂（+ 两指夹爪、RGB-D）、Claude Code 作为 code-as-policy 智能体、MuJoCo 仿真。
- **两个任务**：A1 桌面助餐、A2 桌面取物。能力已具备，本项目负责把它们做成可复现实验系统。
- **核心机制**：把一次失败 `Trace` 蒸馏成 `⟨σ 失败签名, C 适用条件, π 修复策略, V 验证记录⟩` 四要素技能，经 **Gate1 簇身份去重 → Gate2 仿真定量验证 → Gate3 人机安全闸门** 晋升，下一会话由 `retrieve_repair` 注入 Claude Code 的 prompt。
- **三条 SCI 贡献**：C1 有界经验蒸馏（簇身份、`|B_t| ≤ k` 上界）；C2 人身安全写进经验单元并作为晋升必要条件；C3 评测输出驱动离线仿真参数分布更新 + S³R 统一评测协议。

资料库论文正文（已同步勘误与 8.4 节）：`https://www.workbuddy.cn/space/d/w90lFuGDObXwGlK7X5UoKO`
上游依据（**只读，不要修改，已随仓库自带**）：`docs/upstream/baseline-spec-v1.1.md`（v1.1）、`docs/upstream/sci-strategy.md`、`docs/upstream/reference-corrections.md`、`docs/upstream/research-proposal.md`；索引见 `docs/upstream/README.md`。**仓库在任意 Linux 主机上自包含，不得引用打包端的 `D:/...` 绝对路径或父目录文件。**

## 1　必读契约（imports）

@docs/00-框架总览.md
@docs/01-架构与接口契约.md
@docs/02-任务与失败签名.md
@docs/03-实验设计与基线分组.md
@docs/04-创新点与SCI约束.md
@docs/05-参考文献勘误与术语.md
@docs/06-仓库目录契约.md
@docs/07-硬约束与验收清单.md
@docs/08-Linux部署与迁移.md

## 2　硬约束（违反即判为实现错误）

1. **白名单动作接口**：Claude Code 生成的 `run(robot)` 只允许调用 `RobotAPI` 五个原语
   `move_to_pose` / `open_gripper` / `close_gripper` / `get_observation` / `solve_ik`。
   禁止新增控制接口、禁止基线自带执行循环。所有参数用 SI 单位（夹爪开度用米）。
2. **防污染**：`get_observation()` 只返回真机同样可得的量（RGB、深度、分割、位姿、关节/夹爪状态、错误码），**禁止访问仿真真值**。开发集（`split="dev"`）失败才可写库；留出集（`split="heldout"`）只记录、不回写。
3. **基线统一适配**：所有对比方法实现 `MemoryPlugin`，只保留注入点
   `retrieve(ctx)` / `on_episode_end(trace)` / `on_step_end(feedback)`（默认 no-op）/ `snapshot()`。
   `snapshot()` 必须含 6 个字段：`library_size, verified, requires_training, human_budget, extra_demos, fm_calls`。
   PASD 的 Gate1/Gate2/Gate3/`retrieve_repair` **全部折叠进** `retrieve` 与 `on_episode_end`，不得另开后门。
4. **三闸门数值**：Gate1 身份键 `(stage, error_code, cluster_id)`、在线聚类半径 `0.45`；
   Gate2 仿真重复 `10` 次中成功 `≥8` 次（阈值 `0.80`）；
   Gate3 真机连续 `≥8` 次成功 + 首次人工确认 + 安全包络通过。
   **Gate2 达标但违反安全包络的修复一律不得进入 `SAFE`**；`INTENT_AMBIGUOUS` 强制反问澄清，禁止自动晋升。
5. **状态机命名统一**：`OBSERVED → CANDIDATE → VERIFIED → SAFE`，失败/空签名/仿真未达标/安全未通过转 `REJECTED`。
   旧文档里的 `DEPLOYED` 一律弃用（见第 3 节裁决）。
6. **原版 PASD ≠ 本系统**：`integration/baselines/pasd.py` 是**原版双闸门**（Gate1+Gate2、四类抓取错误码、无 Gate3）；
   `integration/baselines/pasd_full.py` 才是**本系统三闸门 + 任务级签名扩展**。两者不可混用。
7. **免训练 / 需训练必须分表**：`snapshot()["requires_training"]` 决定进主表 A / 副表 C1 还是副表 C2，两类**不做同一显著性检验**。主表 A 必须包含 `tgl_skill` 与 `pragmabot`（审稿人必问）。
8. **不得编造实验结果**：只有 E1（240→9 簇、纯度 1.0、去重率 96%）与 E2（FTR 15%–26%）是已复现数据；E3–E7 是协议与预期，代码里不得预填成功率或写死"预期值"。
9. **proxy 措辞**：所有跨范式基线是适配到 code-as-policy 平台的**机制等价代理**，不是原实现移植。代码注释、日志、表格生成器中一律保留 `proxy` 标记；论文措辞只能写"统一插件接口下的机制等价参照"，**不得写"复现了 Voyager / OpenVLA"**。
10. **专利边界**：离线随机化 `q_t(c) → p_t(θ)` 严格限定在**离线训练阶段**，排除 CN122735765A 的「偏差→增量数据→在线微调→推理指针切换」链。不要在 `domain_rand.py` 里加入在线部署/推理指针切换逻辑。
11. **安全外挂**：速度/加速度限幅、工作空间盒、力矩上限、急停与 Watchdog 必须在控制层外挂，不能依赖 LLM 生成代码自觉。**真人实验前先用假人头部模型**完成 Gate3 消融。
12. **术语**：禁止使用 PASD 构想文档里的错误缩写展开名（APR≠Active Process Reward、NEERL≠Navigation Error Recovery、SSS≠Self-Supervised Failure、TAG≠Task-Agnostic Grasping 等）。以 `docs/05` 为准。

## 3　已知口径冲突与裁决（重要，别再引入矛盾）

| # | 上游文件里的不一致 | **本仓库裁决（唯一口径）** |
|---|---|---|
| A | PASD 原文 `CANDIDATE→VERIFIED`；研究方案写 `CANDIDATE→VERIFIED→DEPLOYED`；SCI 策略写 `OBSERVED→CANDIDATE→VERIFIED→SAFE` | 统一为 `OBSERVED → CANDIDATE → VERIFIED → SAFE`，`REJECTED` 为终态；`DEPLOYED` 仅作为历史别名常量保留，不参与逻辑 |
| B | SCI 策略 E3 注写「主表 A 含 SSS 式的免训练等价实现」；v1.1 规范主表 A 不含 SSS，原式放 C2 | **以 v1.1 规范为准**：SSS 原式（需 DAgger 训练）只在副表 C2。若确需加入主表 A，必须新建 `sss_trainingfree_proxy` 并显式标注"非原式、无梯度更新"，不得与 `sss.py` 混名 |
| C | 原版 PASD 是「双闸门」，本系统是「三闸门」 | 见硬约束 6：两个类分别实现，`pasd.py` 不得出现 Gate3 |
| D | 环节数：PASD 原版四类（感知/规划/执行/验证），本系统六类 | 本系统增加 `交互(interaction)` 与 `安全(safety)`；原版 baseline 保持四类 |

## 4　技术栈与运行（Linux 口径）

- **Python ≥ 3.11，一律用 `python3`**（多数 Linux 发行版没有 `python` 别名）；仅标准库即可跑通 `MockPiPER` 冒烟闭环与全部自检。MuJoCo / `piper_sdk` / Claude API 均为**可选依赖**，缺失时必须优雅降级而不是崩溃。
- **目标环境**：Ubuntu 24.04 / Debian 12 / 22.04 + Python 3.11，UTF-8 locale（`LANG=C.UTF-8`、`PYTHONUTF8=1`），LF 换行。新机器先 `./deploy/bootstrap.sh`，再 `python3 deploy/doctor.py`。
- **配置优先级**：环境变量 > `.env` > `configs/default.yaml` > 内置默认，统一由 `src/pasd_life/settings.py` 解析；阈值常量集中在 `src/pasd_life/config.py`，**禁止在业务代码里写魔法数字或绝对路径**。
- **后端唯一入口** `make_backend()`（`src/pasd_life/backends/`，契约见 `docs/01` 第 9 节）；`RobotAPI` 签名与五原语白名单不得改动。
- 常用命令：
  ```bash
  python3 deploy/doctor.py                  # 环境体检（零依赖）
  python3 scripts/contract_tests.py         # 契约测试（零依赖，必须全绿）
  python3 scripts/run_smoke.py              # 失败→蒸馏→晋升→下一回合成功
  python3 scripts/fairness_audit.py         # 16 条公平性清单自检
  python3 scripts/run_backend_probe.py      # 后端工厂 + 真机守卫（DRY-RUN）
  python3 experiments/e2_library_convergence.py --dry-run
  make check                                # 一次跑完四项自检
  python3 -m pytest -q                      # 可选：已装 pytest 时等价
  ```
- 代码风格：类型注解完整、dataclass 优先、每个模块顶部注明它对应的 `docs/` 契约条目；`TODO(scaffold)` 表示待实现，**不得删除契约中已定义的签名**。

## 5　工作方式要求

- 修改任何 `integration/baselines/*` 之前，先读 `docs/03` 第 2 节的 16 条公平性清单。
- 新增基线必须同时更新 `integration/baselines/registry.py` 与 `configs/baselines.yaml`，并在 `docs/06` 的文件表里登记。
- 生成论文表格时用 `experiments/tables.py`，主结论只由主表 A/B 支撑；C1/C2 只报趋势。
- 涉及部署、后端、依赖、路径的改动，先读 `docs/08`，并跑 `python3 deploy/doctor.py` 与 `python3 scripts/run_backend_probe.py`。
- 遇到上游文档与本文件冲突，**以本文件的裁决为准**，并在回复中明确指出冲突点，不要静默二选一。

## 6　当前状态

仓库是**可运行骨架（scaffold）**：核心链路（schema / RobotAPI-Mock / Executor / Extractor / Clusterer / SkillLibrary / Gate1-3 / Runner / Metrics / 部分基线）、Linux 部署层（settings / backends / guard / doctor / bootstrap / 容器 / 打包）已实现；MuJoCo 后端、真机 SDK 适配器、Claude Code 真实接入、E3–E7 完整实验为 `TODO(scaffold)`。
请按 `docs/06` 的生成顺序补全，每完成一层先跑 `python3 scripts/contract_tests.py` 与 `python3 scripts/fairness_audit.py`。

## 7　目标运行环境（Linux）— 部署侧硬约束

1. **默认后端恒为 `mock`**。任何脚本、配置模板、容器 profile 都不得自动把 `PASD_BACKEND` 置为 `real`；真机需要 `PASD_ALLOW_REAL=1` + `PASD_ESTOP_ACK=1` + CLI `confirm_real=True` 三重显式确认（见 `docs/08` 第 6 节）。
2. **不写绝对路径**：所有路径走 `pathlib.Path` / `repo_root()` / `PASD_HOME`；禁止 `D:/`、`C:/`、`/home/<某人>/` 之类硬编码。状态目录默认在 `${XDG_DATA_HOME:-~/.local/share}/pasd-life-assist`，位于仓库外。
3. **密钥与运行产物不入库**：`.env`、`ANTHROPIC_API_KEY`、经验库运行文件、真机日志一律排除（`deploy/make_dist.py` 会二次过滤）；`doctor.py` 只报告密钥**是否存在**，绝不打印值。
4. **零依赖底线**：核心自检、冒烟闭环、公平性审计、后端探针必须仅用标准库跑通；新增第三方依赖只能进 `pyproject.toml` 的 optional extras，且缺失时要优雅降级。
5. **不假装硬件可用**：`PiperSDKAdapter` 与 `MuJoCoBackend` 是显式失败的适配器骨架，缺模型/未核对 SDK 时抛 `BackendUnavailable` 并列核对清单；**禁止凭猜测写出会驱动真机的 API 调用**。
6. **急停不经过 LLM**：`GuardedBackend` 负责速度限幅、工作空间盒、Watchdog 与 `estop()`；新增后端必须经它包装（离线 `mock` 可例外），且不得新增控制原语。
