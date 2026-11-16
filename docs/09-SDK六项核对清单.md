# 09　PiPER SDK 六项核对清单与适配建议

> 状态：已读取本机 `/mnt/sda/users/zdq/piper_sdk`（当前版本 **0.6.1**，`PiperSDK_CURRENT_VERSION`）源码，
> 以下六项**已从源码提取具体结论**；但**尚未在真机 / CAN 上逐项验证**（读源码 ≠ 真机核实）。
> `PiperSDKAdapter` 仍保持显式失败，直到真机逐项确认后再接线（docs/08 §6、docs/07 硬约束 5）。

## 六项核对清单（源码结论 + 待现场核实）

| # | 核对项 | 源码结论（v0.6.1） | 待真机核实 |
|---|---|---|---|
| 1 | **接口类名与连接** | 类 `C_PiperInterface_V2`（`piper_sdk.__init__` 导出，另有 V1 `C_PiperInterface`）；构造 `C_PiperInterface_V2("can0")`；连接 `piper.ConnectPort(can_init=False, piper_init=True, start_thread=True)` | `can0` 是否对应你的 USB2CAN；SDK 版本与臂固件是否匹配 |
| 2 | **关节/位姿单位** | `JointCtrl(joint_1..joint_6)` 每轴单位 **0.001 度**；SI rad → `round(rad × 180/π × 1000)`；反馈 `ArmMsgFeedBackJointStates.joint_N` 同为 0.001 度 | 真机实际量程与限位表一致（见下） |
| 3 | **夹爪开度换算** | `GripperCtrl(gripper_angle, effort, code, set_zero)`：`gripper_angle` 单位 **0.001 mm**（SI m → `round(width_m × 1e6)`）；`effort` 单位 0.001 N/m（0–5000 → 0–5 N/m）；`code`：0x00 失能 / 0x01 使能 / 0x02,0x03 清错 | 0–70 mm 量程与 0.001 mm 编码对应关系 |
| 4 | **状态反馈字段** | `GetArmStatus()` → `(time_stamp, Hz, arm_status)`：`ctrl_mode`(0x00 待机 / 0x01 CAN / 0x02 示教)、`arm_status`(0x00 正常 / **0x01 急停** / 0x02 无解 / 0x03 奇异)；`GetArmHighSpdMsg` 含 `arm_joint_feedback`(0.001°) 与 `gripper_feedback.grippers_angle`(0.001 mm) + `foc_status`(8 位状态) | 反馈 CAN ID 0x2A5–0x2A8 是否正常刷新 |
| 5 | **使能/失能/急停** | 使能 `EnablePiper()` → `EnableArm(7)`（7 = 6 关节 + 夹爪）；失能 `DisablePiper()` → `DisableArm(7)`；急停 `EmergencyStop(0x01)`（0x02 恢复）→ CAN 0x150；`ResetPiper()` 会**立即失电**（危险） | 急停必须外挂控制层、不经过 LLM |
| 6 | **控制频率与超时** | demo 循环 `sleep(0.005)` ≈ **200 Hz**；`GetArmStatus` 返回 `Hz`；`MotionCtrl_2` 有 `move_spd_rate_ctrl`(0–100%) | 实际 CAN 刷新率；据此定 `GuardConfig.step_timeout_s`（默认 2.0 s） |

**关节限位（JointCtrl docstring，用于可达性预筛）**：joint1 ±2.6179 rad(±150°)、joint2 [0, 3.14]([0,180°])、joint3 [-2.967, 0]([-170°,0])、joint4 ±1.745(±100°)、joint5 ±1.22(±70°)、joint6 ±2.09439(±120°)。

## 最小适配改动建议（`PiperSDKAdapter` 五方法映射，未实现）

> 待真机逐项核实后再接线；当前 `connect()` 仍抛 `BackendUnavailable`。

| 适配器方法 | 建议的 SDK 映射（SI 换算） |
|---|---|
| `connect()` | `self._piper = C_PiperInterface_V2(can_interface)`；`ConnectPort()`；循环 `EnablePiper()` 直到 True |
| `move(pose, speed)` | 六轴逆解 → `JointCtrl(j1..j6)`（rad → 0.001°）；速度经 `MotionCtrl_2(ctrl_mode=0x01, move_mode=0x01, move_spd_rate_ctrl=speed_pct)` |
| `gripper(open_, width_m)` | `GripperCtrl(round(width_m*1e6), effort, 0x01 if open_ else 0x00, 0)` |
| `ik(target_pose)` | `C_PiperForwardKinematics` 或真机 IK；注意 6-DoF 无零空间、需可达性预筛（无解 → `IK_UNREACHABLE`） |
| `observe()` | `GetArmStatus()` + `GetArmHighSpdMsg` → 映射到 `REAL_OBSERVABLE_FIELDS`（rad/夹爪 mm 还原为 SI） |
| `stop()` | `EmergencyStop(0x01)`（急停，**不经过 LLM**） |

## 结论

- 六项全部有**源码级答案**，接口、单位、使能、急停、反馈字段均已明确。
- **仍缺的是真机验证**：CAN 是否连通、SDK/固件版本匹配、量程与限位一致、200Hz 是否稳定。
- 因此 `PiperSDKAdapter` **保持显式失败**是正确状态；真机到位并逐项勾选后，按上表实现五方法即可。
