# 设计稿：.env 解析修复 + ClaudeCodePolicyGenerator 实现

日期：2026-11-13
状态：待确认

## 意图与背景

- 任务 1：修复 `.env.example` 行尾注释导致 `load_settings()` 抛 `ValueError` 的 bug。
  根因：`settings.py::_load_dotenv` 只做 `KEY=VALUE` 切分、不剥 `#` 注释，于是
  `PASD_BACKEND=mock  # mock | mujoco | real` 被整体当成值。
- 任务 2：实现 `ClaudeCodePolicyGenerator`（当前两个桩 `generate` / `propose` 均为
  `NotImplementedError`）。

## 目标

- `cp .env.example .env` 后 `load_settings()` 正常解析，`doctor.py` 0 FAIL。
- `ClaudeCodePolicyGenerator.generate()` 用 `anthropic` SDK 产出通过 `Executor._compile`
  白名单校验的策略源码；`propose()` 产出 `fixes == trace.error_code` 的修复计划。
- 不破坏 docs/01 任何签名、公平性清单、安全约束。

## 非目标 / 反目标

- 不改 `RobotAPI` 五原语、不改 `MemoryPlugin`、不改状态机。
- 不引入在线学习 / 梯度更新；不碰 MuJoCo / 真机后端。
- 不把「预期结果」写成实验结果（E3–E7 仍是协议）。

## 后端现实（重要）

- 本机环境变量把 `anthropic` SDK 指向了 **DeepSeek 的 Anthropic 兼容端点**：
  `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`、`ANTHROPIC_AUTH_TOKEN=sk-3260…`、
  `ANTHROPIC_MODEL=deepseek-v4-pro[1M]`。
- 因此 `ClaudeCodePolicyGenerator` 用 `anthropic` SDK 调用时，**实际模型是 DeepSeek
  `deepseek-v4-pro[1M]`**，不是 Claude。`claude-*` 模型名会被透传/忽略，响应里的
  `ThinkingBlock` 是 DeepSeek 的推理内容。
- `agent` extra（`anthropic>=0.40`）保持不变，无需换 `openai`/`deepseek` 客户端。
- **给用户留意的口径问题（非代码）**：论文「Claude Code as code-as-policy」的表述与实际
  DeepSeek 后端存在出入，属于科学诚实性边界，由用户决定如何表述（不在本任务范围）。

## 约束（来自契约）

- 策略源码只允许 `robot.<五原语>()`，禁 import/global（`Executor._compile` 已强制）。
- 公平性 #2/#6：`temperature` / `max_tokens` 固定常量，同一生成器配置跨基线复用。
- 模型默认 `deepseek-v4-pro[1M]`，优先级：`PASD_LLM_MODEL` > `ANTHROPIC_MODEL` 环境变量 >
  常量。可被覆盖。
- 客户端用 `anthropic.Anthropic()`（无参），从环境读取 `base_url` + auth（本机即 DeepSeek 端点）；
  `client` 参数保留用于测试注入 mock。
- 代理：运行时需绕过 `ALL_PROXY=socks://`（或装 `socksio`），否则 `httpx` 崩溃。

## 方案（已拍板）

- 任务 1：**修解析器剥注释** —— `_load_dotenv` 剥行尾 `#` 注释。
- 任务 2 返回契约：**返回 dict + Executor 桥接** —— LLM 返回
  `{"steps": N, "state": {...}}`，`Executor.run` 加 dict→`Observation` 归一化。

## 具体改动

1. `src/pasd_life/settings.py::_load_dotenv`：对 `value` 剥行尾 `#` 注释
   （`value.split("#", 1)[0].rstrip()`），并补契约测试。
2. `src/pasd_life/executor.py::run`：`obs = fn(self.api)` 后，若 `isinstance(obs, dict)`，
   归一化为 `Observation(state=obs.get("state", {}), steps=obs.get("steps", 0),
   success=obs.get("success", True))`。向后兼容现有 callable 路径，不改签名。
3. `src/pasd_life/policy_gen.py::ClaudeCodePolicyGenerator`：
   - `__init__(client=None, model=None, max_tokens=..., temperature=...)`；
     `client` 为 None 时懒创建 `anthropic.Anthropic()`（无参，从环境读 `base_url` + auth，
     本机即 DeepSeek 端点）；`model` 为 None 时按 `PASD_LLM_MODEL > ANTHROPIC_MODEL > 常量` 解析。
   - 固定 system prompt 模板：五原语 + SI 单位 + 任务/场景/hints + 输出契约
     （只输出 `def run(robot): ...` 并返回 dict，不 import、不调用其他函数）。
   - `generate()`：`messages.create` → 从响应提取代码：跳过 `thinking`/`reasoning` 块，
     只取 `text` 块并去 markdown fence → 返回源码字符串。
   - `propose()`：`messages.create` → 解析 JSON repair_plan → 校验
     `fixes == trace.error_code` → 返回 dict，否则 None。
4. `src/pasd_life/config.py`：加 `LLM_TEMPERATURE`、`LLM_MAX_TOKENS`、`LLM_MODEL_DEFAULT`
   常量。
5. 测试：`tests/` 加参数化用例（generate 返回可编译源码、propose 校验 fixes、dict 归一化）。

## 留给实现者的决定

- system prompt 的具体措辞与 few-shot 示例。
- 默认模型常量确认为 `deepseek-v4-pro[1M]`（可被 `PASD_LLM_MODEL`/`ANTHROPIC_MODEL` 覆盖）。
- DeepSeek 推理（thinking）块的提取策略：跳过推理、只取 text 块；若某模型不返回 text 块，
  报清晰错误而非静默返回空源码。
