# .env 修复 + ClaudeCodePolicyGenerator 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `.env` 行尾注释解析 bug，并实现 `ClaudeCodePolicyGenerator`（`generate`/`propose`）使 code-as-policy 链路可用。

**Architecture:** 两个独立改动 + 一个生成器实现。(1) `_load_dotenv` 剥行尾 `#` 注释；(2) `Executor.run` 把 dict 返回值归一化为 `Observation`；(3) `ClaudeCodePolicyGenerator` 用 `anthropic` SDK（本机经 `ANTHROPIC_BASE_URL` 指向 DeepSeek）产出策略源码与修复计划。

**Tech Stack:** Python 3.11+（`python3`）、标准库 `unittest`、`anthropic>=0.40`（`[agent]` extra，已装）、现有 `src/pasd_life` 契约。

**Spec:** `docs/superpowers/specs/2026-11-13-env-fix-and-policy-generator-design.md`

## Global Constraints

- Python ≥ 3.11，一律 `python3`；核心自检零第三方依赖（`anthropic` 属 `[agent]` extra，缺失须优雅降级）。
- 不改 `docs/01` 定义的任何签名、字段名、调用顺序；`RobotAPI` 五原语白名单不变。
- 策略源码只允许 `robot.<五原语>()`，禁 import/global（`Executor._compile` 强制）。
- 公平性 #2/#6：`temperature`/`max_tokens` 固定常量，跨基线复用。
- 模型默认 `deepseek-v4-pro[1M]`，优先级 `PASD_LLM_MODEL` > `ANTHROPIC_MODEL` 环境变量 > 常量。
- 所有路径 `pathlib`/`repo_root()`，禁绝对路径；LF + UTF-8。

## Review Focus

以下输入/失败模式最可能在真机上咬人，逐条配了测试（见对应任务）：

1. **dict 返回值缺字段**（如只有 `state` 没 `steps`）→ 默认 `steps=0`、`state={}`，不抛异常。→ Task 2
2. **generate 只有 thinking 块、无 text 块**（DeepSeek 推理可能吃满 max_tokens）→ 抛清晰错误，不静默返回空源码。→ Task 3
3. **propose 的 JSON 缺 `fixes` 字段或 `fixes` 类型不对** → 返回 None，不进入 Gate2。→ Task 4
4. **generate 返回无 markdown fence 的裸代码**（有的模型不包 fence）→ 原样通过，仍可编译。→ Task 3
5. **`.env` 值用 `export ` 前缀或引号包裹**（如 `export PASD_BACKEND=mock`、`PASD_BACKEND="mock"`）→ 注释剥离后仍正确解析。→ Task 1

---

### Task 1: 修复 `.env` 解析器剥行尾注释

**Files:**
- Modify: `src/pasd_life/settings.py`（`_load_dotenv`，约第 48–52 行）
- Test: `tests/test_settings.py`（新建）

**Interfaces:**
- Produces: `_load_dotenv(path)` 把 `KEY=value  # comment` 解析为 `KEY`/`value`；`export KEY=value` 与 `KEY="value"` 继续可用。

- [ ] **Step 1: 写失败测试**

`tests/test_settings.py`（`unittest`，测试专用 key，避免污染 `os.environ`，用 `self.addCleanup(os.environ.pop, ...)`）：

```python
import os, tempfile, unittest
from pathlib import Path
from src.pasd_life.settings import _load_dotenv

class TestDotenv(unittest.TestCase):
    def _load(self, text):
        d = tempfile.mkdtemp(); p = Path(d) / ".env"
        p.write_text(text, encoding="utf-8")
        _load_dotenv(p)
        for k in ("PASD_T_BACKEND", "PASD_T_REAL", "PASD_T_QUOTED", "PASD_T_EXP"):
            self.addCleanup(os.environ.pop, k, None)

    def test_strips_inline_comment(self):
        self._load("PASD_T_BACKEND=mock            # mock | mujoco | real\n")
        self.assertEqual(os.environ.get("PASD_T_BACKEND"), "mock")

    def test_keeps_export_and_quotes(self):
        self._load("export PASD_T_EXP=mock\nPASD_T_QUOTED=\"dev\"\n")
        self.assertEqual(os.environ.get("PASD_T_EXP"), "mock")
        self.assertEqual(os.environ.get("PASD_T_QUOTED"), "dev")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest tests.test_settings -v`（或 `make check` 前先 `PYTHONPATH=src:. python3 -m unittest tests.test_settings -v`）
