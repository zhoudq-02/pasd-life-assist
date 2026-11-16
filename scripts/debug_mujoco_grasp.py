"""Interactive MuJoCo grasp debugger: real-time render + step-by-step tuning.

Run on a machine WITH a display:
    .venv/bin/python scripts/debug_mujoco_grasp.py

Loads configs/mujoco/scene_grasp.xml (arm + table + slender rod), opens a MuJoCo
viewer, and drives the simulation from a small REPL so you can visually tune the
grasp until "top grasp of the slender rod slips, side grasp holds".

Suggested sequence:
    reset -> open -> close 0.008 -> lift -> rod
"""
from __future__ import annotations

import sys
from pathlib import Path

HOME = [0.0, 1.57, -1.3485, 0.0, 0.0, 0.0, 0.0, 0.0]  # qpos: joint1..6 + joint7 + joint8

HELP = """commands:
  step [n]          step the sim n times (default 1)
  open              open the gripper (then steps 200 so you see it move)
  close [w]         close the gripper to half-width w metres (default 0.008, steps 200)
  lift [d]          raise the elbow (joint2) by d rad (default 0.25, steps 300)
  wrist <rad>       set the wrist roll (joint6) — 0 = top, 1.57 = side
  joints q1..q6     set the 6 arm joints directly (rad)
  home              move the arm to the home config (qpos + ctrl)
  reset             reset the whole scene (rod back to start)
  friction <mu>     set the rod tangential friction
  rod / gripper     print rod / gripper world position
  grasp <w> <a>     run a full grasp (width, approach top|side) and report held
  help              print this help
  q / quit          exit
"""


def main() -> None:
    import mujoco
    import mujoco.viewer  # noqa: F401  (register the viewer submodule)

    root = Path(__file__).resolve().parents[1]
    scene = root / "configs" / "mujoco" / "scene_grasp.xml"
    model = mujoco.MjModel.from_xml_path(str(scene))
    data = mujoco.MjData(model)

    gripper_act = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "gripper")
    rod_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "rod")
    rod_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "rod_geom")
    arm_acts = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"joint{i}") for i in range(1, 7)]

    def set_home() -> None:
        """Put the arm at HOME in both qpos and ctrl (so actuators hold it there)."""
        data.qpos[:8] = HOME
        data.qvel[:] = 0.0
        for i, act in enumerate(arm_acts):
            data.ctrl[act] = HOME[i]
        data.ctrl[gripper_act] = HOME[6]

    def step(n: int) -> None:
        for _ in range(n):
            mujoco.mj_step(model, data)

    set_home()
    mujoco.mj_forward(model, data)

    try:
        viewer = mujoco.viewer.launch_passive(model, data)
    except Exception as exc:  # noqa: BLE001
        print(f"viewer launch failed (need a display / GL): {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(HELP)
    print(f"scene: {scene.name} | rod friction = {model.geom_friction[rod_geom].tolist()}")
    print("arm holds HOME (qpos + ctrl set); 'open'/'close'/'lift' auto-step so you see motion.")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        parts = line.split()
        op = parts[0].lower()
        try:
            if op in ("q", "quit", "exit"):
                break
            elif op == "help":
                print(HELP)
            elif op == "step":
                n = int(parts[1]) if len(parts) > 1 else 1
                step(n)
            elif op == "open":
                data.ctrl[gripper_act] = 0.035
                step(200)
                print(f"gripper opened -> width {2 * data.qpos[6]:.4f} m")
            elif op == "close":
                w = float(parts[1]) if len(parts) > 1 else 0.008
                data.ctrl[gripper_act] = max(0.0, min(0.035, w))
                step(200)
                print(f"gripper closed -> width {2 * data.qpos[6]:.4f} m")
            elif op == "lift":
                d = float(parts[1]) if len(parts) > 1 else 0.25
                data.ctrl[arm_acts[1]] = data.qpos[1] + d
                step(300)
                print(f"elbow raised -> q2 {data.qpos[1]:.4f} rad")
            elif op == "wrist":
                v = float(parts[1])
                data.qpos[5] = v
                data.ctrl[arm_acts[5]] = v
                step(100)
            elif op == "joints":
                q = [float(x) for x in parts[1:7]]
                data.qpos[:6] = q
                for i, act in enumerate(arm_acts):
                    data.ctrl[act] = q[i]
                step(100)
            elif op == "home":
                set_home()
                step(100)
            elif op == "reset":
                mujoco.mj_resetData(model, data)
                set_home()
                print("scene reset; rod back to start")
            elif op == "friction":
                mu = float(parts[1])
                model.geom_friction[rod_geom] = [mu, 0.005, 0.005]
                print(f"rod friction set to {model.geom_friction[rod_geom].tolist()}")
            elif op == "rod":
                print(f"rod  pos = {data.xpos[rod_id].round(4).tolist()}  "
                      f"(held if z > 0.34)")
            elif op == "gripper":
                print(f"gripper qpos(joint7)={data.qpos[6]:.4f}  width={2 * data.qpos[6]:.4f} m")
            elif op == "grasp":
                w = float(parts[1]) if len(parts) > 1 else 0.008
                approach = parts[2] if len(parts) > 2 else "top"
                data.qpos[5] = 0.0 if approach == "top" else 1.57
                data.ctrl[arm_acts[5]] = data.qpos[5]
                data.ctrl[gripper_act] = 0.035
                step(200)
                data.ctrl[gripper_act] = max(0.0, min(0.035, w))
                step(300)
                data.ctrl[arm_acts[1]] = data.qpos[1] + 0.25
                step(500)
                held = data.xpos[rod_id][2] > 0.34
                print(f"grasp width={w} approach={approach}: "
                      f"rod z={data.xpos[rod_id][2]:.4f} held={held}")
            else:
                print(f"unknown command: {op} (try 'help')")
        except (ValueError, IndexError) as exc:
            print(f"bad args: {exc}")
        viewer.sync()

    viewer.close()
    print("bye")


if __name__ == "__main__":
    main()
