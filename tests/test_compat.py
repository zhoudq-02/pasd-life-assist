"""Optional compat layer: pasd aliases / agent glue / MCP server."""
import unittest

from integration.baselines.registry import build
from integration.mcp.pasd_mcp_server import _Server
from integration.pasd import retrieve_repair
from integration.pasd_agent import run_agent_episode
from src.pasd_life.demo import MockEnv
from src.pasd_life.gates import gate1_observe_failure
from src.pasd_life.pasd_core import Extractor, OnlineClusterer, SkillLibrary
from src.pasd_life.schema import PiPERError, SceneContext, Trace


def _fail():
    return Trace.from_error("T1", PiPERError("GRASP_SLIP", {"aspect_ratio": 5.3}),
                            SceneContext("T1", "rod", "dev", {"aspect_ratio": 5.3}))


class TestCompat(unittest.TestCase):
    def test_retrieve_repair_delegates(self):
        lib = SkillLibrary()
        gate1_observe_failure(_fail(), Extractor(), OnlineClusterer(), lib)
        hints = retrieve_repair(lib, SceneContext("T1", "rod", "dev", {"aspect_ratio": 5.3}))
        self.assertEqual(hints, [])  # CANDIDATE skills are not retrieved

    def test_run_agent_episode(self):
        mem = build("no_memory")
        env = MockEnv({"aspect_ratio": 5.3, "target_width": 0.022, "approach": "top"})
        ok, trace = run_agent_episode(mem, env, "T1", 0)
        self.assertFalse(ok)
        self.assertEqual(trace.error_code, "GRASP_SLIP")

    def test_mcp_snapshot(self):
        srv = _Server()
        self.assertEqual(srv.call_tool("snapshot", {})["library_size"], 0)
        srv.call_tool("observe_failure", {"task": "T1", "error_code": "GRASP_SLIP",
                                          "features": {"aspect_ratio": 5.3}})
        self.assertEqual(srv.call_tool("snapshot", {})["library_size"], 1)


if __name__ == "__main__":
    unittest.main()
