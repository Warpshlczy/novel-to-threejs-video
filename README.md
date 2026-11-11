# novel-to-threejs-cinematic

**把小说、剧本或大纲，做成电影级 Three.js 3D 叙事成片。**

一个面向 AI 编程 Agent 的 skill 包：从故事工程、资产生产、分镜调度，到逼真场景、人物表演、神经配音与字幕，最后产出**浏览器可播 + 可导出 MP4**的成片。与具体故事无关，题材不限。

```text
原著/剧本 → 故事工程 → 视觉开发 → 资产计划 → 资产生产 → 分镜与调度 → 装配 → 渲染导出 → 验收
```

## 为什么需要它

把文字变成 3D 动画，最容易失败在四个地方：

1. **一致性崩**：换一个镜头，人物就变了一个人。→ 本包用「资产锁定 + 纯函数时间轴」解决。
2. **资产缺失**：用胶囊和色块演一部需要特写的戏。→ 本包用「T0–T3 资产等级 + 画幅上限 + 资产门」拦住。
3. **画面塑料**：只有色块、没有材质与光照层次。→ 本包给出 PBR/HDRI/SSAO/triplanar/decal/光追静帧的完整配方。
4. **镜头不会讲故事**：只是把小说分段拍。→ 本包给出景别/焦段/轴线/走位/覆盖/剪辑/信息释放的可执行规范与校验器。

## 它是什么

