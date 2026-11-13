# 08　Linux 部署与迁移指南

> **目标环境**：一台全新的 Linux 主机（Ubuntu 24.04 / Debian 12 / Ubuntu 22.04 + Python 3.11，x86_64 或 aarch64）。
> **本机（打包端）只做两件事**：生成压缩包、编辑文档。**不安装依赖、不创建虚拟环境、不启动服务、不连接硬件**。
> 本文是 `docs/01` 第 9 节（后端工厂）与 `docs/07` 第 4 节 E 段（部署验收）的操作版。

---

## 1　三条落地路径

| 路径 | 适用 | 需要联网 | 需要硬件 | 完成标志 |
|---|---|---|---|---|
| **A. 裸机离线自检**（推荐先做） | 验证迁移是否成功 | 否 | 否 | `make check` 全绿、`doctor.py` 无 FAIL |
| **B. 容器** | 不想污染系统 Python，或 22.04 默认 Python 3.10 | 拉基础镜像一次 | 否 | `docker compose run --rm pasd python3 scripts/run_smoke.py` |
| **C. 真机实验** | PiPER 已装好、急停已接线、标定完成 | 装 SDK 时需要 | **是** | Gate3 消融在假人头部上完成 |

**默认后端永远是 `mock`**。路径 C 不会因配置文件、环境变量或容器 profile 被自动打开，需要四重条件同时成立（见第 6 节）。

---

## 2　从打包端到 Linux（一次性）

### 2.1 打包端（当前 Windows 机器也可）

```bash
cd pasd-life-assist
python3 deploy/make_dist.py
# 产出：
#   dist/pasd-life-assist-linux-YYYYMMDD.tar.gz
#   dist/SHA256SUMS
#   dist/MANIFEST.txt
```

`make_dist.py` 会做四件在 Linux 上很关键的事：所有文本文件统一 **LF + UTF-8**、`.sh` 设为 `0755`、归档内路径统一为 `pasd-life-assist/`、排除 `.env`/密钥/venv/日志/经验库运行产物。压缩包内自带 `INSTALL-LINUX.txt`。

### 2.2 传输

```bash
scp dist/pasd-life-assist-linux-*.tar.gz dist/SHA256SUMS user@<linux-host>:~/
# 或：rsync -avz dist/ user@<linux-host>:~/pasd-dist/
```

### 2.3 目标机解包与校验

```bash
cd ~
sha256sum -c SHA256SUMS
tar -xzf pasd-life-assist-linux-*.tar.gz
cd pasd-life-assist
ls -l deploy/*.sh          # 应显示 -rwxr-xr-x；若文件系统丢了执行位：chmod +x deploy/*.sh
```

> 不要只 `cp -r` 源码目录：CRLF 与残留 `__pycache__` 会让 `#!/usr/bin/env bash` 报 `bad interpreter`，`doctor.py` 会明确报出 CRLF 文件。

---

## 3　新机器最小准备与一键引导

```bash
# Ubuntu 24.04 / Debian 12：系统 Python 已 >= 3.11
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl iproute2 can-utils

# 可选：Claude Code CLI 需要 Node.js >= 18（以 Anthropic 官方文档为准）
# curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
# sudo apt install -y nodejs && sudo npm i -g @anthropic-ai/claude-code
```

> **Ubuntu 22.04 默认是 Python 3.10**，低于本仓库 `requires-python>=3.11`。两条路：另装 3.11+（deadsnakes PPA / pyenv），或直接走第 4 节容器路径。`bootstrap.sh` 会在第一步明确报错，不会降级运行。

```bash
./deploy/bootstrap.sh                 # 零依赖：建 .venv、生成 .env、准备状态目录、跑全套自检
./deploy/bootstrap.sh --offline       # 完全断网也可
./deploy/bootstrap.sh --extras dev    # 需要 pytest / pyyaml / ruff 时
./deploy/bootstrap.sh --extras sim,robot   # MuJoCo + PiPER SDK（需联网）
./deploy/bootstrap.sh --no-venv       # 用系统 python3，不建 .venv
```

`bootstrap.sh` 实际执行：`deploy/doctor.py` → `scripts/contract_tests.py` → `scripts/run_smoke.py` → `scripts/fairness_audit.py` → `scripts/run_backend_probe.py`。全部零第三方依赖；`--extras` 是唯一会触发 `pip` 的分支。

体检单独跑：

