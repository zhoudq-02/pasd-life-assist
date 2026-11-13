# PASD-Life-Assist

**失败签名簇驱动的有界经验蒸馏：面向桌面助餐与取物的人机共域具身智能体**

一个「论文 + 可运行系统」双目标仓库。Claude Code 作为 code-as-policy 智能体驱动 AgileX PiPER 6-DoF 机械臂完成桌面助餐（A1）与取物（A2）；系统把一次失败蒸馏成 `⟨σ 失败签名, C 适用条件, π 修复策略, V 验证记录⟩` 四要素技能，经三闸门晋升后在下一会话注入规划器。

> **部署目标是一台新的 Linux 主机。** 本机（打包端）只负责生成压缩包与编辑文档；不在本机建 venv、装依赖、起服务或连硬件。完整迁移步骤见 **`docs/08-Linux部署与迁移.md`**。

## 快速开始（目标 Linux 机器）

```bash
# 打包端（任何 OS）：
python3 deploy/make_dist.py
scp dist/pasd-life-assist-linux-*.tar.gz dist/SHA256SUMS user@<linux-host>:~/

# Linux 主机：
sha256sum -c SHA256SUMS
tar -xzf pasd-life-assist-linux-*.tar.gz
cd pasd-life-assist
./deploy/bootstrap.sh          # 零依赖；默认后端 mock
python3 deploy/doctor.py
make check
claude                         # 自动读取 CLAUDE.md
```

要求 **Python ≥ 3.11**（Ubuntu 24.04 / Debian 12 满足；22.04 自带 3.10，需另装或用 `deploy/docker-compose.yml`）。`bootstrap.sh` 统一 `python3`、UTF-8 locale 与 `PYTHONPATH`，并跑完 doctor + 契约测试 + 冒烟闭环 + 16 条公平性审计 + 后端探针。

## 给 Claude Code 用（三步）

1. 在仓库根目录运行 `claude`（自动读取 `CLAUDE.md` 与 `@docs/00..08` imports）；
2. 把 `PROMPT.md` 里「提示词开始 / 结束」整段粘贴进去；
3. 它会先复述框架、盘点仓库、跑校验命令，然后**停下来等你确认**，再按 `docs/06` 顺序逐层补全。

只想审查代码时，直接说「用 pasd-framework 技能审查所有基线」。Linux 部署相关问题用「用 pasd-framework 技能做一次部署体检」。

## 仓库里的三种上下文形态

| 形态 | 文件 | 用途 |
|---|---|---|
| **根上下文** | `CLAUDE.md` | Claude Code 进入仓库自动读取；硬约束、口径裁决、目标运行环境、`@docs/` imports |
| **启动 Prompt** | `PROMPT.md` | 复制粘贴即可接续开发；含短版与四个专用提示词（C1 / C2 / 基线审查 / Linux 部署） |
| **Skill** | `.claude/skills/pasd-framework/SKILL.md` | 框架导航 / 新增基线 / 合规审查 / 论文写作 / **Linux 部署与真机接入** |

契约文档 `docs/00`–`docs/08`：`01` 代码级接口、`02` 任务与失败签名、`03` 基线分组与 16 条公平性、`04` SCI 创新点、`05` 术语勘误、`06` 目录契约、`07` 验收清单、`08` Linux 部署与迁移。上游依据已随仓库自带于 `docs/upstream/`（索引见其 README），**不依赖任何本机绝对路径**。

## 自检（零第三方依赖，离线可跑）

```bash
python3 deploy/doctor.py               # 环境体检：locale/CRLF/可选模块/后端/硬件
python3 deploy/doctor.py --json        # CI 可解析
python3 scripts/contract_tests.py      # 契约测试（标准库 unittest）
python3 scripts/run_smoke.py           # 失败→蒸馏→Gate2 晋升→下一回合成功
python3 scripts/fairness_audit.py      # 16 条公平性清单
python3 scripts/run_backend_probe.py   # 后端工厂 + 真机守卫（DRY-RUN，不动硬件）
python3 -m pytest -q                   # 可选：装了 pytest 时等价
make check                             # 一次跑完上面四项
```

冒烟闭环复刻 PASD 原始案例：顶抓细长杆（`aspect_ratio=5.3`）→ `GRASP_SLIP` → 蒸馏 `CANDIDATE` → Gate2 仿真 10 次达标 `VERIFIED` → 下一回合注入「侧夹」→ 成功。

## 三层依赖与后端矩阵

| 后端 | 依赖 | 状态 |
|---|---|---|
| `mock`（默认） | 仅标准库 | ✅ 可运行；新机器第一次自检一定用它 |
| `mujoco` | `pip install -e '.[sim]'` + MJCF 模型 + headless GL 库 | 🧩 适配器骨架；缺模型时**显式报错**，不伪造物理 |
| `real` | `pip install -e '.[robot]'` + SocketCAN + udev + 已核对的 SDK 适配器 | 🧩 骨架；需四重确认，见 `docs/08` 第 6 节 |

`PiperSDKAdapter` 有意不猜测 `piper_sdk` 的 API：没有真机就不能写出会驱动电机却未经验证的调用，它会在依赖存在时仍明确列出需现场核对的 6 项。

- **可选 Python 包**：MuJoCo、`piper_sdk`、`anthropic`、pytest/PyYAML/ruff；缺失时优雅降级。
- **配置优先级**：环境变量 > `.env` > `configs/default.yaml` > 内置默认（`src/pasd_life/settings.py`）。
- **阈值常量**集中在 `src/pasd_life/config.py`，禁止魔法数字。
- **状态目录**：`PASD_HOME`（默认 `${XDG_DATA_HOME:-~/.local/share}/pasd-life-assist`）下的 `logs/ runs/ artifacts/`，在仓库外，不入库。

## 安全默认

`PASD_BACKEND=mock`、`PASD_ALLOW_REAL=0`、`PASD_ESTOP_ACK=0`。任何脚本都不会自动启用真机；`GuardedBackend` 把速度限幅、工作空间盒、Watchdog 与急停外挂在控制层，不经过 LLM。真人实验前必须先用假人头部完成 E4 去 Gate3 消融。

## 上游依据（只读，已随仓库自带）

- `docs/upstream/research-proposal.md` — 系统研究方案底稿（资料库 `w90lFuGDObXwGlK7X5UoKO`）
- `docs/upstream/baseline-spec-v1.1.md` — 基线实现规范 v1.1
- `docs/upstream/sci-strategy.md` — SCI 创新点重构与投稿策略
- `docs/upstream/reference-corrections.md` — 9 篇 PASD 参考文献逐篇勘误
- 资料库 PASD 构想：`https://www.workbuddy.cn/space/d/5DyOfqSPUQhBWpQWSKjh2D`（在线文档，运行不依赖）

## 当前状态与边界

**可运行骨架**：核心链路、Linux 部署层、后端工厂与守卫已实现；MuJoCo 后端、真机 SDK 适配器、Claude Code 真实接入、E3–E7 完整实验为 `TODO(scaffold)`。

只有 E1（240→9 簇、纯度 1.0、去重率 96%）与 E2（FTR 15%–26%）是已复现数据；**E3–E7 均为协议与预期，仓库内不预填任何成功率**。结论基于所给 5 篇中文文献、9 篇原文与 4 件专利截图，未做外部专利库/文献库系统检索。详见 `docs/07`。
