---
name: novel-to-threejs-cinematic
description: 把小说、剧本、大纲或分镜稿，制作成电影级 Three.js 3D 叙事成片（浏览器实时播放 + 可导出 MP4）：故事工程、视觉开发、资产生产（图生 3D / 自动重拓扑 / PBR 纹理 / 自动绑定 / 动作重定向）、神经配音与口型、电影级分镜与调度、纯函数时间轴、质量门。适用于「小说转 3D 动画 / 电影级分镜 / 短剧 / 逼真场景 / 人物表演 / three.js 叙事 / 图生 3D / 自动绑定 / 自动配音 / 逐帧渲染 / 成片导出」等请求，题材不限。
license: MIT
---

# 小说 / 剧本 → 电影级 Three.js 叙事（v1.1）

把文字变成**能播、能导出、经得起特写**的 3D 成片。本 skill 与具体故事无关：任何题材、任何长度都走同一套流程，只换参数与资产。

## 0. 什么叫"完成"

一份交付必须同时满足：

1. **能播**：浏览器打开即播，可暂停/拖动/逐帧，字幕与配音同步。
2. **能导出**：一键产出 MP4（H.264/AAC），可离线播放。
3. **能复现**：任意 `t` 的画面可由 `computeState(t)` 重建，拖动进度不漂移。
4. **经得起看**：每个镜头的景别不超过其资产等级允许的上限（见 §2）；特写 1m 内有三层材质细节；人物有二次动作与口型。
5. **能核对**：分镜卡、信息释放表、资产台账、拟音事件表、响度报告齐全。

## 1. 五条铁律

1. **一致性靠资产锁定 + 纯函数时间轴**：角色/场景只加载一次；每帧从 `t` 重算全部状态，不用 `update(dt)` 累积。
2. **资产决定画幅**：能用多大画幅，由资产等级（T0–T3）决定，不由导演愿望决定。弱资产给大特写，是成本最低的翻车方式。
3. **表演 > 面部 > 骨骼 > 模型精度**：真实感的第一来源是"像个在场的人"，不是面数。
4. **声音与画面同源**：配音实测时长驱动字幕与镜头窗；拟音事件与画面动作同帧（±2 帧）。
5. **场景图只是渲染适配器**：规则、状态、时间轴都在 Three 对象之外；电影叙事一律用 authored cuts。

## 2. 资产等级 T0–T3（先定级，再做片）

所有资产（角色 / 场景 / 道具 / 纹理 / 配音）都打一个等级。**等级决定它能出现在什么画幅里**。

| 等级 | 名称 | 典型来源 | 允许的最大画幅 | 禁止 |
|---|---|---|---|---|
| **T0** | blocking | 程序化基本体、灰盒、色块 | 仅 previz / 内部审片 | **不得进成片** |
| **T1** | stylized | CC0 低模（Kenney/Quaternius/KayKit）、风格化 VRM | MS（腰以上） | CU / ECU / 85mm 特写 |
| **T2** | production | VRM/glTF 人形 + Mixamo、图生 3D + 自动重拓扑 + 自动绑定 | MCU（胸以上） | ECU、真实人脸大特写 |
| **T3** | hero | 定制雕刻/扫描、4K 皮肤、15+ blendshape、手工或 UniRig 精绑 | CU / ECU / 任何焦段 | — |

**硬规则（校验器会拦）**

```text
shot.shotSize ∈ {CU, ECU}       → 该镜所有角色资产 tier 必须 = T3
shot.lens ≥ 85                   → 主体（角色或关键道具）tier ≥ T2
character.model = "procedural"   → 仅当 quality.lock 明示 allowProceduralHero=true，否则 build error
配音 = 系统 TTS（say/espeak）     → 仅 prototype 档；production 档 build error
贴图 < 2K（主体 1m 内可见）       → review warning；< 1K 为 build error
```

等级不是"越高越好"，是**成本分配工具**：把 T3 预算集中在 2–3 个 hero 镜头，其余用 T2/T1 的剪影、背影、物件、环境承担叙事。

## 3. 生产流程（八阶段，每阶段有交付物与门）

