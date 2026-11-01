# 树庭角色与教室质量规格 · 学习阶段待审稿

版本：2026-10-21 / draft-1。状态：**等待用户确认，不执行 Blender / UE5 操作**。
本轮仅编写本文件与 `knowledge/cet4_skills.json`。未运行建模、渲染、物理、导出或 UE 导入脚本。

## 1. 证据等级、环境与执行边界

- **文档确认**：下列官方手册/API 确认功能含义；不代表视频作者使用了某个数值。
- **目录/简介确认**：项目已有公开接口核实记录位于 `data/references/lesson-audit/`；没有逐段技术时间戳的内容不能标为“教程原参数”。
- **项目暂定**：为首次对照测试提出的具体值，均需本轮确认及后续单角色预览；不是 Blender 出厂默认值。
- **待补证**：视频确切节点、骨骼目标、材质色值与物理参数，标记“待用户补充时间戳/讲义”。

教程以 Blender 4.5 为一个基准；项目此前构建日志为 Blender 5.0.1。下一阶段先只读核实 MCP 返回的实际版本、可用节点输入和属性，不直接运行旧版 Eevee 开关。当前没有核实可调用的 Blender/UE5 MCP 连接；执行前必须确认工具可用。若不可用，报告连接缺口，不擅自改用命令行执行。

用户指定 `characters/profiles.json` 为角色唯一依据，但本次目录检查未找到该文件；当前角色文本实际位于 `data/curriculum/catalog.json`，另有 `voice/references/profiles.json` 声音参考档案。**三者不能视为同一文件**。角色档案路径的确认是未来剧情生成的接入前置条件；本轮不迁移、改写台词、好感或语音。

所有新资产副本、缓存和预览仅写 `blender/build/` 或 `assets/characters/exported/`。计划代码位置 `blender/materials/toon_shader.py`、`blender/physics/hair_cloth_config.py`；**本轮尚不创建可执行实现**。原始 PMX、贴图、原始 BLEND 不覆盖。

## 2. 三渲二材质：先一位角色验证