```bash
python3 deploy/doctor.py             # 人读，PASS/WARN/FAIL/INFO
python3 deploy/doctor.py --json      # CI 可解析
python3 deploy/doctor.py --strict    # WARN 也返回非零，适合 CI 门禁
```

体检覆盖：Python 版本、是否 Linux、UTF-8 locale、必需文件、CRLF、`.env`、状态目录可写、8 个可选模块、后端与真机守卫、SocketCAN 接口、串口设备、Claude Code CLI、API 密钥**是否存在**（绝不打印值）。

---

## 4　路径 B：容器

```bash
cd pasd-life-assist
docker compose --profile default up --build       # 默认只跑 contract_tests.py
docker compose run --rm pasd python3 scripts/run_smoke.py
docker compose run --rm pasd python3 deploy/doctor.py
docker build --build-arg EXTRAS=dev -t pasd-life-assist:dev -f deploy/Dockerfile .
```

- 镜像基于 `python:3.11-slim`，只设 `PYTHONPATH`，**默认不 pip install 任何包**，因此离线构建也能跑核心自检。
- `Dockerfile` 预置 `libgl1 / libosmesa6 / libglib2.0-0`，为 MuJoCo headless（设 `MUJOCO_GL=osmesa` 或 `egl`）准备。
- 运行用户是 `1000:1000`，状态目录 `/state` 挂回宿主机 `runs/ logs/ artifacts/`。
- `docker compose --profile real up` **只映射设备并开 host 网络**，`PASD_BACKEND` 仍是 `mock`；把设备映射等同于"启用真机"是错误理解。
- 若 `/dev/ttyUSB0` 不存在，compose 会报错：用 `PASD_SERIAL_DEVICE=/dev/ttyACM0 docker compose ...` 覆盖。

---

## 5　运行时配置与目录

优先级：**shell 环境变量 > `.env` > `configs/default.yaml` > 内置默认**（`src/pasd_life/settings.py`）。`.env` 由 `bootstrap.sh` 从 `.env.example` 生成，且被 `.gitignore` 排除。

| 变量 | 默认 | 说明 |
|---|---|---|
| `PASD_BACKEND` | `mock` | `mock` / `mujoco` / `real` |
| `PASD_SPLIT` | `dev` | `heldout` 只记录、不写经验库 |
| `PASD_SEED` | `0` | 与 `configs/seeds.yaml` 对齐 |
| `PASD_HOME` | `${XDG_DATA_HOME:-~/.local/share}/pasd-life-assist` | 状态根，下设 `logs/ runs/ artifacts/` |
| `PASD_ADAPTER` | `sdk` | `sdk`（真实 SDK，未核对）/ `null`（干跑，不动硬件） |
| `PASD_CAN_INTERFACE` / `PASD_CAN_BITRATE` | `can0` / `1000000` | 位率**必须**对照 AgileX 手册核对 |
| `PASD_SERIAL_DEVICE` | `/dev/ttyUSB0` | USB2CAN / 串口节点 |
| `PASD_ALLOW_REAL` / `PASD_ESTOP_ACK` | `0` / `0` | 真机确认位，默认关闭 |
| `ANTHROPIC_API_KEY` | 未设 | 仅 `ClaudeCodePolicyGenerator` 需要；不入库、不打印 |

`LANG=C.UTF-8 / LC_ALL=C.UTF-8 / PYTHONUTF8=1` 由 `bootstrap.sh`、Dockerfile 与 `.env.example` 三处兜底。新机器若是 `LANG=C`，中文文档名与日志会乱码——这是迁移后最常见的第一个坑。

后端工厂是唯一入口（`docs/01` 第 9 节）：

```python
from src.pasd_life.backends import make_backend
from src.pasd_life.robot_api import RobotAPI
api = RobotAPI(make_backend())        # 不传参即读 settings；新机器上一定是 mock
```

`settings.py` / `backends/` **不修改** `RobotAPI` 的任何签名，也不新增控制原语；`GuardedBackend` 只是控制层外挂（速度限幅、工作空间盒、Watchdog、急停），符合 `docs/07` 第 3 节。

---

## 6　路径 C：PiPER 真机接入（逐项核对，不可跳步）

### 6.1 硬件与权限