| 阶段 | 输入 | 产出 | 完成标准 |
|---|---|---|---|
| **S0 故事工程** | 原文/大纲 | beat sheet、信息释放表、张力曲线、伏笔三处表 | 每场有戏剧功能；观众知情时机可核对 |
| **S1 视觉开发** | S0 + 参考 | Look Dev 板：色板、材质语言、镜头语言、LUT、参考帧 + **资产等级预算表** | 一句话说清"像什么"；每个角色/场景已定 T 级 |
| **S2 资产计划** | S1 | `design/asset-plan.json`：每个资产的等级/来源/尺寸/面数/纹理/绑定/许可 | 每个资产有 ID、tier、route、license、验收阈值 |
| **S3 资产生产** | S2 | `assets/` 实体文件 + `assets/manifest.json` + `assets/CREDITS.md` | `validate_assets.py` 全绿；无 T0 资产进成片 |
| **S4 分镜与调度** | S0/S1/S3 | 分镜卡（景别/焦段/机位/轴线/走位/覆盖/cutReason） | 每镜唯一职责；轴线零违规；**画幅不超资产等级** |
| **S5 装配** | S3/S4 | 场景装配、光照、大气、人物、时间轴、字幕 | `computeState(t)` 全绿；音频全部加载 |
| **S6 渲染导出** | S5 | 实时播放器 + MP4 + SRT + 响度报告 | 成片可离线播；-14 LUFS |
| **S7 验收** | 全部 | 验收记录 + 关键帧证据 | 技术门 + 叙事门 + 资产门全绿 |

> S2/S3 是 v1.1 新增的**独立阶段**。跳过它们，S5 就只能用程序化占位资产，成片必崩。

## 4. Agent 执行协议（只给文本，Agent 自己跑完全程）

每个阶段 Agent 的动作、禁止项与出口命令。**不允许跳阶段，不允许用"占位资产先跑通"作为交付理由。**

| 阶段 | Agent 必须做 | Agent 禁止 | 出口校验 |
|---|---|---|---|
| S0 | 写 `design/00-story.md`；填信息释放表 | 用旁白代替画面事件 | 每场有目标/障碍/转折 |
| S1 | 写 `01-look-dev.md`；给每个资产定 T 级 | 给全部角色定 T3（预算失控） | 等级预算表覆盖所有资产 |
| S2 | 写 `asset-plan.json`（schema 见 `templates/project/asset-plan.schema.json`） | 手写下载链接而不写 license | schema 校验通过 |
| S3 | 跑 `build_assets.py` → 归一化 → 压缩 → `validate_assets.py` | 把 T0 资产标成 T2 | `validate_assets.py` error=0 |
| S4 | 写分镜卡；跑 `validate_shots.py` | CU/ECU 配 T2 以下资产 | error=0，warning 逐条判断 |
| S5 | 装配、绑定、口型、混音 | 用 `say` 交 production 档 | 首屏可播；seek 不漂 |
| S6 | 导出 MP4 + SRT + 响度报告 | 用录屏代替逐帧编码 | 离线可播；-14 LUFS |
| S7 | 截图证据 + 验收记录 | 用单张远景宣称完成 | 技术/叙事/资产三门全绿 |

**Agent 决策顺序（遇到不确定时按此顺序选）**

```text
1. 先问：这个镜头必须看清脸吗？
   ├─ 必须 → 该角色必须 T3；否则改分镜（背影/手/物件/剪影）
   └─ 不必 → T1/T2 即可
2. 再问：本机有 NVIDIA GPU 吗？
   ├─ 有 → 本地图生 3D + 本地绑定（路线 B）
   └─ 没有 → 托管 API（fal/Replicate，路线 C）或纯 CC0 + VRM（路线 A）
3. 最后问：预算按次还是按时？
   ├─ 按次 → 托管 API（只对 hero 资产付费）
   └─ 按时 → 本地 GPU / 自建 ComfyUI
```

## 5. 资产生产路线（三选一，可混用）

| 路线 | 适用 | 角色 | 场景/道具 | 纹理 | 成本 |
|---|---|---|---|---|---|
| **A 零 GPU** | 快速交付、风格化、群像 | VRM（VRoid / Ready Player Me）或 CC0 人形 + Mixamo | Poly Haven / Kenney / Quaternius CC0 | Poly Haven / ambientCG 4K | 0 |
| **B 本地 GPU** | 写实主角、独特造型 | 文生图 → 图生 3D（TRELLIS.2 / Hunyuan3D-2.1）→ 重拓扑 → UniRig → Mixamo | 图生 3D + PBR 投影 | Hunyuan3D-Paint / Paint3D / Material Maker | 电费 + 24GB 显存 |
| **C 托管 API** | 无 GPU 但要 T3 | 同上，走 fal / Replicate 托管 | 同上 | 同上 | 按次付费 |