Expected: `test_strips_inline_comment` FAIL（`PASD_T_BACKEND` 值含 `# mock | ...`）

- [ ] **Step 3: 实现**：在 `_load_dotenv` 里，`value = value.strip().strip('"').strip("'")` 改为 `value = value.split("#", 1)[0].strip().strip('"').strip("'")`

- [ ] **Step 4: 运行测试确认通过**

Run: `PYTHONPATH=src:. python3 -m unittest tests.test_settings -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**（`git add src/pasd_life/settings.py tests/test_settings.py && git commit -m "fix: strip inline comments in .env reader"`）

---

### Task 2: `Executor.run` dict→Observation 归一化

**Files:**
- Modify: `src/pasd_life/executor.py`（`run` 方法，`obs = fn(self.api)` 之后）
- Test: `tests/test_executor.py`（新建）

**Interfaces:**
- Consumes: `Observation`（`schema.py`）、`Executor`/`RobotAPI`/`MockPiPER`（已存在）
- Produces: `Executor.run(str)` 接受返回 `dict` 的策略源码，归一化为 `Observation(state, steps, success)`。

- [ ] **Step 1: 写失败测试**

`tests/test_executor.py`：

```python
import unittest
from src.pasd_life.executor import Executor
from src.pasd_life.robot_api import RobotAPI, MockPiPER
from src.pasd_life.schema import Observation

SRC = "def run(robot):\n    robot.open_gripper()\n    return {\"steps\": 1, \"state\": {\"ok\": True}}\n"

class TestExecutor(unittest.TestCase):
    def test_normalizes_dict_return(self):
        obs = Executor(RobotAPI(MockPiPER({}))).run(SRC)
        self.assertIsInstance(obs, Observation)
        self.assertEqual(obs.steps, 1)
        self.assertEqual(obs.state["ok"], True)

    def test_dict_missing_fields_defaults(self):
        obs = Executor(RobotAPI(MockPiPER({}))).run("def run(robot):\n    return {}\n")
        self.assertEqual(obs.steps, 0)
        self.assertEqual(obs.state, {})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `PYTHONPATH=src:. python3 -m unittest tests.test_executor -v`
Expected: FAIL（`'dict' object has no attribute 'steps'`）

- [ ] **Step 3: 实现**：在 `run` 里 `obs = fn(self.api)` 之后加

```python
if isinstance(obs, dict):
    obs = Observation(state=obs.get("state", {}), steps=obs.get("steps", 0),
                      success=obs.get("success", True))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `PYTHONPATH=src:. python3 -m unittest tests.test_executor -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**（`git add src/pasd_life/executor.py tests/test_executor.py && git commit -m "feat: normalize dict policy returns to Observation"`）

---

### Task 3: 配置常量 + `ClaudeCodePolicyGenerator.__init__`/`generate`

**Files:**
- Modify: `src/pasd_life/config.py`（追加常量）
- Modify: `src/pasd_life/policy_gen.py`（`ClaudeCodePolicyGenerator`）
- Test: `tests/test_policy_gen.py`（新建）

**Interfaces:**
- Consumes: `SceneContext`, `RepairHint`（`schema.py`）、`LLM_*` 常量（本任务新增）、`load_settings`（`settings.py`）
- Produces:
  - `ClaudeCodePolicyGenerator(client=None, model=None, max_tokens=None, temperature=None)`
  - `ClaudeCodePolicyGenerator.generate(task: str, ctx: SceneContext, hints: list[RepairHint]) -> str`（返回源码字符串）
  - 常量 `LLM_TEMPERATURE: float = 0.2`、`LLM_MAX_TOKENS: int = 2048`、`LLM_MODEL_DEFAULT: str = "deepseek-v4-pro[1M]"`

- [ ] **Step 1: 写失败测试**

`tests/test_policy_gen.py`（`_FakeClient` 用 `.messages.create(**kw)` 返回带 `.content` 的假响应；content 块有 `.type`/`.text`）：

