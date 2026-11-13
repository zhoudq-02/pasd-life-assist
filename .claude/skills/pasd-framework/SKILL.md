---
name: pasd-framework
description: PASD-Life-Assist 仓库的框架导航、合规审查与 Linux 部署技能。当需要理解本项目架构、新增或审查对比基线、生成实验表格、撰写论文创新点/相关工作、检查公平性清单与 FTO 边界，或在新 Linux 主机上部署、体检、接真机时使用。触发词：PASD、失败签名、三闸门、Gate1/Gate2/Gate3、基线、MemoryPlugin、S³R、有界蒸馏、生活辅助、助餐、取物、PiPER、Claude Code 策略、公平性审查、创新点划界、Linux 部署、bootstrap、doctor、后端工厂、SocketCAN、真机接入。
---

# PASD-Life-Assist 框架技能

## 何时用

- 接手本仓库、需要快速理解四层架构与三条 SCI 贡献；
- 新增/修改 `integration/baselines/*`，或审查现有基线是否公平；
- 生成实验表格、写相关工作/创新点/投稿策略；
- 检查实现是否越过 FTO、安全或科学诚实边界；
- **在新 Linux 主机上部署、跑环境体检、排查 `python3` / locale / CRLF / CAN / udev 问题、接入 PiPER 真机。**

目标环境是 Linux，命令一律 `python3`；本机只用于打包（`python3 deploy/make_dist.py`），不在本机安装依赖或启动服务。

## 第一步：加载契约（不可跳过）

按顺序读取：
1. `CLAUDE.md`（根上下文、硬约束、三条口径裁决、**第 7 节 Linux 部署硬约束**）
2. `docs/01-架构与接口契约.md`（代码签名 + **第 9 节后端工厂与 settings**）
3. `docs/03-实验设计与基线分组.md`（v1.1 分组 + 16 条公平性清单）
4. `docs/05-参考文献勘误与术语.md`（禁止使用的错误术语）
5. **部署/后端/路径类任务必读** `docs/08-Linux部署与迁移.md`
6. 按任务再读：`docs/02`（任务/签名）、`docs/04`（创新点）、`docs/06`（目录契约）、`docs/07`（验收清单）

回答框架性问题时，**先引用契约条目编号再给结论**；不要凭通用机器人知识猜测本项目的阈值与状态机。上游依据只读 `docs/upstream/`，不得引用任何 `D:/...` 路径。

## 工作流 A：新增或修改基线

1. 确认它属于哪张表：主表 A（免训练）/ 主表 B（消融）/ 副表 C1（免训练趋势）/ C2（需训练趋势）/ D（安全与迁移）。
2. 实现 `MemoryPlugin` 四方法，输出统一包装 `RepairHint(text, executable, verified, verified_by, source)`。
3. `verified_by` 按原文实际机制填：PASD `simulation`、TGL `admission_check`、SSS `vlm_judge`、ARMADA `human`、无验证 `none`。**不许一律 False**。
4. `snapshot()` 六字段：`library_size, verified, requires_training, human_budget, extra_demos, fm_calls`。
5. 同步三处：`registry.py`、`configs/baselines.yaml`、`docs/06` 文件表。
6. 跑 `python3 scripts/fairness_audit.py`，16 条全 PASS 才进实验队列。
7. 复述该基线与 PASD 的划界（参照 `docs/04` 第 4 节），并保留 `proxy` 标记。

## 工作流 B：合规审查

逐项检查，输出「通过 / 违规 + 文件:行号 + 最小修复」：

- [ ] 五原语白名单无越界；`get_observation()` 无仿真真值
- [ ] heldout 不写库；`retrieve` / `on_episode_end` 是唯一读写点
- [ ] `promote()` 是唯一状态写入口；状态为 `OBSERVED/CANDIDATE/VERIFIED/SAFE/REJECTED`
- [ ] 安全包络一票否决优先于 Gate2 成功率；`INTENT_AMBIGUOUS` 转人工
- [ ] `baselines/pasd.py` 无 Gate3；`pasd_full.py` 有三闸门
- [ ] Gate2 数值 10 次 / 0.80；Gate1 半径 0.45；Gate3 连续 ≥8 次
- [ ] 免训练 / 需训练分表，主表 A 含 `tgl_skill` 与 `pragmabot`
- [ ] 假晋升率对无晋升状态机的方法记 `N/A`
- [ ] 无硬编码成功率；E3–E7 标注「协议 + 预期」
- [ ] 术语无错误缩写展开名；无 `DEPLOYED` 参与逻辑
- [ ] `domain_rand.py` 无在线微调 / 推理指针切换
- [ ] 表格措辞为「机制等价参照」，无「复现了 TGL/SSS」
- [ ] **无硬编码绝对路径；无自动启用 `real` 后端；核心自检零第三方依赖**