细节、命令、显存、许可见 `references/asset-pipeline.md`。

**人脸特写的现实约束**：低预算实时 Three.js 很难做到"像真人"。若剧本要求真实人脸大特写，用**混合方案**：Three.js 出场景/道具/运镜/previz，人脸特写走图生视频（Wan-S2V / 商业视频模型）后期合成。不要用 T2 资产硬顶 ECU。

## 6. 技术栈选型（详见 `references/component-catalog.md`）

| 层 | 首选 | 备选 |
|---|---|---|
| 引擎 | three.js（vendor 化，无构建） | Babylon.js |
| 色彩/后期 | `pmndrs/postprocessing` + ACES/AgX + 一支 LUT | three 原生 composer |
| 环境光 | `PMREMGenerator` + Poly Haven CC0 HDRI（主光 2K+） | 程序化天空 |
| 材质 | `MeshPhysicalMaterial`（clearcoat/transmission/sheen） | `MeshStandardMaterial` |
| AO/反射 | `N8python/n8ao` + SSR | SSAOEffect |
| 人物 | glTF/VRM 人形 + Mixamo 重定向 | `pixiv/three-vrm`（VRM 资产时） |
| 图生 3D | `microsoft/TRELLIS.2` | `Tencent-Hunyuan/Hunyuan3D-2.1` |
| 自动绑定 | `VAST-AI-Research/UniRig` | Mixamo / AccuRIG |
| 重拓扑 | `wjakob/instant-meshes` + Blender | `cnr-isti-vclab/meshlab` |
| 口型 | `rhubarb-lip-sync`（离线）/ `HeadTTS`（浏览器） | `TalkingHead` |
| 配音 | IndexTTS 2.5 / CosyVoice 3（神经、零样本音色） | `edge-tts`（免费兜底） |
| 动作/物理 | `dimforge/rapier` | cannon-es |
| 粒子/VFX | `Alchemist0823/three.quarks` | 自写 Points |
| 时间轴 | 自写 `computeState(t)` + `theatre-js/theatre`（调参） | GSAP |
| 空间查询 | `gkjohnson/three-mesh-bvh` | 手写包围盒 |
| 离线光追 | `gkjohnson/three-gpu-pathtracer`（hero 静帧） | Blender Cycles |
| 压缩 | `donmccurdy/glTF-Transform` + `zeux/meshoptimizer` + KTX2 | gltfpack |
| 导出 | WebCodecs + `Vanilagy/mp4-muxer` | `mediabunny` |

## 7. 通用项目结构

```
<project>/
  design/
    00-story.md            故事工程：beat sheet / 信息释放表 / 张力曲线
    01-look-dev.md         视觉开发：色板 / 材质语言 / 镜头语言 / LUT / 资产等级预算
    02-characters.md       角色：ID / 等级 / 三视图 / 骨骼 / 表情 / 口型
    03-locations.md        场景：ID / 等级 / 尺寸 / 光照 / 大气 / 材质
    04-props.md            道具：ID / 等级 / 线索链（埋-强化-回收）
    05-shots.md            分镜卡
    06-sound.md            配音 / 拟音事件表 / 环境三层 / 音乐 spotting
    07-qa.md               验收记录
    asset-plan.json        资产生产计划（S2 的唯一输入）
    story.json             数据契约（S4 之后）
  assets/
    models/  textures/  hdri/  audio/  visemes/  subtitles/
    manifest.json          资产台账（build_assets 生成，validate_assets 校验）
    CREDITS.md             来源 + 许可
  src/
    story.js               由构建脚本生成的唯一数据源
    timeline.js            computeState(t) 纯函数
    world.js               场景装配与 apply(t, state)
    character.js           角色/动画/口型
    audio.js               配音调度 + 环境音
    main.js                播放器/控制/导出
  tools/
    build_assets.py        asset-plan → 资产 + manifest（provider 适配器）
    validate_assets.py     台账/等级/画幅/许可校验（asset gate）
    build_timeline.py      TTS 实测 → 时间轴 → 字幕 → story.js
    validate_shots.py      分镜/轴线/画幅校验
    export_mp4.js          WebCodecs 导出
  quality.lock.json        质量合同（等级阈值、禁止项）
  qa/
    screenshots/  verification.json  build-report.json
  index.html  styles.css  start.command
```