教程关联：[T1 三渲二 MMD 流程](https://www.bilibili.com/video/BV18DJC6dE1S/)。其具体节点与色值 **待用户补充时间戳/讲义**。以下节点行为来自 [Shader to RGB 手册](https://docs.blender.org/manual/en/4.3/render/shader_nodes/converter/shader_to_rgb.html)、[4.5 节点支持说明](https://docs.blender.org/manual/id/4.5/render/eevee/limitations/nodes_support.html)、[ColorRamp API](https://docs.blender.org/api/4.5/bpy.types.ColorRamp.html)。

### 2.1 MMD 副本预处理

1. 复制成构建资产，记录原文件 SHA256、骨架、材质槽、UV、形态键、蒙皮权重与贴图路径。
2. 用户要求按材质分离：在副本通过实际安装的 mmd_tools 接口执行；其操作器 ID 需先查插件版本，不能猜写调用名。
3. 分离前后核对顶点关联、三角面总数、材质对应、权重与每个表情；若插件分离丢失形态键，停止并保留副本，不应用到原件。
4. 按材质分离是本项目的可审阅工作流，并非节点生效的技术必要条件；材质槽本身也可以持有独立节点树。
5. 皮肤、脸、眼睛、头发、布料、金属、透明配饰分组。删除默认 Principled BSDF **仅作用于选定的赛璐珞材质副本**，不批量破坏眼睛透明层、原贴图或金属表现。

### 2.2 完整基础节点与连接

颜色标量说明：用于阈值计算的光照通道与用于固有色的贴图分开，避免把原贴图先乘进漫射再乘一次。

| 标识 / 完整节点名 | Blender 节点类型 | 输入与连接 | 项目暂定值（待确认） |
| --- | --- | --- | --- |
| Base Texture / Image Texture | `ShaderNodeTexImage` | 原 UV → Vector；Color → Base Multiply.Color1 | 沿用原固有色贴图，sRGB；不覆盖原图 |
| Light Probe / Diffuse BSDF | `ShaderNodeBsdfDiffuse` | BSDF → Shader to RGB.Shader | Color=(1,1,1,1)，Roughness=0 |
| Light Color / Shader to RGB | `ShaderNodeShaderToRGB` | Color → RGB to BW.Color | Eevee 专用 |
| Light Value / RGB to BW | `ShaderNodeRGBToBW` | Val → Toon Ramp.Fac | 光照转标量 |
| Toon Ramp / Color Ramp | `ShaderNodeValToRGB` | Color → Base Multiply.Color2 | `interpolation='CONSTANT'`；3 色阶 |
| Base Multiply / Mix Color（Multiply） | `ShaderNodeMixRGB`，`blend_type='MULTIPLY'` | Fac=1；输出 → Toon Emission.Color | 乘原贴图与分段光照；执行前检查当前版本节点接口 |
| Toon Emission / Emission | `ShaderNodeEmission` | Emission → Material Output.Surface | Strength=1 |
| Material Output | `ShaderNodeOutputMaterial` | 接收 Shader 输出 | Surface 使用 Emission，不把 Color 直接当 Shader 接入 |

“保留23个色块”暂解释为 **2–3 个色块**，拟用 3 个；若用户字面要求 23 个需另确认。初测色阶采用线性 RGB 乘数：位置 0.00 → (0.58,0.52,0.55)，0.45 → (0.82,0.78,0.78)，0.65 → (1,1,1)。0.45/0.65 是光照阈值，不是皮肤颜色；均为项目提案，视频未确认。

首次只对那刻夏的一个皮肤材质与一个衣料材质测试。保留脸部贴图中已有血色，默认不加写实毛孔、凹凸噪声或强镜面。脸部阴影若需要 SDF，必须先确认存在相应贴图与头部朝向数据；本规格不假定模型已有 SDF。

### 2.3 Fresnel 边缘光：独立分支

来源：[Fresnel 官方说明](https://docs.blender.org/manual/en/4.4/render/shader_nodes/input/fresnel.html)。文档确认 Factor 随视角/法线变化，未规定本项目的边缘光阈值。

连接：`Fresnel (ShaderNodeFresnel).Fac → Rim Ramp.Fac → Rim Tint Multiply → Add(Base Multiply, Rim) → Emission.Color`。
不要让 Fresnel 直接取代基础 Toon Ramp 的光照 Fac，否则会把明暗分段变为视角分段。

项目暂定：IOR=1.45；Rim Ramp 常值，位置 0.00=黑、0.70=白；Rim Tint 为暖白；附加强度 0.08，测试区间 0.03–0.12。皮肤默认关闭，头发/衣料才试开；阈值、色温与启用部位待用户确认。此支路仅模拟艺术边缘光，不宣称真实散射。

### 2.4 反向外壳描边

来源：[Solidify 官方说明](https://docs.blender.org/manual/id/4.5/modeling/modifiers/generate/solidify.html)。确认材质偏移是相对原面材质索引的偏移；“1”不普遍等于全模型第二材质槽。

- 分离后的单一表面对象：槽 0=原赛璐珞材质，槽 1=黑色描边材质；Solidify `material_offset=1`、`material_offset_rim=1`，Flip Normals 开启，黑色材质开启背面剔除以形成外壳描边。该材质不得设双面，否则会遮住正面。
- 修改器位于蒙皮变形之后；先确认法线与统一缩放，保留原形态键。多材质对象必须重映射或专门外壳副本，不能假设偏移 1 全落到黑色。
- 用户给出的厚度文本暂读为 0.01–0.05。**单位未确认，不直接采用**：若模型按米，它等于 10–50 毫米，容易遮脸。建议外壳外扩有效厚度 **2 毫米**起测，区间 1–4 毫米；以实际角色身高换算对象空间值，非统一填 0.02。
- 若坚持 0.02 模型单位，应在测得角色尺度后另做对照。厚度正负与 offset 配对以“壳向外扩、法线反向”为验收条件，执行阶段在副本确认；眼线和脸内边不自动加粗。

### 2.5 Eevee、AO 与辉光

来源：[4.5 Eevee 阴影](https://docs.blender.org/manual/en/4.5/render/eevee/light_settings.html)、[4.5 渲染通道](https://docs.blender.org/manual/en/4.5/render/layers/passes.html)、[4.5 Glare API](https://docs.blender.org/api/4.5/bpy.types.CompositorNodeGlare.html)。

选择实际安装版本的 Eevee 引擎。旧版 AO/Bloom 面板属性不能直接写入 4.5/5.x；AO 用当前可用 AO 材质节点/通道或遮蔽方案评估，辉光用合成器 Glare（BLOOM 或 FOG_GLOW）实现，不依赖旧 `use_bloom`。

项目暂定测试：1920×1080、64 渲染样本、固定曝光 0 EV、AgX；背景 AO 乘入强度 0.15、作用距离 0.15 米，脸部不乘 AO；辉光只叠高亮区域，最终与原图混合 0.05（测试 0–0.08）。Glare 阈值先设为当前节点中相当于线性亮度 1.0 的输入，具体 socket 名与可用范围待版本读取后确认。以上均非视频参数。

Shader to RGB 对渲染通道与部分屏幕空间效果有限制，首轮以 Combined 图像验收，不承诺 AO、SSS 与传统 PBR 完全一致。截图对照固定相机、曝光、光源、姿势；输出原材质、基础三阶、带边缘光三个版本到 `blender/build/previews/`，由用户选风格。

## 3. 头发 / 衣摆：阻尼追踪约束栈

教程关联：[T2 阻尼追踪](https://www.bilibili.com/video/BV1qpd1B8EF9/)。简介确认低配置下的跟随方案并提醒穿模；具体骨骼命名、目标构造与数值 **待用户补充时间戳/讲义**。
文档依据：[Damped Track](https://docs.blender.org/manual/en/latest/animation/constraints/tracking/damped_track.html)、[约束空间与影响](https://docs.blender.org/manual/en/4.5/animation/constraints/interface/common.html)。

**概念校正**：Damped Track 的“damped”指最短 swing 旋转、减少跟踪轴滚转，不是带时间积分的弹簧。Influence 只控制约束混合强度。不能把“越接近 1 越松弛、越小越紧绷”作为通用物理定律；迟滞必须由独立的延迟目标、模拟或已烘焙目标轨迹提供。

### 3.1 无循环依赖的目标与约束顺序

1. 为每根待测头发骨建立独立目标（非其受约束的后代），绑定到**只读基础动画**生成的代理链。根部固定，跟踪目标置于基本姿态的骨尾方向，避免零长目标；不得直接让骨追踪自己变形后的子骨，形成依赖环。
2. 项目暂定：目标轨迹进行确定性二阶跟随滤波，固有频率 3 Hz、阻尼比 0.85；24 fps 下每帧 4 个积分子步，先预滚 24 帧。它是本项目可复现目标生成方案，不是视频已核实算法；这几个值待用户确认，不等同 Influence。
3. 每根自由段骨：**Damped Track → Limit Rotation**，先跟踪再限角；用户已存在的其他约束另行检查，不能无差别删除。
4. Damped Track：Track Axis=`TRACK_Y`（骨骼局部 +Y），Influence 初值 0.35；候选 0.20–0.55。根部不加跟随，末端不凭索引统一加大，先看链长和权重。
5. Limit Rotation：Owner Space=`LOCAL`，XYZ 限制启用，Influence=1。以已校准的休止方向为中位，弯曲 X/Z 初值 ±12°、建议 ±8°–18°；扭转 Y 初值 ±5°、建议 ±3°–8°。写入 API 时转换为弧度；需先核对每条链的骨 roll 与局部轴，角度不能跨链机械照搬。

### 3.2 碰撞与输出

`collision_offset_m=0.008`，建议 0.005–0.012 米，**项目暂定**。这是代理胶囊外扩/接触校验的参数，不是 Damped Track 自带属性。Limit Rotation 也不自动消除穿模。
离线跟随测试需按身体代理检测目标/链段，必要时投影到代理表面，再限角并复查实际蒙皮；UE 的胶囊或 Physics Asset 不会自动修改一个纯烘焙 AnimSequence，必须显式使用有碰撞求解的运行时节点才产生补偿。

首个物理子任务：仅风堇一条头发链、60 帧运动测试，另预滚 24 帧。输出关闭约束/启用约束的相同帧 1、15、30、45、60 序列；检查根部固定、角度、身体距离和首尾衔接。验证后烘焙为骨骼视觉关键帧，FBX/GLB 接收端不依赖 Blender 约束。

## 4. 裙摆物理、刚体与烘焙选型

教程关联：[T3 裙摆物理配布](https://www.bilibili.com/video/BV1sMSQBkECB/)、[T4 刚体优化](https://www.bilibili.com/video/BV1GD9XBqEL2/)。T3 是效果展示与配布，不能由 14 秒画面反推唯一 Cloth 配置；T4 简介指向 XF-Blender 与 MikuMikuRig，未证明标准 Blender 参数即可复现其定制求解器。配布文件使用条件、插件版本与具体设置 **待用户补充时间戳/讲义或配布说明**。不直接安装/执行第三方文件。

### 4.1 选型规则

| 条件 | 方案与输出 | 待确认内容 |
| --- | --- | --- |
| 目标是离线近景裙摆褶皱，网格拓扑可模拟 | Cloth 低模代理 + 表面传递到展示裙摆；腰部固定、身体代理 Collision | 裙摆网格边界、层间厚度、低模绑定映射 |
| 已有完整裙骨、要求 UE 与 Web 共用动画 | 优先裙骨驱动 / 受限次级运动，烘焙骨骼；接受褶皱细节有限 | 每角色骨链、裙摆权重与动作范围 |
| 用 MMD Tools / 插件刚体转布料 | 先核实所装插件是否提供并支持该功能，再对副本试验 | 不将未验证操作器列作可直接执行步骤 |
| 场景道具掉落或碰撞 | Rigid Body，仅道具与代理体 | 不把整片裙子直接当一个刚体 |

本轮建议：风堇先验证头发链；遐蝶裙摆使用 Cloth 小样对照，是否转为骨骼版由 UE/Web 性能与视觉结果决定。两种版本不要同时在同一裙摆上叠加求解。

### 4.2 Cloth 最小测试配置

依据：[Shape / Pin Group](https://docs.blender.org/manual/en/4.5/physics/cloth/settings/shape.html)、[Cloth 碰撞说明](https://docs.blender.org/manual/en/4.1/physics/cloth/settings/collisions.html)（碰撞原理参考，执行时核对当前版本属性）。

单位米、24 fps、重力 (0,0,-9.81)。全部以下为 **项目暂定，不是教程数值或通用布料常量**：

- 在代理副本确认统一缩放，不盲目对已绑定原角色 Ctrl-A；腰线 Pin Group 权重 1，向下两圈渐变到 0。先查现有形态键与修改器兼容性。
- 修改器拟为 Armature（驱动固定区域）→ Cloth → Surface/Subdivision（仅显示）；不得将厚 Solidify 外壳送入布料自碰撞。是否使用 Dynamic Mesh 要看目标是否存在拉伸变形，初测关闭。
- `quality=8`、碰撞质量=4；身体代理开 Collision，布料 Object Collision 开启；`distance_min=0.005 m`、自碰撞距离 0.004 m、代理外厚度 0.003 m。紧贴层间先检查净空，大距离会悬浮，小距离会漏碰。
- 无可靠布料/网格密度依据时，mass、拉伸/压缩/剪切/弯曲刚度保留当前版本 Cotton 预设读取值，并在首轮报告中逐项记录；**当前暂不编造一组质量或刚度数**。未记录预设实值前不发布“可复现最终参数”。
- 预滚 24 帧，测试 60 帧；先在站立小样验证，再测坐姿与起身。评估腰部漂移、裙摆与腿/座椅距离、交叠与振荡，不用“有 Collision”代替检测。

### 4.3 刚体稳定性

依据：[RigidBodyWorld API](https://docs.blender.org/api/current/bpy.types.RigidBodyWorld.html)。API 当前文档的 `substeps_per_frame` 和 `solver_iterations` 默认均为 10；执行时仍需读取本机版本。

项目提案：普通场景 substeps=10、iterations=20；高速测试 substeps=40（候选 30–50）、iterations=20（候选 10–20）。统一缩放只作用于道具副本；静态碰撞代理设 Passive。
碰撞 margin 按最薄碰撞尺寸 d 计算：`min(0.005 m, 0.1*d)`，不得超过该尺寸十分之一；为每个道具报告实际值。这是项目经验起点，不是视频参数，薄片需要更细代理与更小边距。增加步数不能补救错误尺度或初始互穿。

### 4.4 跨引擎烘焙边界

骨骼约束/刚体驱动骨骼：烘焙视觉关键帧并导出 FBX/GLB。直接 Cloth 顶点模拟不能仅点“烘焙”就自动成为骨骼动画，不能假设 FBX 保留任意布料缓存。
UE 电影展示候选：Alembic → Geometry Cache → Sequencer，见 [Epic Geometry Cache 文档](https://dev.epicgames.com/documentation/unreal-engine/cinematic-geometry-cache-track-in-unreal-engine)。Web 不默认支持相同缓存，需离线转骨骼/可控形态键或使用简化循环；具体选择待缓存体积测试。

## 5. 教室比例、材质与光照

教程关联：[T5 天空之城全流程](https://www.bilibili.com/video/BV1i9JyzXEyU/)（简介为 Blender 4.5）、[T6 卡通教室课程](https://www.bilibili.com/video/BV1ku411Z7oe/)（目录包括桌椅、结构、道具、窗、贴图、书、窗帘与合成）。布尔设置、渐变节点和具体灯光数值 **待用户补充时间戳/讲义**；下表是项目尺寸基准，不冒充教程测量值。

### 5.1 比例与搭建顺序

现有场景外壳脚本约宽 15.5 m、深 14.8 m、顶高 4.6 m；角色目标高度 1.57–1.84 m。这是本地脚本读取得到的基线，不是符合人体工学的认证。

| 项目 | 暂定基准 | 来源与待确认 |
| --- | --- | --- |
| 座高 | 保留现有 0.48 m；坐面深 0.44–0.48 m、宽 0.48–0.54 m | 本地坐姿基线 + 项目提案；需逐角色量大腿、脚掌接触 |
| 桌面 | 高 0.76 m，宽 0.70 m，深 0.50 m，厚 0.025 m | 项目提案；现有手腕与书本接触需联动调整，不能只降桌面 |
| 桌下净空 | 不少于 0.66 m 高，腿部后方避免横杆 | 项目提案；用实际坐姿几何验收 |
| 通道 | 主通道 1.00–1.20 m，玩家碰撞半径基线 0.24 m | 项目提案；同时检验衣摆外扩及相机不穿桌 |
| 讲台 | 保留现有 0.18 m 高的基线，老师路线保持可走净空 | 本地基线；布尔与阶梯变更须重查路径 |
| 教室主体 | 首轮不整体缩放外壳，以家具与人物比例为优先 | 当前关卡依赖既有坐标，整体变更须单独确认 |

顺序：参考测量 → 桌椅灰模 → 教室主体与门窗 → 结构倒角/布尔 → 材质分组 → 书本公告栏与窗帘 → 灯光。大型布尔使用 Simple/Exact 的选择依实际重叠情况测试；只在副本应用，检查薄面、法线和材质 ID。不要把任意布尔模式称为天空之城视频原步骤。

木材、羊皮纸、墙面、绿板、金属细饰、玻璃/窗景分别分组。渐变拟由 Texture Coordinate.Object → Mapping → Gradient Texture.LINEAR → ColorRamp → 固有色混合；先以局部尺度校准。木质与羊皮纸保留粗糙度差异，初测木材 0.65、纸 0.85，渐变混合 0.12；均为待确认项目值。云与树先用自制简化资产，不下载作者未授权模型。

### 5.2 可对照的光照方案

项目暂定：左侧窗为主光，主光对地俯角约 35°，暖色 Sun energy=2.0（Blender Sun 的软件强度值，不当作场景 lux）；Sun angle=5°；大面 Area Fill 相对主光画面亮度约 25%，偏中性冷色，World strength=0.2。Area 的绝对功率取决于面积和距离，待首个固定曝光灰模测光后记录，不猜一个通用瓦数。

前述 0 EV / AgX 作为 Blender 对照基线；皮肤高光不大面积截白，衣料暗部保留色相。局部暖光服务木质/羊皮纸，绿色环境光不直接把皮肤染绿。初测不加体积雾；窗光层次通过几何遮挡与阴影实现，辉光按 2.5 节低强度候选。UE 需固定曝光独立配光，不能把 Blender energy 值直接复制为 UE 灯光单位。

## 6. UE5 对应方案与确认关卡

本轮只有规格，不创建 `ue5/tech_notes.md`；进入用户批准的 UE 阶段时，将以下方案与实测差异写入该文件。

- Shader to RGB、Blender ColorRamp 节点树不直接通过 FBX/glTF 还原。保留固有色、透明遮罩、法线与材质 ID；UE 用自己的分段明暗材质函数/渲染方案重建。
- 第一位角色先做展示 Actor，固定光照/相机，与 Blender 基础三阶、描边和轮廓光逐项对照。静态烘焙颜色可作美术目标图，不能冒充可随灯光移动的实时明暗。
- 单纯 Unlit 接收不到常规动态漫反射；若采用 Unlit + 显式主光方向参数近似分段，只适用于受控展示，遮挡阴影要另定义。全局后处理会影响背景，不能无测试承诺精确皮肤分组；最终方案需用户在单角色预览后选择。
- 自习室只用静态或轻量已烘焙循环，实时头发/裙摆求解关闭；不新增对话、考核或自动镜头打扰。
- 确认顺序：本规格 → 那刻夏单角色材质对照 → 风堇单链60帧 → 裙摆小样 → 教室主体 → 光照 → 角色站位 → 摄像机轨道 → Web 事件接口。每一步需展示结果并确认后再进入下一步，不将本次规格确认扩展为以后所有阶段的自动授权。

## 7. 本轮请确认的决定

1. “23 色块”按 **3 色阶**解释，阈值 0.45 / 0.65，是否接受为初测起点？
2. 描边采用 **2 毫米**，而不是未注明单位的 0.02；是否接受？
3. 边缘光初测关闭皮肤，仅头发/衣料强度 0.08；是否接受？
4. Damped Track Influence=0.35、局部弯曲 ±12°/扭转 ±5°、外扩 8 毫米；独立目标二阶跟随 3 Hz / 阻尼比 0.85；是否接受为风堇单链测试起点？
5. 桌面 0.76 米需与手腕接触一起测试，坐高先保留 0.48 米；是否接受？

这些值均为可调提案，未从不可读取的视频部分编造来源。没有用户确认前，不执行任何资产操作。
