# 组件选型目录（GitHub 已核实）

> star 数为 2026-11-11 检索结果，仅作活跃度参考；接入前仍需读 README 与 License。
> 原则：**能用现成的就不自己写；能 vendor 化就不引构建链；能在浏览器跑就不上 GPU 服务。**

## 1. 渲染与后期

| 组件 | star | 能力 | 接入方式 | 注意 |
|---|---|---|---|---|
| `mrdoob/three.js` | — | 引擎本体 | vendor `three.module.js` + `three.core.js` | 固定版本，不要 CDN |
| `pmndrs/postprocessing` | 2970 | Bloom / SSAO / DOF / LUT / 色差 / Noise / SMAA / GodRays | `EffectComposer` + `EffectPass` | `frameBufferType: HalfFloatType`；`renderer.toneMapping = NoToneMapping` |
| `N8python/n8ao` | 504 | 时间稳定 SSAO | `N8AOPass` | 集显可半分辨率 |
| `gkjohnson/three-gpu-pathtracer` | 2045 | 浏览器光追（离线关键帧） | BVH + `WebGLPathTracer` | 不能实时，用于出静帧 |
| `yomotsu/camera-controls` | 2450 | 平滑运镜/过渡 | `CameraControls` | 适合预演，成片仍建议关键帧插值 |
| `Alchemist0823/three.quarks` | 1197 | 粒子/VFX 引擎 + 编辑器 | `ParticleSystem` | 纹理图集可复用 |
| `gkjohnson/three-mesh-bvh` | 3566 | 射线/空间查询/遮挡 | `computeBoundsTree()` | 相机防穿模、地形吸附 |
| `gkjohnson/three-bvh-csg` | 962 | 布尔运算 | `Evaluator` | 开洞/切割，注意面数增长 |

## 2. 人物与表演

| 组件 | star | 能力 | 接入方式 | 注意 |
|---|---|---|---|---|
| `pixiv/three-vrm` | 2280 | VRM 加载/骨骼/表情/lookAt | `GLTFLoader` + `VRMLoaderPlugin` | VRM 即 glTF 扩展；自带 Humanoid |
| `met4citizen/TalkingHead` | 1670 | 实时口型 + 全身数字人 | 独立 JS 类 | 集成快，样式需改造 |
| `met4citizen/HeadTTS` | 184 | 浏览器内神经 TTS + viseme | WebGPU/WASM 或本地服务 | 模型体积需评估 |
| `DanielSWolf/rhubarb-lip-sync` | 2760 | 音频 → viseme 时间轴 | CLI 预处理 | 最稳，离线可批量 |
| `Bingeljell/image-to-3dlab` | 1164 | 图/文 → 带贴图 + 自动绑定 + 21 动作 | 本地 Python | 需 Apple Silicon / NVIDIA |
| `microsoft/TRELLIS` / `TRELLIS.2` | 14242 / 12824 | 图/文 → 3D | 本地 GPU | 需重拓扑与绑定 |
| `Tencent-Hunyuan/Hunyuan3D-2.1` | 4413 | 图/文 → 3D + PBR | 本地 GPU | 材质质量较好 |
| `DepthAnything/Depth-Anything-V2` | 9136 | 单目深度 | Python 推理 | 用于 2.5D 视差层 |
| `tencent-ailab/IP-Adapter` | 6713 | 参考图一致性 | Diffusion 管线 | 角色三视图 → 各镜同人 |

## 3. 资产与压缩

| 组件 | star | 能力 | 接入方式 | 注意 |
|---|---|---|---|---|
| `Poly-Haven/Public-API` | 64 | CC0 HDRI/贴图/模型 API | HTTP | 1k 够用，2k 做主光 |
| `agmmnn/polydown` | 109 | Poly Haven 批量下载 | CLI | 注意带宽与体积 |
| `kanaworksai-hue/sozai-search-mcp` | 45 | 让 agent 搜 ~36000 个 CC0 资产 | MCP | 需核对许可与尺度 |
| `donmccurdy/glTF-Transform` | 2070 | Draco / KTX2 / meshopt / 量化 | Node CLI/SDK | 纹理务必 KTX2 |
| `zeux/meshoptimizer` | 8831 | 网格简化 / gltfpack | CLI | LOD 与压缩一起做 |

## 4. 物理 / 时间轴 / 导出

| 组件 | star | 能力 | 接入方式 | 注意 |
|---|---|---|---|---|
| `dimforge/rapier` | 6058 | 3D 物理（刚体/碰撞/布料） | `@dimforge/rapier3d` WASM | 布料可做旗帜/衣物 |
| `theatre-js/theatre` | 12975 | 运动设计编辑器 + 时间轴 | `@theatre/core` | 可视化调参，导出 JSON 后仍走纯函数 |
| `Vanilagy/mp4-muxer` | 618 | WebCodecs 封装 MP4 | `Muxer` + `VideoEncoder` | 码率 ≥12Mbps，音频 AAC |
| `Breakthrough/PySceneDetect` | 5431 | 镜头切分 | CLI | 用于成片切点自检 |
| `supergeniodelmale/Cinemetrica` | 21 | 电影镜长/切点统计 | Python | 校准节奏曲线 |

## 5. 生产流程参考（方法论，不是依赖）