## 8. 数据模型（摘要，完整 schema 见 `templates/project/story.schema.json`）

```jsonc
{
  "meta":   { "id": "EP01", "duration": 90, "fps": 30, "aspect": "2.39:1", "grade": "production" },
  "palette":{ "key": "#...", "fill": "#...", "rim": "#...", "accent": "#..." },
  "characters": [{
    "id": "lead", "model": "gltf", "src": "assets/models/chr_lead.glb",
    "tier": "T3", "rig": "humanoid", "bones": 65, "blendshapes": 18,
    "tris": 58000, "texelDensity": 1024, "license": "original",
    "lipsync": "assets/visemes/lead.json", "lock": "..."
  }],
  "locations":  [{ "id": "bridge", "tier": "T2", "src": "assets/models/env_bridge.glb", "hdri": "night_2k.hdr", "license": "CC0" }],
  "props":      [{ "id": "mug", "tier": "T2", "src": "...", "clue": ["setup", "reinforce", "payoff"] }],
  "shots":      [{ "id": "S01", "start": 0, "end": 6, "shotSize": "MS", "lens": 50, "axis": "main", "cameraSide": "A", "cutReason": "..." }],
  "lines":      [{ "id": "V01", "shot": "S01", "speaker": "lead", "sub": "...", "emotion": "calm" }],
  "events":     [{ "t": 12.4, "type": "foley", "id": "mug_set_down", "gain": -18 }],
  "curves":     { "fog": [[0,0.01],[60,0.05]], "exposure": [[0,1.0]] }
}
```

规则：`shots.start/end` 由 `lines` 实测时长反推；`events`/`curves` 与镜头窗同源 remap。**`tier` 是必填项**，缺省视为 T0 并报错。

## 9. 质量门

**验收分级**：`smoke`（能启动）→ `feature`（新行为 + 入口/出口）→ `visual`（关键帧截图）→ `performance`（先测量再优化）。不跳级。

**资产门（`validate_assets.py`）**
- 所有 `tier` 必需；`T0` 出现在成片镜头引用中 = error。
- `shotSize ∈ {CU, ECU}` 的镜头，出场角色必须 T3。
- `lens ≥ 85` 的镜头，主体资产 ≥ T2。
- 主体贴图 ≥ 2K；角色/关键道具必须有 baseColor + normal + roughness。
- 每个资产有 license；CC-BY 有署名；生成物有模型来源记录。
- 面数/纹素密度/骨骼数符合等级阈值（见 `quality.lock.json`）。

**技术门**
- 帧率：1280×720 集显 ≥30fps（p95 掉帧 <5%）；1080p 桌面 ≥50fps。
- 预算：集显三角面 ≤300k、draw call ≤120、材质 ≤40、后期 ≤3 pass；桌面 ≤2M / ≤300。
- 色彩：全片同一 `toneMapping`、同一曝光、同一 LUT；暗部无 banding。
- 一致性：同角色跨镜同实例、同材质、同光照；纹素密度偏差 ≤20%。
- 时间轴：`computeState(t)` 对任意 `t` 幂等；seek 后音频与字幕对齐误差 ≤80ms。

**叙事门**
- 每镜有唯一职责与 `cutReason`；连续两镜景别不同、角度差 ≥30°。
- 同场轴线一致；越轴有中性镜头或运动交代。
- 每场 ≥1 个插入镜/反应镜；镜长分布符合段落曲线。
- 信息释放表填完；每个伏笔有埋/强化/回收。
- 峰值前有 0.5–1s 静默设计；关键声音有 J/L cut。
- **画幅配额**：CU+ECU ≤ 总镜头数 25%（除非 T3 角色占比 ≥ 全片出场时长 60%）；85mm ≤ 30%。

**交付门**
- MP4 可离线播放；SRT 与音频同源；-14 LUFS ±0.5、峰值 ≤ -1 dBTP。
- 字幕不越安全区、对比度 ≥4.5:1。

## 10. 常见失败模式 → 规避

