# 素材来源与版权说明

本项目的**代码、课程文本、剧情、界面设计**由作者（Lauvi61）原创，以 MIT 许可发布（见 [LICENSE](LICENSE)）。

下面这些不是原创内容，单独说明。

---

## 角色 3D 模型

`blender/animated/` 下的四个模型：

| 文件 | 角色 | 出处 |
|---|---|---|
| `anaxa.glb` | 那刻夏 | 《崩坏：星穹铁道》 |
| `hyacine.glb` | 风堇 | 《崩坏：星穹铁道》 |
| `castor.glb` | 遐蝶 | 《崩坏：星穹铁道》 |
| `phainon.glb` | 白厄 | 《崩坏：星穹铁道》 |

- **角色形象与设定**：版权归 miHoYo / HoYoverse 所有
- **模型文件**：由公开模型站获取，原作者标注为「崩坏：星穹铁道」，经本地 Blender 转换与骨骼修复后用于本项目
- **使用范围**：仅用于同人二创、非商业用途

米哈游对同人创作持开放态度，本项目按此惯例使用，并在此标明来源。若权利方认为不妥，请联系删除，我会立即移除相关文件。

**替换说明**：这四个模型是可选资源。想换成自己的角色，把同名 `.glb` 放进 `blender/generated/` 即可；不放也能跑，只是 3D 课堂里没人。

---

## 角色立绘与背景

- `assets/portraits/`、`assets/bg_*.jpg` —— 同上，源自《崩坏：星穹铁道》同人创作，版权归原权利方

---

## 词库来源

`data/vocabulary/cet4-core.json` 的词条、音标、释义，编译自一本公开出版的四级词汇书。

**该书本身不随本仓库分发**（`cet4-core-source.pdf` 已被 `.gitignore` 排除）。仓库里只有从它整理出的结构化词条数据。

「原图溯源」功能需要原书 PDF 才能工作。想用这个功能，请自行准备合法取得的 PDF，放到 `data/vocabulary/cet4-core-source.pdf`。

---

## 第三方库

- [Three.js](https://threejs.org/) —— MIT
- [FastAPI](https://fastapi.tiangolo.com/) / [Uvicorn](https://www.uvicorn.org/) —— MIT / BSD
- [PyMuPDF](https://pymupdf.readthedocs.io/) —— AGPL（仅在本地运行，不提供服务端分发）
