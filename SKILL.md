---
name: novel-to-threejs-cinematic
description: 把任意小说、剧本、大纲或分镜稿，制作成电影级 Three.js 3D 叙事成片（浏览器实时播放 + 可导出 MP4）：故事工程、视觉开发、真实感场景（PBR/HDRI/大气/水体/后期）、人物表演（VRM/骨骼/口型/二次动作）、电影级分镜与调度（景别/焦段/轴线/走位/覆盖/剪辑/声音）、纯函数时间轴与音频实测同步、组件选型与质量门。适用于「小说转 3D 动画 / 电影级分镜 / 短剧 / 逼真场景 / 人物表演 / three.js 叙事 / 逐帧渲染 / 成片导出」等请求，题材不限。
license: MIT
---

# 小说 / 剧本 → 电影级 Three.js 叙事（v4）

把文字变成**能播、能导出、经得起特写**的 3D 成片。本 skill 与具体故事无关：任何题材、任何长度都走同一套流程，只换参数与资产。

## 0. 什么叫"完成"

一份交付必须同时满足：

1. **能播**：浏览器打开即播，可暂停/拖动/逐帧，字幕与配音同步。
2. **能导出**：一键产出 MP4（H.264/AAC），可离线播放。
3. **能复现**：任意 `t` 的画面可由 `computeState(t)` 重建，拖动进度不漂移。
4. **经得起看**：特写 1m 内有三层材质细节；人物有二次动作与口型；镜头有动机。
5. **能核对**：分镜卡、信息释放表、拟音事件表、响度报告齐全。

## 1. 三条铁律

1. **一致性靠资产锁定 + 纯函数时间轴**：角色/场景只加载一次；每帧从 `t` 重算全部状态，不用 `update(dt)` 累积。
2. **表演 > 面部 > 骨骼 > 模型精度**：真实感的第一来源是"像个在场的人"，不是面数。先给呼吸、眨眼、重心，再谈高模。
3. **声音与画面同源**：配音实测时长驱动字幕与镜头窗；拟音事件与画面动作同帧（±2 帧）。
4. **场景图只是渲染适配器**：规则、状态、时间轴都在 Three 对象之外；相机模式必须显式声明（orbit / follow / chase / rail / first-person / **authored cuts**），电影叙事一律用 authored cuts。

## 2. 生产流程（七阶段，每阶段有交付物与门）

| 阶段 | 输入 | 产出 | 完成标准 |
|---|---|---|---|
| **S0 故事工程** | 原文/大纲 | beat sheet、信息释放表、张力曲线、伏笔三处表 | 每场有戏剧功能；观众知情时机可核对 |
| **S1 视觉开发** | S0 + 参考 | Look Dev 板：色板、材质语言、镜头语言、LUT、参考帧 | 一句话能说清"像什么"；同场景光色唯一 |
| **S2 资产** | S1 | 角色/道具/环境资产 + 授权登记 + LOD | 每个资产有 ID、来源、许可、面数、纹素密度 |
| **S3 分镜与调度** | S0/S1/S2 | 分镜卡（含焦段/机位/轴线/走位/覆盖/cutReason） | 每镜唯一职责；轴线零违规；覆盖齐全 |
| **S4 装配** | S3 | 场景装配、光照、大气、人物、时间轴、字幕 | `computeState(t)` 全绿；音频全部加载 |
| **S5 渲染导出** | S4 | 实时播放器 + MP4 + SRT + 响度报告 | 成片可离线播；-14 LUFS |
| **S6 验收** | 全部 | 验收记录 + 关键帧证据 | 技术门 + 叙事门全绿 |

## 3. 技术栈选型（详见 `references/component-catalog.md`）

| 层 | 首选 | 备选 |
|---|---|---|
| 引擎 | three.js（vendor 化，无构建） | Babylon.js |
| 色彩/后期 | `pmndrs/postprocessing` + ACES/AgX + 一支 LUT | three 原生 composer |
| 环境光 | `PMREMGenerator` + Poly Haven CC0 HDRI | 程序化天空 |
| 材质 | `MeshPhysicalMaterial`（clearcoat/transmission/sheen） | `MeshStandardMaterial` |
| AO/反射 | `N8python/n8ao` + SSR | SSAOEffect |
| 人物 | `pixiv/three-vrm` + VRMA | glTF + Mixamo |
| 口型 | `rhubarb-lip-sync`（离线）/ `HeadTTS`（浏览器） | `TalkingHead` |
| 动作/物理 | `dimforge/rapier`（碰撞/布料） | cannon-es |
| 粒子/VFX | `Alchemist0823/three.quarks` | 自写 Points |
| 运镜 | `yomotsu/camera-controls`（平滑过渡） | 自写插值 |
| 时间轴 | 自写 `computeState(t)` + `theatre-js/theatre`（可视化调参） | GSAP |
| 空间查询 | `gkjohnson/three-mesh-bvh`（射线/遮挡/防穿模） | 手写包围盒 |
| 布尔 | `gkjohnson/three-bvh-csg`（开洞/切割） | Blender 预处理 |
| 离线光追 | `gkjohnson/three-gpu-pathtracer`（关键帧） | Blender Cycles |
| 压缩 | `donmccurdy/glTF-Transform` + `zeux/meshoptimizer` + KTX2 | gltfpack |
| 导出 | WebCodecs + `Vanilagy/mp4-muxer` | `mediabunny`（纯 TS 转码/裁剪，可 mp4/webm） |
| 镜头切分自检 | `Breakthrough/PySceneDetect` | 人工 |

## 4. 通用项目结构