| 组成 | 内容 |
|---|---|
| `SKILL.md` | 总纲：资产等级、八阶段流程、Agent 执行协议、技术栈、数据模型、四类质量门、失败模式、投入档位 |
| `references/asset-pipeline.md` | 资产生产：等级预算、CC0 来源、图生 3D、重拓扑/UV、纹理控制、自动绑定、压缩、许可 |
| `references/threejs-refinement.md` | 引擎内精修：triplanar、detail normal、顶点 AO、decal、接触阴影、三档画质 preset、光追静帧 |
| `references/cinematic-staging.md` | 电影级分镜与调度：景别/角度/焦段/运镜/构图/走位/轴线/剪辑/信息释放/伏笔/**资产能力驱动分镜** |
| `references/photoreal-scene.md` | 逼真场景：色彩科学、PBR、三层光、阴影、AO/SSR、大气、水体、后期、多尺度细节契约 |
| `references/character-performance.md` | 人物：四条来源路线（图生 3D / VRM / CC0 / 程序化）、骨骼、表情、口型、二次动作 |
| `references/sound-and-delivery.md` | 声音：神经 TTS 矩阵、音色设计、情绪标注、自动配音流水线、拟音/环境/音乐/混音/导出 |
| `references/component-catalog.md` | 组件选型（GitHub star 已核实）+ 托管 API + 决策树 + 可复用零件 |
| `templates/project/` | 可直接复制的脚手架：数据契约、资产计划、质量合同、分镜卡、时间轴、构建脚本、校验器、播放器壳、导出脚本 |

## 安装

支持 Agent Skill 规范的环境（Claude Code、Codex等）任选其一：

```bash
# A. 复制到用户级 skills 目录
git clone https://github.com/Warpshlczy/novel-to-threejs-video.git
cp -R novel-to-threejs-video ~/.workbuddy-ai/skills/
# 或 Claude Code：
cp -R novel-to-threejs-video ~/.claude/skills/

# B. 用 skills CLI（若你的环境支持）
npx skills add Warpshlczy/novel-to-threejs-video -y -g
```

## 资产等级 T0–T3（v5 核心）

| 等级 | 名称 | 典型来源 | 允许的最大画幅 |
|---|---|---|---|
| T0 | blocking | 程序化基本体、灰盒 | 不进成片 |
| T1 | stylized | CC0 低模、风格化 VRM | MS |
| T2 | production | VRM/glTF + Mixamo、图生 3D + 自动重拓扑 + 自动绑定 | MCU |
| T3 | hero | 定制雕刻/扫描、4K 皮肤、15+ blendshape | CU / ECU |

**规则**：CU/ECU 只给 T3；85mm 只给 T2 及以上；CU+ECU ≤25%，85mm ≤30%。
资产不够时改分镜（手/背影/剪影/物件/声音），不要硬切特写。

## 三条铁律

1. **一致性靠资产锁定 + 纯函数时间轴**：角色/场景只加载一次；每帧从 `t` 重算，不用 `update(dt)` 累积。
2. **资产决定画幅**：能用多大画幅由资产等级决定，不由导演愿望决定。
3. **表演 > 面部 > 骨骼 > 模型精度**：先给呼吸、眨眼、重心，再谈高模。

第 4 条：**声音与画面同源**，配音实测时长驱动字幕与镜头窗。
第 5 条：**场景图只是渲染适配器**，电影叙事用 authored cuts。

## 快速开始

```bash
# 1. 建项目并复制脚手架
mkdir my-episode && cp -R templates/project/* my-episode/

# 2. 填规格与数据
#    my-episode/REBUILD-SPEC.md      ← 目标画质/资产/镜头/声音/预算/验收
#    my-episode/design/story.json    ← 按 story.schema.json 填
#    my-episode/design/asset-plan.json ← 按 asset-plan.schema.json 填

# 3. 资产计划 + 台账
cd my-episode
python3 tools/build_assets.py --plan design/asset-plan.json

# 4. 双校验
python3 tools/validate_shots.py design/story.json
python3 tools/validate_assets.py design/story.json

# 5. 生成配音与时间轴（需 ffmpeg；production 档用 edge-tts 或神经 TTS）
python3 tools/build_timeline.py

# 6. 起服务预览
python3 -m http.server 8899 --bind 127.0.0.1
# 打开 http://127.0.0.1:8899/index.html?t=45&preview=1
```

> 脚手架复制到项目后，目录是 `tools/`；本仓库内为 `templates/project/`。

## 质量门（摘要）

| 门 | 关键指标 |
|---|---|
| 资产 | 无 T0 进成片；CU/ECU 主体 T3；85mm 主体 ≥T2；主体贴图 ≥2K；三件套齐全；许可可追溯 |
| 技术 | 集显 720p ≥30fps（p95 掉帧 <5%）；三角面 ≤300k；draw call ≤120；纹素密度偏差 ≤20%；任意 `t` 可重建 |
| 叙事 | 每镜唯一职责与 `cutReason`；连续两镜景别不同、角度差 ≥30°；轴线零违规；伏笔三处齐全；峰值前有静默 |
| 交付 | MP4 可离线播放；SRT 与音频同源；-14 LUFS ±0.5；峰值 ≤ -1 dBTP |

验收分四级：`smoke → feature → visual → performance`，不跳级。

## 目录

```
.
├── SKILL.md
├── references/
│   ├── asset-pipeline.md
│   ├── threejs-refinement.md
│   ├── cinematic-staging.md
│   ├── photoreal-scene.md
│   ├── character-performance.md
│   ├── sound-and-delivery.md
│   └── component-catalog.md
├── templates/project/
│   ├── story.schema.json
│   ├── asset-plan.schema.json
│   ├── quality.lock.json
│   ├── shot-card.md
│   ├── compute-state.js
│   ├── build_assets.py
│   ├── validate_assets.py
│   ├── build_timeline.py
│   ├── validate_shots.py
│   ├── player-shell.html
│   ├── export.js
│   ├── REBUILD-SPEC.md
│   └── README.md
├── examples/minimal/          # 20 秒四镜最小示例（prototype 档）
├── .github/workflows/validate.yml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## 兼容性

- 渲染层：three.js（建议固定版本并 vendor 化）；不依赖构建链也能跑。
- 资产：GLB / glTF 2.0 / VRM；图生 3D 输出（TRELLIS.2 / Hunyuan3D-2.1）；CC0 模型与 PBR 贴图。
- 绑定：VRM 自带 Humanoid、Mixamo、UniRig。
- 导出：WebCodecs + mp4-muxer，或 mediabunny。
- 配音：神经 TTS（IndexTTS 2.5 / CosyVoice 3 / GPT-SoVITS / edge-tts）/ 真人；口型用 rhubarb 或 viseme 时间轴。

## 致谢

方法论参考并受益于以下开源项目（仅借鉴方法，不复制代码）：

- [zenstory-ai/drama-skills](https://github.com/zenstory-ai/drama-skills) — 每镜唯一职责、连续性锁、对白估时
- [zenstory-ai/novel-to-game](https://github.com/zenstory-ai/novel-to-game) — ART_DIRECTION、实机验收
- [WhiteTowerAI/ohmygame](https://github.com/WhiteTowerAI/ohmygame) — 多尺度细节契约、资产 7 步、分级验收
- [SkyeShark/eidoverse-video](https://github.com/SkyeShark/eidoverse-video) — 纹素密度/风化、lipsync、增强顺序
- [microsoft/TRELLIS.2](https://github.com/microsoft/TRELLIS.2)、[Tencent-Hunyuan/Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) — 图生 3D
- [VAST-AI-Research/UniRig](https://github.com/VAST-AI-Research/UniRig) — 自动骨骼与蒙皮
- [bilibili/IndexTTS](https://github.com/bilibili/IndexTTS)、[FunAudioLLM/CosyVoice](https://github.com/FunAudioLLM/CosyVoice) — 神经配音
- [pmndrs/postprocessing](https://github.com/pmndrs/postprocessing)、[N8python/n8ao](https://github.com/N8python/n8ao)、[pixiv/three-vrm](https://github.com/pixiv/three-vrm)

## 许可

MIT，见 [LICENSE](LICENSE)。
