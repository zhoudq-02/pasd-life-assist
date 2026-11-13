# upstream/ — 随仓库自带的上游依据（只读）

这些文件原本位于打包端（Windows）工作区父目录与临时目录。为使仓库在**新 Linux 机器上自包含**，已复制到此处并改用 ASCII 文件名。Claude Code 与论文写作直接引用本目录，**不要再引用任何 `D:/...` 或父目录路径**。

| 文件 | 原文件 | 用途 |
|---|---|---|
| `research-proposal.md` | 《面向生活辅助的具身智能体系统研究》报告底稿 | 系统方案 10 章；资料库版本 `https://www.workbuddy.cn/space/d/w90lFuGDObXwGlK7X5UoKO` |
| `baseline-spec-v1.1.md` | `实验对比基线实现规范.md` | 统一 `MemoryPlugin` 适配层、主表 A / 副表 C1、C2 分组、16 条公平性清单 |
| `sci-strategy.md` | `SCI创新点重构与投稿策略.md` | C1 有界蒸馏 / C2 安全晋升 / C3 闭环迁移、E1–E7、期刊与审稿质疑 |
| `reference-corrections.md` | `PASD参考文献原文核对与勘误.md` | 9 篇 PASD 参考文献逐篇勘误、规范引用条目、术语禁令 |

资料库中的 PASD 构想原文：`https://www.workbuddy.cn/space/d/5DyOfqSPUQhBWpQWSKjh2D`（在线文档，本仓库不依赖它即可运行）。9 篇原文 PDF 未随仓库分发；`reference-corrections.md` 已包含核对结论与规范引用条目，离线写作足够。

文中出现的 `D:/skill/paper/` 等路径是**核对发生地的历史记录**，不是运行依赖；Linux 目标机上没有该目录也不影响任何功能。请勿在代码、配置或新文档中再写入本机绝对路径。

**只读约定**：本目录是依据材料，不是代码契约。冲突时以 `CLAUDE.md` 第 3 节裁决与 `docs/01`–`docs/08` 为准。