| 失败模式 | 症状 | 规避 |
|---|---|---|
| 弱资产大画幅 | 特写里是几何体 | 先定资产等级，再定景别；CU 只给 T3 |
| 塑料感 | 表面只有色块 | 补齐 normal + roughness + AO；统一纹素密度；triplanar |
| 假人 | 角色站着不动 | 呼吸/眨眼/重心/手指微动（见 character-performance） |
| 蜡像脸 | 皮肤无变化、眼窝不暗 | 4K 皮肤 + SSS 近似 + 接触阴影 + 眼窝 AO |
| 声音出戏 | 系统 TTS 的机械韵律 | 神经 TTS + 参考音色 + 情绪标注 + 句间气口 |
| 镜头乱 | 观众不知道看哪 | 每镜唯一职责 + 焦点唯一 + 三分/负空间 |
| 越轴 | 两人像没在对视 | 一场一条主轴，机位只在一侧 |
| 跳帧 | 切镜后画面"闪" | 30° 规则 + 景别变化 |
| 拖沓 | 前 20 秒没事件 | 信息释放表前置钩子；镜长按曲线压 |
| 声画不同步 | 嘴型/字幕漂 | 用实测时长排轴；`setTime` 不用 `update` |
| 细节被雾吃 | 近景也糊 | 雾密度按距离衰减；主体与背景 ≥15% 亮度差 |
| 越做越慢 | 后期堆太多 | 顺序 AO→反射→Bloom→AA；集显先砍 SSAO/DOF |
| 导出糊 | 录屏压缩 | WebCodecs 按帧编码，码率 ≥12Mbps |
| 生成资产不可复现 | 每次跑出来不一样 | 固定 seed / 模型版本 / prompt；产物 + hash 入库 |

## 11. 投入档位

| 档 | 适用 | 角色 | 场景/道具 | 配音 | 交付 |
|---|---|---|---|---|---|
| **prototype** | 内部预演 | T1（VRM/CC0） | T1 | `say` / `edge-tts` | 可播，不对外 |
| **production** | 对外短剧 | T2（VRM/图生 3D + 自动绑定） | T2 | `edge-tts` / IndexTTS | 1080p MP4 |
| **hero** | 参赛/商单 | T3（图生 3D + 精修 + 4K 皮肤） | T3 | IndexTTS 2.5 / CosyVoice 3 + 人工校 | 1080p+ 光追静帧 |

成本集中在 S3：`hero` 档只为 2–3 个主角色和 1–2 个主场景付费，其余用 T1/T2。

## 12. 题材适配（只换参数，不换流程）

| 题材 | 镜头侧重 | 材质/大气 | 声音 |
|---|---|---|---|
| 悬疑/恐怖 | 长镜 + 负空间 + 延迟揭示 | 低照度、单光源、体积雾 | 静默、J-cut、耳鸣 |
| 科幻 | 广角 + 对称构图 + 大幅运镜 | 金属/发光/雾 + bloom | 低频嗡鸣、合成音 |
| 古装/武侠 | 中远景 + 横移 + 留白 | 布料 sheen、木石、尘埃 | 环境声、兵器拟音 |
| 都市/情感 | 中近景 + 手持 + 浅景深 | 湿地面反射、霓虹 | 环境底噪、音乐主导 |
| 奇幻 | 大远景 + 升降 + 奇观 | 次表面散射、体积光 | 合唱、魔法音效 |

## 13. 参考手册

- `references/asset-pipeline.md` — 资产生产：等级、来源、图生 3D、重拓扑、纹理控制、绑定、压缩、许可
- `references/threejs-refinement.md` — Three.js 侧精修：triplanar、decal、细节法线、接触阴影、LOD、光追静帧
- `references/component-catalog.md` — 组件选型（star 核实、接入方式、替代）
- `references/cinematic-staging.md` — 电影级分镜与故事调度（含资产能力驱动分镜）
- `references/photoreal-scene.md` — 逼真场景：材质/光照/大气/水体/后期
- `references/character-performance.md` — 人物：来源等级/骨骼/表情/口型/二次动作
- `references/sound-and-delivery.md` — 配音（神经 TTS 矩阵）/混音/导出/交付
- `templates/project/` — 可直接复制的项目脚手架（schema、分镜卡、资产计划、校验器、播放器）