## 工作流 C：写论文内容

- 主论点与三条贡献直接取 `docs/04` 第 1、2 节，**不要重新发明贡献**。
- 已作废的说法清单见 `docs/04` 第 3 节；出现即删除。
- 相关工作按 9 篇原文的实际机制分 5 组，分组与展开名以 `docs/05` 为准。
- 主结论只由主表 A/B 支撑；C1/C2 只报趋势。
- 必须正面引用并划界 TGL（arXiv:2608.17209）与 SSS（arXiv:2609.38178），并如实报告 SSS 修复成功率 0.70–0.77。
- 题目用 `docs/04` 第 5 节的投稿版，不要用《…系统研究》。

## 工作流 D：Linux 部署与真机接入

1. 先跑 `python3 deploy/doctor.py --json`，把 FAIL 与 WARN 分开；**只给修复命令，不自动 sudo / pip install / 改 `.env`**。
2. 跑 `python3 scripts/run_backend_probe.py`，确认：默认 `mock`、未确认时 `make_backend("real")` 抛 `RealHardwareGuardError`、干跑适配器不发硬件指令、速度被 `GuardedBackend` 限幅。
3. 常见故障按 `docs/08` 第 8 节速查：`python` 别名缺失、`LANG=C` 中文乱码、CRLF `bad interpreter`、22.04 的 Python 3.10、缺 `python3-venv`、`/dev/ttyUSB0` 权限、`can0` 未起。
4. 打包迁移用 `python3 deploy/make_dist.py` + `SHA256SUMS`；容器用 `deploy/docker-compose.yml`（`--profile real` **只映射设备，不启用真机**）。
5. 真机接入前必须过 `docs/08` 第 6 节：udev / SocketCAN 位率 / SDK 六项核对 / 摩擦与夹持力标定 / 假人头部 / 停机协议 / 三重确认。`PiperSDKAdapter` 与 `MuJoCoBackend` 是**显式失败的适配器骨架**，缺模型或未核对 SDK 时抛 `BackendUnavailable`；**禁止凭猜测写出会驱动真机的 API 调用**。
6. 新增或修改后端时：只走 `make_backend()` 工厂，保持 `step(name, **kwargs)` / `observation()` 协议，由 `GuardedBackend` 包装，绝不新增控制原语或第二套 `RobotAPI`。

## 三条口径裁决（遇到冲突直接采用）

1. 状态机统一 `OBSERVED → CANDIDATE → VERIFIED → SAFE`，`DEPLOYED` 仅历史别名。
2. SSS 原式（需训练）只在副表 C2；若要进主表 A 必须新建 `sss_trainingfree_proxy` 并标注「非原式、无梯度更新」。
3. 原版 PASD 双闸门 + 四类错误码；本系统三闸门 + 六类环节。两者是不同类，不可混用。

## 禁止事项

- 不要修改 `docs/01` 定义的签名、字段名、调用顺序。
- 不要放宽白名单、防污染或安全约束来让测试变绿。
- 不要把「预期趋势」写成实验结果，不要预填成功率。
- 不要写「双闸门独有」「复现了 TGL/SSS」「APR = Active Process Reward」等作废表述。
- 不要在 `domain_rand.py` 里加在线部署链（CN122735765A 边界）。
- 不要在本机安装依赖、建 venv、启动服务或连接硬件；不要写 `D:/...` 绝对路径。
- 不要自动把 `PASD_BACKEND` 设为 `real`，不要替用户填写 `PASD_ALLOW_REAL` / `PASD_ESTOP_ACK`。
- 不要顺手重构与本任务无关的代码。

## 结束前

运行 `python3 scripts/contract_tests.py`、`python3 scripts/fairness_audit.py`（部署类任务再加 `python3 deploy/doctor.py` 与 `python3 scripts/run_backend_probe.py`），把结果贴给用户，并列出改动文件与偏离契约之处（没有也要明说「无偏离」）。若环境已装 pytest，`python3 -m pytest -q` 等价。