```bash
lsusb                                   # 记录 VID:PID
# 按 deploy/udev/99-piper.rules.template 填好，安装到 /etc/udev/rules.d/99-piper.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG dialout "$USER"        # 重新登录后生效
sudo PASD_CAN_INTERFACE=can0 ./deploy/setup_can.sh
PASD_CAN_DRY_RUN=1 sudo -E ./deploy/setup_can.sh    # 只打印将要执行的动作
ip -details link show can0
```

CAN 位率、适配器驱动（`gs_usb` / `candleLight` 等）依现场硬件而定，仓库里的 `1000000` 只是占位默认值。**不要在未确认的情况下把 `setup_can.sh` 接进开机自启**。

### 6.2 SDK 适配器：必须现场核对的 6 件事

`src/pasd_life/backends/piper.py` 的 `PiperSDKAdapter` 是**有意保留的骨架**：仓库没有真机，不能凭猜测写出会驱动电机的 API 调用，因此 `connect()` 在依赖存在时也会明确抛 `BackendUnavailable` 并列出核对清单，而不是假装可用。接入前对照 AgileX `piper_sdk` 手册确认：

1. 接口类名与连接/使能方法；
2. 关节/位姿单位（m 还是 mm，rad 还是 deg）——`RobotAPI`  contract 是 **SI**；
3. 夹爪开度到 SDK 参数的换算（0–70 mm，见 `configs/calibration.yaml`）；
4. 状态反馈字段与错误码映射（`REAL_OBSERVABLE_FIELDS`）；
5. 使能 / 失能 / **急停**调用（急停不得经过 LLM）；
6. 控制频率与超时，用于 `GuardConfig.step_timeout_s`。

改完后再做摩擦与夹持力标定（`scripts/calibrate_friction.py`，逐步降低夹持力直到滑落）与 `SRCC` 监测，详见 `docs/07` 第 5 节。

### 6.3 三重显式确认

`make_backend("real", confirm_real=True)` 要求**同时**满足：

| 条件 | 来源 |
|---|---|
| `PASD_BACKEND=real` | 环境变量 / `.env` |
| `PASD_ALLOW_REAL=1` | 环境变量 / `.env` |
| `PASD_ESTOP_ACK=1` | 环境变量 / `.env`（物理急停已接线并测试） |
| `confirm_real=True` | **CLI 显式标志**，代码里写死不算 |

缺任何一条都抛 `RealHardwareGuardError`。容器 profile、`.env.example`、`bootstrap.sh` 都不会自动置位。此外还须：**假人头部模型先完成 E4 去 Gate3 消融**、工作空间盒已标定、最小人机距离阈值有来源、用户同意与停机协议齐备。

### 6.4 迁移后第一次真机前，先跑干跑

```bash
PASD_BACKEND=real PASD_ADAPTER=null PASD_ALLOW_REAL=1 PASD_ESTOP_ACK=1 \
  python3 scripts/run_backend_probe.py
```

该命令走完整条工厂 → 守卫 → 五原语链路，但 `NullAdapter` 不发任何 CAN 帧、不产生任何关节运动，输出明确标记 `DRY-RUN`。`scripts/run_suite.py` 仍是 `TODO(scaffold)`，请勿把不存在的 `--confirm-real-hardware` 参数当成现成入口。

---

## 7　在 Linux 上让 Claude Code 接续开发

```bash
cd ~/pasd-life-assist
claude                  # 自动读取 CLAUDE.md 与 @docs/00..08 imports
```

然后粘贴 `PROMPT.md`「提示词开始/结束」整段。若新会话未自动加载上下文，在提示词最前加：

```
请先完整读取 CLAUDE.md 与 docs/ 下全部 .md 文件（含 08-Linux部署与迁移.md），再执行以下任务。
```

要点：
- 所有命令在 Linux 用 `python3`（很多发行版没有 `python` 别名）；`Makefile` 与 `bootstrap.sh` 已统一。
- 上游依据不再指向 Windows 父目录，改读 `docs/upstream/`（`upstream/README.md` 有映射表）。
- `.claude/skills/pasd-framework/SKILL.md` 新增「工作流 D：Linux 部署与真机接入」，会强制先跑 `doctor.py`。
- 可选 MCP 服务 `integration/mcp/pasd_mcp_server.py` 仍是桩；启用前先确认 Claude Code 的 MCP 配置格式，不要臆造参数。

---

## 8　故障排查速查

