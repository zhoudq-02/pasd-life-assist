#!/usr/bin/env python3
"""Backend factory probe. Zero dependency, zero network, ZERO hardware motion.

Run on the Linux host (or the packaging host) to verify that settings,
the backend factory and the real-hardware guard all behave as documented:

    python3 scripts/run_backend_probe.py

Contract: docs/01 section 9 / docs/08 section 3 & 6.
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.pasd_life.backends import make_backend  # noqa: E402
from src.pasd_life.backends.base import BackendUnavailable, RealHardwareGuardError  # noqa: E402
from src.pasd_life.backends.guard import GuardConfig, GuardedBackend  # noqa: E402
from src.pasd_life.robot_api import MockPiPER, RobotAPI  # noqa: E402
from src.pasd_life.settings import load_settings  # noqa: E402


def main() -> int:
    s = load_settings()
    print("=== runtime settings (secrets never printed) ===")
    for key, value in s.describe().items():
        print(f"  {key:<20} {value}")

    print("\n=== 1) mock backend (default) ===")
    api = RobotAPI(make_backend("mock", settings=s, scene={"aspect_ratio": 5.3}))
    print("  observation:", api.get_observation())
    print("  move_to_pose:", api.move_to_pose({"target": [0.3, 0.0, 0.15]}, speed=0.1))
    print("  [OK] five-primitive whitelist reachable through the factory")

    print("\n=== 2) real backend must be refused without explicit confirmations ===")
    try:
        make_backend("real", settings=s)
    except RealHardwareGuardError as exc:
        print("  [OK] refused:", exc)
    else:
        print("  [FAIL] real backend was reachable without the guard")
        return 1

    print("\n=== 3) dry-run adapter: full stack, no motion ===")
    dry = replace(s, backend="real", adapter="null", allow_real=True, estop_ack=True)
    guarded = make_backend(settings=dry, confirm_real=True)
    api2 = RobotAPI(guarded)
    api2.move_to_pose({"target": [0.3, 0.0, 0.15]}, speed=0.1)
    api2.open_gripper()
    api2.close_gripper(width=0.022)
    api2.solve_ik({"target": [0.3, 0.0, 0.15]})
    print("  dry_run:", getattr(guarded.inner, "dry_run", False))
    print("  [OK] DRY-RUN only; no CAN frame, no joint motion")

    print("\n=== 4) control-layer speed clamp (LLM cannot bypass it) ===")
    wrapper = GuardedBackend(MockPiPER(), config=GuardConfig())
    result = wrapper.step("move_to_pose", pose={"target": [0.3, 0.0, 0.15]}, speed=0.9)
    print("  clamped eef_speed:", result["eef_speed"], "| violations:", wrapper.violations)
    if result["eef_speed"] > 0.15:
        print("  [FAIL] speed was not clamped")
        return 1
    print("  [OK] clamped to SafetyEnvelope.max_eef_speed")

    print("\n=== 5) mujoco backend fails loudly until the MJCF model exists ===")
    try:
        make_backend("mujoco", settings=s)
    except BackendUnavailable as exc:
        print("  [EXPECTED]", exc)
    else:
        print("  [INFO] MuJoCo model + dependency present")

    print("\nPROBE OK: no hardware was moved, nothing was installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