```python
import unittest
from src.pasd_life.policy_gen import ClaudeCodePolicyGenerator
from src.pasd_life.config import LLM_MAX_TOKENS, LLM_TEMPERATURE
from src.pasd_life.executor import Executor
from src.pasd_life.robot_api import RobotAPI, MockPiPER
from src.pasd_life.schema import SceneContext

class _Block:
    def __init__(self, type_, text=""): self.type, self.text = type_, text
class _Resp:
    def __init__(self, content): self.content, self.stop_reason = content, "end_turn"
class _Messages:
    def __init__(self, resp): self._resp = resp
    def create(self, **kw): return self._resp
class _FakeClient:
    def __init__(self, content): self.messages = _Messages(_Resp(content))

class TestPolicyGenerator(unittest.TestCase):
    def _ctx(self):
        return SceneContext("T1", "slender rod", "dev", {"aspect_ratio": 5.3})

    def test_defaults_and_explicit_model(self):
        gen = ClaudeCodePolicyGenerator(client=_FakeClient([]), model="m")
        self.assertEqual(gen.model, "m")
        self.assertEqual(gen.max_tokens, LLM_MAX_TOKENS)
        self.assertEqual(gen.temperature, LLM_TEMPERATURE)

    def test_generate_strips_thinking_and_fence(self):
        blocks = [_Block("thinking", "let me think"),
                  _Block("text", "```python\ndef run(robot):\n    robot.open_gripper()\n    return {\"steps\": 1, \"state\": {}}\n```")]
        src = ClaudeCodePolicyGenerator(client=_FakeClient(blocks), model="m").generate("T1", self._ctx(), [])
        self.assertIn("def run(robot):", src)
        self.assertNotIn("let me think", src)
        self.assertNotIn("```", src)
        Executor(RobotAPI(MockPiPER({})))._compile(src)  # 通过白名单编译

    def test_generate_no_text_block_raises(self):
        gen = ClaudeCodePolicyGenerator(client=_FakeClient([_Block("thinking", "only")]), model="m")
        with self.assertRaises(RuntimeError):
            gen.generate("T1", self._ctx(), [])

    def test_generate_bare_source_no_fence_passthrough(self):
        src0 = "def run(robot):\n    return {\"steps\": 1, \"state\": {}}\n"
        src = ClaudeCodePolicyGenerator(client=_FakeClient([_Block("text", src0)]), model="m").generate("T1", self._ctx(), [])
        self.assertEqual(src.strip(), src0.strip())
```

- [ ] **Step 2: 运行测试确认失败**

Run: `PYTHONPATH=src:. python3 -m unittest tests.test_policy_gen -v`
Expected: FAIL（`NotImplementedError` / `AttributeError`，类尚是桩）

- [ ] **Step 3: 实现 `config.py` 常量 + `policy_gen.py`**

`config.py` 追加三个常量（值见 Interfaces）。`policy_gen.py` 的 `ClaudeCodePolicyGenerator`：

- `__init__`：存 `self._client = client`；`self.model = model or _resolve_model()`；`self.max_tokens = max_tokens if max_tokens is not None else LLM_MAX_TOKENS`；`self.temperature = temperature if temperature is not None else LLM_TEMPERATURE`。
- `_resolve_model()`：`s = load_settings(); return s.llm_model or os.environ.get("ANTHROPIC_MODEL", "") or LLM_MODEL_DEFAULT`。
- `_get_client()`：`self._client` 非空则返回；否则 `import anthropic`（包在 `try/except ImportError`，缺失抛清晰 `RuntimeError`）并 `return anthropic.Anthropic()`。
- `generate()`：拼 system prompt（模块级常量 `_SYSTEM_PROMPT`，须含：五原语及 SI 单位、输出契约「只输出 `def run(robot):` 并返回 `{"steps":N,"state":{...}}`、不 import」）与 user 消息（task + `ctx.instruction`/`ctx.scene_summary`/`ctx.features` + hints 文本）；调 `self._get_client().messages.create(model=self.model, max_tokens=self.max_tokens, temperature=self.temperature, system=_SYSTEM_PROMPT, messages=[...])`；从 `resp.content` 收集 `type=="text"` 块的 `.text`，跳过 thinking/reasoning；去掉首尾 markdown fence（```python / ```）；无 text 块抛 `RuntimeError`；返回字符串。

- [ ] **Step 4: 运行测试确认通过**

Run: `PYTHONPATH=src:. python3 -m unittest tests.test_policy_gen -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**（`git add src/pasd_life/config.py src/pasd_life/policy_gen.py tests/test_policy_gen.py && git commit -m "feat: implement ClaudeCodePolicyGenerator.generate with LLM config"`）

