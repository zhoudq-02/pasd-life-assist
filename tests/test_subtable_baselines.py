"""Sub-table C1/C2 baselines: mechanism-equivalent proxies (docs/03 §3)."""
import unittest

from integration.baselines.armada import ARMADAProxy
from integration.baselines.irosa_interface import IROSAInterface
from integration.baselines.neerl import NEERLProxy
from integration.baselines.reflexion import ReflexionMemory
from integration.baselines.rlingua import RLinguaProxy
from integration.baselines.soar import SOARProxy
from integration.baselines.sss import SSSProxy
from integration.baselines.uniskill_proxy import UniskillProxy
from integration.baselines.vla_proxy import VLAProxy
from src.pasd_life.schema import Observation, PiPERError, SceneContext, Trace


def _ctx():
    return SceneContext("T1", "rod", "dev", {"aspect_ratio": 5.3})


def _fail(code="GRASP_SLIP"):
    return Trace.from_error("T1", PiPERError(code, {"aspect_ratio": 5.3}), _ctx())


def _success():
    return Trace.from_success("T1", Observation(state={"elapsed": 1.0}, steps=3), _ctx())


class TestReflexion(unittest.TestCase):
    def test_stores_lessons_and_retrieves_text(self):
        m = ReflexionMemory()
        m.on_episode_end(_fail())
        hints = m.retrieve(_ctx())
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].verified_by, "none")
        self.assertFalse(hints[0].verified)


class TestUniskill(unittest.TestCase):
    def test_only_success_stored(self):
        m = UniskillProxy()
        m.on_episode_end(_success())
        m.on_episode_end(_fail())
        self.assertEqual(len(m.items), 1)


class TestIROSA(unittest.TestCase):
    def test_retrieve_interface_hint(self):
        m = IROSAInterface()
        hints = m.retrieve(_ctx())
        self.assertEqual(len(hints), 1)
        self.assertIn("KMP", hints[0].text)


class TestSSS(unittest.TestCase):
    def test_stores_only_verified_repairs_and_counts_fm(self):
        m = SSSProxy()
        t1 = _fail(); t1.repair_verified = True; t1.applied_repair = {"fixes": "GRASP_SLIP"}
        t2 = _fail()
        m.on_episode_end(t1)
        m.on_episode_end(t2)
        self.assertEqual(len(m.items), 1)
        self.assertEqual(m.fm_calls, 2)

    def test_retrieve_verified_by_vlm_judge(self):
        m = SSSProxy()
        t = _fail(); t.repair_verified = True; t.applied_repair = {"fixes": "GRASP_SLIP"}
        m.on_episode_end(t)
        hints = m.retrieve(_ctx())
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0].verified_by, "vlm_judge")


class TestSOAR(unittest.TestCase):
    def test_retrieve_always_empty_and_vlm_labels(self):
        m = SOARProxy()
        m.on_episode_end(_fail())
        self.assertEqual(m.retrieve(_ctx()), [])
        self.assertEqual(m.fm_calls, 1)


class TestARMADA(unittest.TestCase):
    def test_human_budget_and_verified_by_human(self):
        m = ARMADAProxy()
        m.on_episode_end(_fail())
        self.assertEqual(m.human_budget, 1)
        hints = m.retrieve(_ctx())
        self.assertEqual(hints[0].verified_by, "human")


class TestTrainingProxies(unittest.TestCase):
    def test_retrieve_always_empty(self):
        for cls in (NEERLProxy, RLinguaProxy, VLAProxy):
            m = cls()
            m.on_episode_end(_fail())
            self.assertEqual(m.retrieve(_ctx()), [], cls.__name__)


if __name__ == "__main__":
    unittest.main()
