# 三渲二风格基线 · Paper Anime Render Helper

更新：2026-10-22。本文件是「可参数化」的风格基准，不是对某一张参考图的临摹。

## 1. 参考来源

- UP主：B站「竹下下下下下」，同作者署名 Paper Zhu。
- 插件：**Paper Anime Render Helper v2.5.0**（Blender Extensions，GPL-3.0-or-later，`paperzhu-animehelper-extension`；作者 paperzhu；GitHub issues `PUBG11S1/paperzhu-anime-helper`）。
- 安装/使用教程：B站 **BV1YaPYz5EDX**（尚未逐帧学习，仅确认入口）。
- 项目内既有基线：`blender/materials/approved_npr.json`（v1，用户此前已确认）。
- 「生气的那刻夏」视频（BV1riGbzeEHK）简介署名渲染方案为「卡渲秘咒」。

> 说明：本会话模型无图像输入，无法目视视频帧或渲染图；以下「视频观感」项凡不能从公开文字/参数确认的，均标注**待逐帧比对**，不编造精确数值。

## 2. 插件参数面板（已从 `props.py` 逐项核实）

| 分组 | 参数 | 默认值 | 可调范围 |
| --- | --- | --- | --- |
| Outline | Outline Thickness | 0.001 | 0.0 – 0.05 |
| Color | Color Contrast | AgX High Contrast | AGX_HIGH / MEDIUM_HIGH / HIGH / VERY_HIGH |
| Color | Color Exposure | 0.0 | −2.0 – 2.0 |
| Color | Node Contrast | 0.35 | −1.0 – 1.0 |
| Highlights | Highlight Mix | 0.6 | 0.0 – 1.0 |
| Highlights | Highlight Roughness | 0.15 | 0.0 – 1.0 |
| Toon Shadow | Shadow Color | (0.62, 0.62, 0.65, 1.0) | 0 – 1 |
| Toon Shadow | Shadow Threshold | 0.5 | 0.0 – 1.0 |
| Toon Shadow | Shadow Softness | 0.08 | 0.0 – 0.5 |
| Toon Shadow | Shadow Strength | 0.35 | 0.0 – 1.0 |
| Toon Shadow | Light Influence | 0.8 | 0.0 – 1.0 |
| Toon Shadow | Minimum Brightness | 0.15 | 0.0 – 1.0 |
| Glow | Glow Threshold | 0.85 | 0.0 – 10.0 |
| Skybox | Sky Source | Built-in Cartoon Sky | BUILTIN / FILE |
| Skybox | Environment Strength | 1.0 | 0.0 – 10.0 |
| Skybox | Horizontal Rotation | 0.0 | 0 – 2π |
| General | Switch to Eevee When Applying | True | bool |

插件操作器：`paper_helper.apply_outline / apply_outline_fix / remove_outline / apply_color / remove_color / apply_skin / remove_skin / apply_toon_shadow / remove_toon_shadow / apply_glow / remove_glow / apply_skybox / restore_skybox`。

实现要点（`toon_shadow.py`）：`Diffuse → Shader to RGB → RGB to BW → MapRange(SMOOTHERSTEP, softness) → 明暗混合 → Emission`，即 **2 段受光/背光** + 可调柔边；不是 PBR 连续渐变。描边为 Solidify 反向外壳 + 黑色材质。

## 3. 风格特征与观感（待逐帧比对项）

| 特征 | 可确认来源 | 结论 |
| --- | --- | --- |
| 着色色阶数量 | 插件实现为 2 段；项目已确认基线为 3 段（阈值 0.45/0.65） | 采用 **2–3 段**，默认 3 段（与项目既有基线一致） |
| 描边厚度倾向 | 插件默认 1mm，范围 0–50mm；项目已确认 2mm | 提案 **1–3mm**，起点 2mm |
| 高光形状 | 插件为 Fresnel 视角遮罩（非手绘高光块） | 高光为**视角边缘遮罩**；具体形状/位置 **待逐帧比对** |
| 肤色典型色值 | 项目 NPR 保留原贴图固有色，仅改明暗分段 | 肤色不强行换色；具体色值 **待逐帧比对** |
| 发色典型色值 | 同上；边缘光只挂衣料/头发 | 发色 **待逐帧比对** |
| 边缘光 | 项目基线：Fresnel IOR 1.45，阈值 0.70，强度 0.08；仅衣料 | 保留项目基线 |

## 4. 推荐基线配置（四位角色共用风格族）

```json
{
  "color_look": "AGX_HIGH",
  "color_exposure": 0.0,
  "outline_thickness_m": 0.002,
  "toon_threshold": 0.45,
  "toon_softness": 0.08,
  "toon_strength": 0.35,
  "toon_light_influence": 0.8,
  "toon_min_brightness": 0.12,
  "toon_shadow_color": [0.62, 0.62, 0.65],
  "highlight_mix": 0.6,
  "highlight_roughness": 0.15,
  "rim_ior": 1.45,
  "rim_threshold": 0.70,
  "rim_strength": 0.08,
  "rim_classes": ["cloth", "hair"],
  "glow_threshold": 0.85
}
```

角色微调规则（同族、不同色相）：
- 那刻夏（墨绿/薄荷）：暗部偏移偏冷绿，高光略强。
- 白厄（海蓝/白）：暗部偏蓝灰，明暗分界略软。
- 遐蝶（淡紫/银灰）：暗部偏移偏紫，避免紫发压成灰。
- 风堇（粉/白）：暗部偏粉灰，最小亮度略抬高，防止粉色阴影发脏。

## 5. 已验证

- 测试渲染：`blender/style_baseline_render.png`（应用色阶+描边+卡通明暗），对照 `blender/style_baseline_before.png`（默认 PBR）。
- 插件对 2 个测试材质应用卡通明暗成功、对 2 个对象添加描边成功（Blender 控制台中文回执）。
- 环境详情见 `blender/env_report.md`。

## 6. 定量自检（对象区域，可复跑）

`blender/analyze_style_baseline.py` 用 before/after 差异掩码隔离立方体+球体（318,930 像素），对比默认 PBR 与三渲二渲染：

| 指标 | 默认 PBR | 三渲二 | 判据 |
| --- | --- | --- | --- |
| 亮度直方图归一化熵 | 0.4799 | **0.1860** | 更低 → 色阶更分明 |
| 前 3 直方图区间占比 | 0.6809 | **0.9778** | 更高 → 色块更集中 |
| 边缘密度（\|∇L\| > 0.08） | 0.0043 | **0.0182**（4.2×） | 更高 → 描边/硬边可见 |
| 平均亮度梯度 | 0.00309 | 0.00462 | 参考项 |

`unique_levels`（20→45）与 `flat_fraction`（0.982→0.967）受抗锯齿与描边过渡像素影响，**不作为判据**，仅记录。

结论：熵显著下降、前 3 区间占比显著上升、边缘密度增至 4.2 倍，客观支持「色阶分明、描边可见、非连续渐变」。
原始数据：`blender/style_baseline_metrics.json`。复跑：用带 numpy+Pillow 的 Python 执行 `blender/analyze_style_baseline.py`。