| 项目 | star | 可借鉴 |
|---|---|---|
| `HBAI-Ltd/Toonflow-app` | 21435 | 无限画布 + 3D 导演台预演 + 多参考视频生成；2 分钟成片成本量级 |
| `waooAI/waoowaoo` | 14837 | 工业级全流程影视生产 |
| `Narcooo/inkos` | 11116 | 小说→剧本→分镜→互动的 Agent 链 |
| `dramaclaw/dramaclaw` | 7676 | 剧本到成片流水线（含 TTS） |
| `Forget-C/Jellyfish` | 7168 | 分镜状态机（信息确认 / 运行时 / 就绪度三分） |
| `zenstory-ai/drama-skills` | 4098 | 每镜唯一职责、连续性锁、对白估时 |
| `zenstory-ai/novel-to-game` | 1003 | ART_DIRECTION、六项实机验收 |
| `SkyeShark/eidoverse-video` | 118 | 纹素密度归一 + 风化层、lipsync.py、默认增强顺序 |

## 6. 选型决策树

```
要不要真实感？
├─ 要 → 有 GPU/时间？ 
│        ├─ 有 → 图生 3D（TRELLIS/Hunyuan3D）+ 重拓扑 + 绑定
│        └─ 没有 → CC0 资产（Poly Haven）+ PBR 套图 + HDRI
└─ 不要（风格化）→ 程序化几何 + 固定色板 + 少量贴图

人物要不要说话？
├─ 要 → VRM + viseme（rhubarb 离线 / HeadTTS 在线）
└─ 不要 → CC0/程序化 + 二次动作

要不要导出 MP4？
├─ 要 → WebCodecs + mp4-muxer（精确）
└─ 只要网页 → MediaRecorder 即可
```

## 7. 许可与合规

- CC0（Poly Haven / Kenney / Quaternius）可商用，仍需在 `assets/CREDITS.md` 登记来源。
- VRM 模型注意作者授权（CC-BY 需署名；禁止二次分发需遵守）。
- 生成模型（TRELLIS/Hunyuan3D/HunyuanVideo）输出许可随模型，商用前核对。
- 音乐/音效：优先自制或 CC0；商用曲库需授权。

## 8. 可复用零件：ohmygame（本地仓库）

若机器上有 `ohmygame`（WhiteTowerAI/ohmygame，Apache-2.0），以下零件可直接抄结构或 vendor：

| 零件 | 路径 | 拿来干什么 |
|---|---|---|
| 多尺度细节契约 | `plugins/threejs-world/skills/threejs-world/references/world-contract.md` | 世界/中/近三层细节标准、细节分布、审查视图 |
| 资产 7 步 | `plugins/web-game-studio/skills/web-3d-asset-pipeline/SKILL.md` | 规范化（单位/轴向/pivot/命名）、asset key、碰撞代理 |
| 分级验收 | `plugins/web-game-studio/skills/game-playtest/SKILL.md` | smoke / feature / regression / visual / performance |
| Three 架构边界 | `plugins/web-game-studio/skills/three-webgl-game/SKILL.md` | 场景图只是渲染适配器；相机模式含 authored cuts |
| 音频 ducking | `src/shared/playable-audio.ts` | 音乐降到 0.25、0.4s 淡出；首次手势启动 |
| 沙箱 CSP | `src/shared/playable-sandbox.ts` | `default-src 'none'` + `sandbox="allow-scripts"` 播放器壳 |
| 视频转码/裁剪 | `src/renderer/video-trim.ts`（mediabunny） | `Input+BlobSource → Conversion → Output(Mp4/WebM)`，`CanvasSink` 取帧 |
| 资产台账 | `src/daemon/asset-library.ts` | origin / purpose / derivedFrom / model3d / sourceKey |
| 运行参数 | `src/story-web/runtime.ts` | `?silent=1`、`?playtest=1`、`?scene=` 直达 |
| 依赖 | `node_modules/mediabunny`(1.61.3)、`@gltf-transform/core`(4.5.1)、`sharp`(0.35.5)、`three`(0.172.0) | 可直接 vendor |

不要搬：Electron 主进程、Supabase 云、canvas 无限画板、小游戏插件——与叙事成片无关。

## 9. MCP 生成工具（ohmygame-studio）

若在 ohmygame 环境里工作，资产生产可走它已配置好的 provider，不必自己接 API：

| 工具 | 用途 |
|---|---|
| `generate_image` | 概念图 / 角色三视图 / 关键帧 |
| `generate_3d_asset` | **图 → 3D**（传 `imagePath`，先出图再 3D） |
| `animate_3d_asset` | 3D 资产绑定动画 |
| `generate_video` | 逐镜视频 / 奇观镜动态层 |
| `generate_speech` | 配音（与 rhubarb/HeadTTS 口型对接） |
| `generate_sound_effect` / `generate_music` | 拟音 / 配乐 |
| `wait_job` / `get_job` / `cancel_job` | 异步任务（>45s 返回 job id，勿重复提交） |
| `game_use` | 真实窗口试玩与截图（验收证据） |
| `canvas_check` | 改 `canvas/` 后校验 |

推荐链路：`generate_image`（三视图）→ `generate_3d_asset` → `animate_3d_asset` → `generate_speech` → rhubarb viseme → `game_use` 验收。
