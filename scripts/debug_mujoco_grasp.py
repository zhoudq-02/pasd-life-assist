"""Interactive MuJoCo grasp debugger: real-time render + step-by-step tuning.

Run on a machine WITH a display:
    .venv/bin/python scripts/debug_mujoco_grasp.py

This loads configs/mujoco/scene_grasp.xml (arm + table + slender rod), opens a
MuJoCo viewer, and drives the simulation from a small REPL so you can visually
tune the grasp until "top grasp of the slender rod slips, side grasp holds".

The grasp sequence to try:
    reset  ->  open  ->  step 200  ->  close 0.008  ->  step 300  ->  lift  ->  step 500  ->  rod
"""
from __future__ import annotations

import sys
from pathlib import Path

HOME = [0.0, 1.57, -1.3485, 0.0, 0.0, 0.0, 0.0, 0.0]

HELP = """commands:
  step [n]          step the sim n times (default 1)
  open              open the gripper (ctrl -> 0.035)
  close [w]         close the gripper to half-width w metres (default 0.008)
  lift [d]          raise the elbow (joint2) by d rad (default 0.25)
  wrist <rad>       set the wrist roll (joint6) — 0 = top, 1.57 = side
  joints q1..q6     set the 6 arm joints directly (rad)
  home              move the arm to the home config
  reset             reset the whole scene (rod back to start)
  friction <mu>     set the rod tangential friction (default 0.01)
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

    mujoco.mj_resetData(model, data)
    data.qpos[:8] = HOME

    try:
        viewer = mujoco.viewer.launch_passive(model, data)
    except Exception as exc:  # noqa: BLE001
        print(f"viewer launch failed (need a display / GL): {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(HELP)
    print(f"scene: {scene.name} | rod friction = {model.geom_friction[rod_geom].tolist()}")
    print("grasp sequence: reset -> open -> step 200 -> close 0.008 -> step 300 -> lift -> step 500 -> rod")

    def show_rod():
        print(f"rod  pos = {data.xpos[rod_id].round(4).tolist()}  "
              f"(held if z > 0.34)")

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
                for _ in range(n):
                    mujoco.mj_step(model, data)
            elif op == "open":
                data.ctrl[gripper_act] = 0.035
            elif op == "close":
                w = float(parts[1]) if len(parts) > 1 else 0.008
                data.ctrl[gripper_act] = max(0.0, min(0.035, w))
            elif op == "lift":
                d = float(parts[1]) if len(parts) > 1 else 0.25
                data.ctrl[arm_acts[1]] = data.qpos[1] + d
            elif op == "wrist":
                data.qpos[5] = float(parts[1])
            elif op == "joints":
                q = [float(x) for x in parts[1:7]]
                data.qpos[:6] = q
            elif op == "home":
                data.qpos[:8] = HOME
                data.qvel[:] = 0.0
            elif op == "reset":
                mujoco.mj_resetData(model, data)
                data.qpos[:8] = HOME
                data.qvel[:] = 0.0
            elif op == "friction":
                mu = float(parts[1])
                model.geom_friction[rod_geom] = [mu, 0.005, 0.005]
                print(f"rod friction set to {model.geom_friction[rod_geom].tolist()}")
            elif op == "rod":
                show_rod()
            elif op == "gripper":
                print(f"gripper qpos(joint7)={data.qpos[6]:.4f}  width={2*data.qpos[6]:.4f} m")
            elif op == "grasp":
                w = float(parts[1]) if len(parts) > 1 else 0.008
                approach = parts[2] if len(parts) > 2 else "top"
                data.qpos[5] = 0.0 if approach == "top" else 1.57
                data.ctrl[gripper_act] = 0.035
                for _ in range(200):
                    mujoco.mj_step(model, data)
                data.ctrl[gripper_act] = w
                for _ in range(300):
                    mujoco.mj_step(model, data)
                data.ctrl[arm_acts[1]] = data.qpos[1] + 0.25
                for _ in range(500):
                    mujoco.mj_step(model, data)
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