---

### Task 4: `ClaudeCodePolicyGenerator.propose`

**Files:**
- Modify: `src/pasd_life/policy_gen.py`
- Test: `tests/test_policy_gen.py`（追加）

**Interfaces:**
- Consumes: `Trace`, `PiPERError`, `SceneContext`（`schema.py`）；Task 3 的 `ClaudeCodePolicyGenerator` 基础设施
- Produces: `ClaudeCodePolicyGenerator.propose(trace) -> dict | None`（dict 含 `fixes == trace.error_code`；无效/不匹配/不可解析返回 None）

- [ ] **Step 1: 写失败测试**（追加到 `tests/test_policy_gen.py`）

```python
import json
from src.pasd_life.schema import PiPERError, Trace

def _trace(code="GRASP_SLIP"):
    return Trace.from_error("T1", PiPERError(code, {"aspect_ratio": 5.3}), SceneContext("T1", "rod", "dev", {}))

class TestPropose(unittest.TestCase):
    def test_returns_dict_when_fixes_match(self):
        payload = {"fixes": "GRASP_SLIP", "approach": "side", "text": "侧夹"}
        blocks = [_Block("text", "```json\n" + json.dumps(payload) + "\n```")]
        out = ClaudeCodePolicyGenerator(client=_FakeClient(blocks), model="m").propose(_trace())
        self.assertEqual(out, payload)

    def test_returns_none_when_fixes_mismatch(self):
        blocks = [_Block("text", json.dumps({"fixes": "OTHER"}))]
        out = ClaudeCodePolicyGenerator(client=_FakeClient(blocks), model="m").propose(_trace())
        self.assertIsNone(out)

    def test_returns_none_when_fixes_missing(self):
        blocks = [_Block("text", json.dumps({"text": "no fixes"}))]
        out = ClaudeCodePolicyGenerator(client=_FakeClient(blocks), model="m").propose(_trace())
        self.assertIsNone(out)

    def test_returns_none_on_invalid_json(self):
        blocks = [_Block("text", "not json")]
        out = ClaudeCodePolicyGenerator(client=_FakeClient(blocks), model="m").propose(_trace())
        self.assertIsNone(out)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `PYTHONPATH=src:. python3 -m unittest tests.test_policy_gen -v`
Expected: `test_returns_dict_when_fixes_match` FAIL（`NotImplementedError`）

- [ ] **Step 3: 实现 `propose(trace)`**

调 `messages.create`（模型/温度/max_tokens 同 `generate` 的常量），prompt 要求输出单个 JSON 对象 `{"fixes": <error_code>, ...}`；提取 text 块 → 去 fence → `json.loads`；`json.loads` 失败或结果非 dict 或 `fixes != trace.error_code` 时返回 None；否则返回该 dict。复用 Task 3 的 `_get_client()` 与 fence/text 提取逻辑（可抽公共私有方法）。

- [ ] **Step 4: 运行测试确认通过**

Run: `PYTHONPATH=src:. python3 -m unittest tests.test_policy_gen -v`
Expected: 全部 8 tests PASS

- [ ] **Step 5: 全量回归 + Commit**

Run: `make check`（或 `python3 scripts/contract_tests.py && python3 scripts/run_smoke.py && python3 scripts/fairness_audit.py && python3 scripts/run_backend_probe.py`）
Expected: 全绿
Commit: `git add src/pasd_life/policy_gen.py tests/test_policy_gen.py && git commit -m "feat: implement ClaudeCodePolicyGenerator.propose"`

---

## 非功能说明（不建任务）

- 真机调用 `ClaudeCodePolicyGenerator.generate()` 需绕过 socks 代理：`env -u ALL_PROXY -u all_proxy`，或 venv 装 `socksio`。生成器 `_get_client()` 不主动改环境变量，此约束写进 `policy_gen.py` 模块 docstring 与 `docs/08`（可选）。
- `anthropic.Anthropic()` 无参创建在本机依赖 `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_BASE_URL` 环境变量（非 `.env` 的 `ANTHROPIC_API_KEY`）；离线契约测试用注入的 `_FakeClient`，不触发网络。
