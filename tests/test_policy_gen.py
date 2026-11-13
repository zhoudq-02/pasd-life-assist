"""ClaudeCodePolicyGenerator (offline, fake client). Contract: design spec Task 3/4."""
import json
import os
import sys
import types
import unittest
from unittest import mock

from src.pasd_life.config import LLM_MAX_TOKENS, LLM_MODEL_DEFAULT, LLM_TEMPERATURE
from src.pasd_life.executor import Executor
from src.pasd_life.policy_gen import ClaudeCodePolicyGenerator, _extract_text, _resolve_model
from src.pasd_life.robot_api import MockPiPER, RobotAPI
from src.pasd_life.schema import PiPERError, SceneContext, Trace


class _Block:
    def __init__(self, type_, text=""):
        self.type, self.text = type_, text


class _Resp:
    def __init__(self, content):
        self.content, self.stop_reason = content, "end_turn"


class _Messages:
    def __init__(self, resp):
        self._resp = resp

    def create(self, **kw):
        return self._resp


class _FakeClient:
    def __init__(self, content):
        self.messages = _Messages(_Resp(content))


class TestPolicyGenerator(unittest.TestCase):
    def _ctx(self):
        return SceneContext("T1", "slender rod", "dev", {"aspect_ratio": 5.3})

    def test_defaults_and_explicit_model(self):
        gen = ClaudeCodePolicyGenerator(client=_FakeClient([]), model="m")
        self.assertEqual(gen.model, "m")
        self.assertEqual(gen.max_tokens, LLM_MAX_TOKENS)
        self.assertEqual(gen.temperature, LLM_TEMPERATURE)

    def test_generate_strips_thinking_and_fence(self):
        blocks = [
            _Block("thinking", "let me think"),
            _Block("text", "```python\ndef run(robot):\n    robot.open_gripper()\n    return {\"steps\": 1, \"state\": {}}\n```"),
        ]
        src = ClaudeCodePolicyGenerator(client=_FakeClient(blocks), model="m").generate("T1", self._ctx(), [])
        self.assertIn("def run(robot):", src)
        self.assertNotIn("let me think", src)
        self.assertNotIn("```", src)
        Executor(RobotAPI(MockPiPER({})))._compile(src)

    def test_generate_no_text_block_raises(self):
        gen = ClaudeCodePolicyGenerator(client=_FakeClient([_Block("thinking", "only")]), model="m")
        with self.assertRaises(RuntimeError):
            gen.generate("T1", self._ctx(), [])

    def test_generate_bare_source_no_fence_passthrough(self):
        src0 = "def run(robot):\n    return {\"steps\": 1, \"state\": {}}\n"
        src = ClaudeCodePolicyGenerator(client=_FakeClient([_Block("text", src0)]), model="m").generate("T1", self._ctx(), [])
        self.assertEqual(src.strip(), src0.strip())

    def test_extract_text_coerces_non_string(self):
        self.assertEqual(_extract_text([_Block("text", ["def run(robot):"])]), "def run(robot):")

    def test_generate_fence_only_raises(self):
        gen = ClaudeCodePolicyGenerator(client=_FakeClient([_Block("text", "```")]), model="m")
        with self.assertRaises(RuntimeError):
            gen.generate("T1", self._ctx(), [])

    def test_lazy_client_is_memoized(self):
        gen = ClaudeCodePolicyGenerator(client=None, model="m")
        fake_module = types.SimpleNamespace(Anthropic=mock.Mock(return_value="FAKE_CLIENT"))
        with mock.patch.dict(sys.modules, {"anthropic": fake_module}):
            self.assertEqual(gen._get_client(), "FAKE_CLIENT")
            self.assertEqual(gen._get_client(), "FAKE_CLIENT")
            self.assertEqual(fake_module.Anthropic.call_count, 1)

    def test_resolve_model_strips_whitespace_and_defaults(self):
        with mock.patch.dict(os.environ, {"PASD_LLM_MODEL": "   ", "ANTHROPIC_MODEL": ""}):
            self.assertEqual(_resolve_model(), LLM_MODEL_DEFAULT)


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


if __name__ == "__main__":
    unittest.main()
