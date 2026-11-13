# deploy/ — Linux 部署包索引

完整说明见 `docs/08-Linux部署与迁移.md`。目标机器是 Linux；本机只用于打包，不安装、不启动任何服务。

| 文件 | 作用 |
|---|---|
| `bootstrap.sh` | 一键引导：检查 Python≥3.11、建 venv、生成 `.env`、可选装 extras、准备状态目录、跑全套自检。**默认零依赖、默认 `mock`** |
| `doctor.py` | 环境体检（零依赖）：locale/UTF-8、CRLF、可选模块、后端、CAN/串口、Claude Code CLI、密钥存在性；支持 `--json`、`--strict` |
| `make_dist.py` | 在打包端生成 `dist/*.tar.gz`：统一 LF/UTF-8、`.sh` 可执行位、排除密钥与运行产物 |
| `setup_can.sh` | SocketCAN 接口启用（需 root，`PASD_CAN_DRY_RUN=1` 可预演） |
| `udev/99-piper.rules.template` | udev 规则模板，VID/PID 需在目标机用 `lsusb` 实测后填写 |
| `Dockerfile` / `docker-compose.yml` | 离线可用的容器自检；`--profile real` 仅映射设备，不启用真机 |
| `systemd/pasd-contract-tests.service` | 可选 oneshot 单元，只跑离线契约测试，不自动启动真机 |

**安全默认**：`PASD_BACKEND=mock`、`PASD_ALLOW_REAL=0`、`PASD_ESTOP_ACK=0`。真机需要三重显式确认（见 `docs/08` 第 6 节），脚本不会替你打开。
