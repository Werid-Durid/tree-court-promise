# 课堂骨骼动画

四人均在原 MMD 骨架上制作动作，烘焙为独立 FBX / GLB。原始修复模型位于 `blender/generated`，动作派生文件位于 `blender/animated`；不覆盖原网格、材质与表情。

| 角色 | 课堂行为 |
| --- | --- |
| 阿那克萨戈拉斯 | 站在讲台，抬手讲解，分步转身，往返踱步，停步继续讲解 |
| 风堇 | 站在讲台旁，双手收于身前，轻微抬手提示和点头 |
| 遐蝶 | 朝向黑板坐在椅上，小幅手部回应、点头，动作克制 |
| 白厄 | 朝向黑板坐在椅上，抬手和较明显的回应点头 |

动作周期 24 秒、每秒 24 帧。腿部使用原脚部 IK 固定支撑目标，摆腿具有抬脚和缓入缓出；手臂按原骨长解算肘部平面，骨盆承担步行重心变化。导出时烘焙约束，运行时不依赖 Blender / MMD 插件。椅面 48 cm，学生髋、膝和脚部目标与桌椅共同标定。

## 复现

在项目根目录执行：

```powershell
& D:/blender/blender.exe --factory-startup -b --python blender/create_classroom_motion.py
npm.cmd --prefix web/renderer run build
& D:/UE5/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe ue5/TreeCourt/TreeCourt.uproject "-ExecutePythonScript=$pwd/ue5/install_classroom_motion.py" -unattended -nosplash -nullrhi
```

本次环境未提供可调用的 Blender / Unreal MCP 接口，使用两款软件的本地 Python 自动化入口；命令及结果留在本目录 `build-*.log`、`ue-install.log`、`ue-install.json` 中。

网站 `/models/{角色}.glb` 优先提供动作版，`/api/animation-status` 返回动作名称和可用状态。UE5 使用 `/Game/TreeCourt/L_Classroom` 中原角色，绑定各自骨架的 AnimSequence；`override_animation_data` 将循环播放设置保存到关卡。使用“播放 / Simulate”观察运行效果。

## 检查与边界

- 各角色导出面数与原模型一致：42466 / 39687 / 52293 / 37488。
- 原 UE5 角色目录导入前后散列一致，动画单独导入。
- `metrics.json`：导出 GLB 的支撑脚位移、脚部顶点最低高度、首尾骨骼位置差。
- 老师四段左脚支撑期抽样最大位移约 0.126 mm；四个动画首尾骨骼位置差小于 0.008 mm。四人脚部顶点最低高度在地面上下约 2.1 mm 内，老师网站站位还按原模型底高补偿。
- `previews`：单人正侧视图、网站和 UE5 实际场景截图、浏览器动画视频。
- `web/tests/animation-smoke.mjs` 使用独立测试档案，检查四个 AnimationMixer 成功载入以及移动端布局。

当前为程序化制作的基础课堂循环，尚未实现动作与逐句台词同步、动作捕捉或动态衣料碰撞。现有长披风和裙摆保留原骨骼跟随，极端视角及动作过渡仍可继续细调。此轮只涉及动作、座位及动画加载，没有调整教学内容、语音或学习进度逻辑。