| 现象 | 原因 | 处理 |
|---|---|---|
| `bad interpreter: /usr/bin/env bash^M` | 解压了 CRLF 文件 | 重新用 `make_dist.py` 打包；或 `sed -i 's/\r$//' deploy/*.sh` |
| `python: command not found` | Linux 无 `python` 别名 | 一律用 `python3` / `make check` |
| `ERROR: Python >= 3.11 required` | Ubuntu 22.04 自带 3.10 | 装 3.11+ 或走第 4 节容器 |
| `venv creation failed` | 缺 `python3-venv` | `sudo apt install python3-venv` 或 `--no-venv` |
| 中文日志/文件名乱码 | `LANG=C` | `export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUTF8=1` |
| `ModuleNotFoundError: No module named 'src'` | 未设 `PYTHONPATH` | 用 `bootstrap.sh` 或 `make check`；或 `export PYTHONPATH=$PWD/src:$PWD:$PWD/integration` |
| `Permission denied: /dev/ttyUSB0` | udev/用户组 | udev 规则 + `dialout` 组 + 重新登录；不要长期 `chmod 666` |
| `can0: absent` | CAN 未起/驱动未加载 | `sudo ./deploy/setup_can.sh`、`ip -details link show` |
| MuJoCo 导入/渲染失败 | 缺系统 GL 库 | 装 `libgl1 libosmesa6 libglib2.0-0`，设 `MUJOCO_GL=osmesa` |
| `BackendUnavailable: MuJoCo model not found` | 未提供 `configs/mujoco/piper.xml` | 预期行为；Gate2 仿真须先补 MJCF 与标定 |
| pip 装不上（离线机器） | 无网络 | 核心自检零依赖；用 `--offline`，或先在有网机器做 wheelhouse |
| `doctor.py` 一堆 WARN | 可选模块/CLI 未装 | 不是错误；`--strict` 仅用于 CI 门禁 |

---

## 9　安全红线（与 `docs/07` 一致）

1. 默认 `mock`；任何脚本都不自动切换 `real`。
2. 急停与 Watchdog 在控制层外挂，不经过 LLM；`GuardedBackend` 与 `SafetyEnvelope` 是唯二闸门。
3. 真人实验前先用假人头部完成 E4；`INTENT_AMBIGUOUS` 强制澄清、不自动晋升。
4. `.env`、`ANTHROPIC_API_KEY`、经验库运行文件、真机日志一律不入库；`make_dist.py` 会再次排除。
5. `split=heldout` 绝不写库；防污染字段过滤在 `GuardedBackend.observation()` 里又加了一层。
6. 离线随机化只做 `q_t(c) → p_t(θ)`，不含在线微调 / 推理指针切换（CN122735765A 边界）。

---

## 10　部署验收清单（对应 `docs/07` 第 4 节 E 段）

- [ ] `sha256sum -c SHA256SUMS` 通过，解压后 `deploy/*.sh` 可执行
- [ ] `python3 deploy/doctor.py` 无 FAIL；`LANG` 含 UTF-8；无 CRLF
- [ ] `make check`（契约测试 / 冒烟闭环 / 16 条公平性 / 后端探针）全绿
- [ ] `scripts/run_backend_probe.py` 打印 `PROBE OK`，且 `DRY-RUN` 分支不发硬件指令
- [ ] 未显式确认时 `make_backend("real")` 抛 `RealHardwareGuardError`
- [ ] `.env` 未入库、`ANTHROPIC_API_KEY` 未出现在任何日志或 `MANIFEST.txt`
- [ ] 真机前：udev / CAN / SDK 六项核对 / 摩擦标定 / 假人头部 / 停机协议 全部完成
- [ ] Claude Code 能读到 `CLAUDE.md` + `docs/00..08` + `docs/upstream/`，无需任何本机绝对路径

---

## 11　打包端 vs 目标机的职责边界

| | 打包端（本机 Windows） | 目标机（新 Linux） |
|---|---|---|
| 允许 | 编辑文档、`python3 deploy/make_dist.py`、`bash -n` 语法检查、`compileall` 静态检查 | 全部运行、venv、可选 pip、实验、真机、Claude Code |
| 禁止 | 建 venv、装依赖、启动服务、连硬件、把本机路径写进仓库 | 把 `.env` 提交、跳过三重确认、真人先于假人 |
| 交付 | `dist/*.tar.gz` + `SHA256SUMS` + `MANIFEST.txt` | `doctor.py` 报告 + `make check` 输出 |
