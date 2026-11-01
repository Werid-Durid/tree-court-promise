# Blender 环境报告 · 三渲二准备

更新：2026-10-22。对应任务：第一步「自行安装与配置 Blender 环境」。

## 1. 版本

| 项 | 值 |
| --- | --- |
| Blender | **5.0.1**（hash `a3db93c5b259`，build 2025-12-16 01:32:30） |
| 可执行文件 | `D:\blender\blender.exe` |
| 渲染引擎 | Eevee（`BLENDER_EEVEE`；Blender 5.0 中 Next 已并入该枚举） |

## 2. 插件

| 项 | 值 |
| --- | --- |
| 名称 | Paper Anime Render Helper |
| 版本 | **2.5.0** |
| 作者 | Paper Zhu（paperzhu） |
| 来源 | Blender Extensions `paperzhu-animehelper-extension`；GitHub `PUBG11S1/paperzhu-anime-helper` |
| 安装方式 | **CLI 扩展安装（可复现）**：`blender --command extension install-file -r user_default -e <zip>` |
| 安装路径 | `%APPDATA%\Blender Foundation\Blender\5.0\extensions\user_default\Paperzhu_animehelper_extension\` |
| 模块名 | `bl_ext.user_default.Paperzhu_animehelper_extension` |
| 本地副本 | `blender/vendor/paperzhu_animehelper_extension-2.5.0.zip`（换机器/断网可复现） |
| 安装脚本 | `blender/install_paper_anime_helper.ps1` |

## 3. 验证记录

### 3.1 插件模块出现在启用列表

```powershell
& D:\blender\blender.exe -b --python-expr "import bpy; print([a.module for a in bpy.context.preferences.addons])"
```

实际输出（节选）：

```
['bl_ext.blender_org.mmd_tools', 'bl_ext.user_default.Paperzhu_animehelper_extension', 'bl_pkg', 'cycles', ...]
```

### 3.2 三渲二基础节点链自检

- 测试脚本：`blender/test_paper_npr.py`
- 测试对象：立方体 `PaperNPRExtensionTestCube` + 球体 `PaperNPRExtensionTestSphere`
- 应用：`apply_color`（AgX High Contrast）+ `apply_toon_shadow`（阈值 0.45、柔边 0.08、强度 0.35）+ `apply_outline`（2mm）
- 渲染输出：
  - **`blender/style_baseline_render.png`**（应用后）
  - `blender/style_baseline_before.png`（默认 PBR 对照）
- Blender 回执：
  - 「已应用风格化色彩管理」
  - 「已为 2 个材质应用卡通明暗；跳过 0 个」
  - 「已为 2 个对象添加/更新描边」

## 4. 环境变量

本次**未使用** `$BLENDER_SYSTEM_SCRIPTS` / `$BLENDER_SYSTEM_EXTENSIONS`：插件通过 Blender 4.2+ 自带扩展系统安装到 `user_default` 仓库，路径固定、可脚本化。

可复现安装的两种等价方式（任选其一）：

- **方式 A（本次使用）**：`blender --command extension install-file -r user_default -e blender/vendor/paperzhu_animehelper_extension-2.5.0.zip`
- **方式 B（环境变量）**：把插件目录解压到自定义扩展根，并设置
  `BLENDER_USER_EXTENSIONS=<目录>`（用户扩展根），使 Blender 启动时在 `<目录>/user_default/Paperzhu_animehelper_extension/` 找到扩展；适合绿色/便携部署。

## 5. 复现步骤

```powershell
# 1. 安装插件（使用仓库内副本，无需联网）
& D:\blender\blender.exe --command extension install-file -r user_default -e `
  "$PWD\blender\vendor\paperzhu_animehelper_extension-2.5.0.zip"

# 2. 验证模块已启用
& D:\blender\blender.exe -b --python-expr "import bpy; print([a.module for a in bpy.context.preferences.addons])"

# 3. 生成三渲二基线测试渲染
& D:\blender\blender.exe -b --python blender\test_paper_npr.py
```

## 6. 注意事项

- `bpy.ops.wm.read_factory_settings()` 会关闭用户扩展；脚本中改用数据层清空场景 + `addon_utils.enable()` 兜底。
- 后台模式（`-b`）下避免 `bpy.ops.object.select_all/delete/shade_smooth`（context poll 失败）；改用对象数据 API 与 `select_set`。
- 插件要求 Eevee（Shader to RGB）；Cycles 不适用。