```
<project>/
  design/
    00-story.md            故事工程：beat sheet / 信息释放表 / 张力曲线
    01-look-dev.md         视觉开发：色板 / 材质语言 / 镜头语言 / LUT
    02-characters.md       角色：ID / 三视图 / 骨骼 / 表情 / 口型
    03-locations.md        场景：ID / 尺寸 / 光照 / 大气 / 材质
    04-props.md            道具：ID / 线索链（埋-强化-回收）
    05-shots.md            分镜卡（见 cinematic-staging）
    06-sound.md            拟音事件表 / 环境三层 / 音乐 spotting
    07-qa.md               验收记录
  assets/
    models/  textures/  hdri/  audio/  subtitles/
  src/
    story.js               由构建脚本生成的唯一数据源
    timeline.js            computeState(t) 纯函数
    world.js               场景装配与 apply(t, state)
    character.js           角色/动画/口型
    audio.js               配音调度 + 程序化环境音
    main.js                播放器/控制/导出
  tools/
    build_timeline.py      TTS 实测 → 时间轴 → 字幕 → story.js
    validate_shots.py      分镜/资产/时间轴校验
    export_mp4.js          WebCodecs 导出
  qa/
    screenshots/  verification.json  build-report.json
  index.html  styles.css  start.command
```

## 5. 数据模型（摘要，完整 schema 见 `templates/project/story.schema.json`）

```jsonc
{
  "meta":   { "id": "EP01", "duration": 90, "fps": 30, "aspect": "2.39:1" },
  "palette":{ "key": "#...", "fill": "#...", "rim": "#...", "accent": "#..." },
  "characters": [{ "id": "lead", "model": "vrm", "rig": "humanoid", "lipsync": "viseme.json" }],
  "locations":  [{ "id": "bridge", "hdri": "night_1k.hdr", "fog": 0.02 }],
  "props":      [{ "id": "mug", "clue": ["setup", "reinforce", "payoff"] }],
  "shots":      [{ "id": "S01", "start": 0, "end": 6, "shotSize": "MS", "lens": 50, "axis": "main", "cutReason": "..." }],
  "lines":      [{ "id": "V01", "shot": "S01", "speaker": "lead", "sub": "...", "voice": "..." }],
  "events":     [{ "t": 12.4, "type": "foley", "id": "mug_set_down", "gain": -18 }],
  "curves":     { "fog": [[0,0.01],[60,0.05]], "exposure": [[0,1.0]] }
}
```

规则：`shots` 的 `start/end` 可由 `lines` 实测时长反推（构建脚本负责 remap）；`events` 与 `curves` 必须按同一时基。

## 6. 质量门

**验收分级**（按改动大小选一档，不跳级）：`smoke`（能启动、首屏可操作）→ `feature`（新行为 + 入口/出口 + 失败路径）→ `visual`（关键帧截图，查构图/遮挡/裁剪/响应式）→ `performance`（先测量再优化）。截图空白检测只是警告信号，不能当作"画面正常"的证明。

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

**交付门**
- MP4 可离线播放；SRT 与音频同源；-14 LUFS ±0.5、峰值 ≤ -1 dBTP。
- 字幕不越安全区、对比度 ≥4.5:1。

## 7. 常见失败模式 → 规避

| 失败模式 | 症状 | 规避 |
|---|---|---|
| 塑料感 | 表面只有色块 | 补齐 normal + roughness + AO；统一纹素密度 |
| 假人 | 角色站着不动 | 呼吸/眨眼/重心/手指微动（见 character-performance） |
| 镜头乱 | 观众不知道看哪 | 每镜唯一职责 + 焦点唯一 + 三分/负空间 |
| 越轴 | 两人像没在对视 | 一场一条主轴，机位只在一侧 |
| 跳帧 | 切镜后画面"闪" | 30° 规则 + 景别变化 |
| 拖沓 | 前 20 秒没事件 | 信息释放表前置钩子；镜长按曲线压 |
| 声画不同步 | 嘴型/字幕漂 | 用实测时长排轴；`setTime` 不用 `update` |
| 细节被雾吃 | 近景也糊 | 雾密度按距离衰减；主体与背景 ≥15% 亮度差 |
| 越做越慢 | 后期堆太多 | 顺序 AO→反射→Bloom→AA；集显先砍 SSAO/DOF |
| 导出糊 | 录屏压缩 | WebCodecs 按帧编码，码率 ≥12Mbps |

## 8. 题材适配（只换参数，不换流程）

| 题材 | 镜头侧重 | 材质/大气 | 声音 |
|---|---|---|---|
| 悬疑/恐怖 | 长镜 + 负空间 + 延迟揭示 | 低照度、单光源、体积雾 | 静默、J-cut、耳鸣 |
| 科幻 | 广角 + 对称构图 + 大幅运镜 | 金属/发光/雾 + bloom | 低频嗡鸣、合成音 |
| 古装/武侠 | 中远景 + 横移 + 留白 | 布料 sheen、木石、尘埃 | 环境声、兵器拟音 |
| 都市/情感 | 中近景 + 手持 + 浅景深 | 湿地面反射、霓虹 | 环境底噪、音乐主导 |
| 奇幻 | 大远景 + 升降 + 奇观 | 次表面散射、体积光 | 合唱、魔法音效 |

## 9. 参考手册

- `references/component-catalog.md` — 组件选型（star 核实、接入方式、替代）
- `references/cinematic-staging.md` — 电影级分镜与故事调度
- `references/photoreal-scene.md` — 逼真场景：材质/光照/大气/水体/后期
- `references/character-performance.md` — 人物：模型/骨骼/表情/口型/二次动作
- `references/asset-pipeline.md` — 资产：来源/授权/规范化/压缩/LOD
- `references/sound-and-delivery.md` — 声音/混音/导出/交付
- `templates/project/` — 可直接复制的项目脚手架（schema、分镜卡、时间轴、校验器、播放器）
