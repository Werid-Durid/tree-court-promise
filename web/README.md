# 树庭之约 · 网站 MVP

**已升级为浏览器 3D 课堂，并生成 UE5 场景工程。** 最新说明见 `../docs/3D课堂升级.md`。四人 GLB 来源于本地 Blender 转换，教师／助教／同学身份已更新；已有学习存档与关系规则保留。

阶段一交付：四级英语第一章（12 个知识点、四位角色）、课程与章节入口、打字机对白、联想线索、记忆钩子、角色好感与关系状态、本地存档、SQLite API、资料上传队列。另提供基础自习计时器；它不代表阶段四的 UE5 自习场景已经完成。

## 启动

Windows 双击项目根目录的 `启动树庭网站.bat`。或者在根目录运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File web/start.ps1
```

首次需要 Python 3.10+、pip 和网络以安装依赖；之后使用 `web/.venv`。打开 <http://127.0.0.1:8765>，保持终端开启，Ctrl+C 停止。

手动启动：

```powershell
py -3 -m venv web/.venv
web/.venv/Scripts/python.exe -m pip install -r web/requirements.lock.txt
web/.venv/Scripts/python.exe -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8765
```

API 文档：<http://127.0.0.1:8765/docs>。端口占用时可给启动脚本传 `-Port 8766`。默认仅接受本机访问；移动端适配指响应式网页，跨设备接入与身份认证不在阶段一范围内。

## 使用

- 从课程表进入四级英语首章。其余六门科目显示真实的“筹备中”状态。
- 每次选择后都有解释、例句和记忆钩子，不显示冰冷的正确／错误弹窗。
- 每个知识点首次作答匹配时，当前角色好感 +4；未匹配不扣分。重温与重复提交不刷好感。
- 刷新恢复当前词笺和反馈。已完成的词会留在“修习手札”，可单独重温或回顾待巩固的词。
- 好感 30/60/85 开放学术支线。达到 85 且完成章节后，用户可主动选择恋爱或好友路线。好友路线不扣分、不影响课程与帮助、不重复邀请。首章每人仅负责 3 个词，最多各 +12，后续课程才能自然推进到高阈值；无需降低阈值提前触发。
- 自习室支持正向计时、25 分钟计时、低音量合成环境声、暂停和退出。切出页面自动暂停并记录中断，不把后台时间算作专注。意外关闭后可保存最后一次已计时片段。
- 资料支持 10 MB 内 PDF/TXT/Markdown，文本要求 UTF-8。PDF 最多 100 页；扫描件标记待 OCR。当前仅保存原件和提取文本、进入待编译队列，不自动发布课程或宣称已生成知识点。

## 存档和隐私边界

浏览器 `treecourt.web.v1` 保存匿名档案 ID、事件和同步状态。SQLite 保存于 `data/runtime/treecourt.sqlite3`；资料原件和提取文本保存于 `data/runtime/materials/`。浏览器档案 ID 相当于本地访问凭据，导出文件也包含它，请妥善保管。

服务器从学习事件计算好感和关系，使用唯一事件 ID 去重，拒绝不满足条件的关系变更。失去服务器连接时先保存在 localStorage，服务恢复后同步。首次加载需要本地服务；这不是离线安装型 PWA。

阅读设置、修习手札均可导出 JSON 作为备份；当前尚未实现导入界面。清除浏览器数据会生成新档案，旧 SQLite 数据不会自动关联到新档案。备份时应同时保留导出手札及整个 `data/runtime/`，停止服务后再复制数据库。

本地匿名档案不等于线上账户系统。线上部署前需要补充账户认证、文件处理隔离、配额与数据库迁移。

## 模块

```text
web/backend/app.py       FastAPI、上传与静态文件边界
web/backend/domain.py    事件校验、好感、章节和关系规则
web/backend/storage.py   SQLite 仓储
web/frontend/state.js    浏览器事件归约器
web/frontend/app.js      路由、对话、存档、资料和基础自习
web/frontend/styles.css 桌面／移动端样式
data/curriculum/         审核后发布的课程
data/teaching-policy.json 教学与关系参数
```

推荐接口返回 `baseline-v1`，只建议首章和最近待巩固词；阶段五的间隔复习、错选类型分析与个性化配额尚未实现。

## 验证与打包

根目录运行：

```powershell
web/.venv/Scripts/python.exe -m unittest discover -s web/tests -v
node --test web/tests/state.test.mjs
powershell -NoProfile -ExecutionPolicy Bypass -File web/package.ps1
```

如需重跑浏览器验收，先启动本地服务，再运行 `node web/tests/browser-smoke.mjs`；需要已安装 Playwright、Edge 和 Node.js。脚本默认使用 Codex 的本地浏览器依赖目录，也可通过 `TREECOURT_NODE_MODULES` 指定你的 `node_modules` 路径。测试使用独立浏览器档案。

压缩包输出至 `web/artifacts/`，包含网站源码、依赖锁、课程、现有图像与集成说明；不包含虚拟环境、私人存档、上传资料和 3D 模型，首次启动安装依赖。现有图像沿用本地同人项目素材，发布或分发前应查看原模型与图片附带的使用说明。

## UE5 状态

四人动画邀约与可选一人陪学的自习室，制作说明及验收方法见 [四人动画与自习室](../docs/四人动画与自习室.md)。课堂椅子的连接结构已单独修复，并同步至网页与 UE5 课堂。

已生成 UE 工程与四人角色资产。`/api/stage/events` 使用固定组件白名单同步黑板，实际执行成功才返回 true。浏览器支持独立 3D，无需 UE 运行。Blender／Unreal MCP 尚未连接，本轮通过可复现后台脚本执行。完整游戏内答题 UI 和免编辑器 EXE 尚未交付。
