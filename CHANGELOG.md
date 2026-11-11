# Changelog

## 1.1.0 — 2026-11-12

资产生产成为独立阶段；新增「资产等级 vs 画幅」硬约束。

- `SKILL.md`：七阶段扩为八阶段（S2 资产计划、S3 资产生产）；新增资产等级 T0–T3 与画幅上限；新增「Agent 执行协议」（每阶段必做/禁止/出口校验 + 决策顺序）；新增投入档位（prototype/production/hero）与资产门；失败模式补到 14 条。
- 新增 `references/asset-pipeline.md`（重写）：等级预算、CC0/生成/扫描来源矩阵、图生 3D 输入规范、重拓扑/UV、纹素密度与 PBR 套图、自动绑定、规范化、压缩/LOD、台账可复现、许可。
- 新增 `references/threejs-refinement.md`：triplanar、detail normal、顶点 AO/曲率遮罩、假 SSS、Decal、接触阴影、后期顺序、三档画质 preset、光追静帧。
- `references/cinematic-staging.md`：新增「资产能力驱动分镜」——画幅上限、CU/ECU 与 85mm 配额、资产不足时的替代语法、分镜卡新增 `subjectTier`/`faceBudget`/`assetFallback`。
- `references/character-performance.md`：重写为四条来源路线（图生 3D / VRM / CC0 / 程序化），VRM 明确为备选；补各路线最小配置、T3 blendshape 最小集、按等级的表情分级。
- `references/sound-and-delivery.md`：重写配音为神经 TTS 矩阵（IndexTTS 2.5 / CosyVoice 3 / GPT-SoVITS / Fish-Speech / edge-tts）；新增音色档案、情绪标注、自动配音流水线（合成→归一→对齐→viseme→混音）、档位门禁。
- `references/component-catalog.md`：新增图生 3D / 自动绑定 / 重拓扑 / 神经 TTS 组件表与托管 API；决策树改为按资产等级与画幅分流。
- `templates/project/` 新增：`quality.lock.json`（质量合同）、`asset-plan.schema.json`、`build_assets.py`（计划→台账/作业单/hash 校验）、`validate_assets.py`（资产门）。
- `story.schema.json`：meta 增 `grade`；characters/locations/props 增 `tier`/`license` 与质量字段；shots 增 `subjectTier`/`faceBudget`/`assetFallback`；lines 增 `emotion`/`intensity`/`pauseAfter`。
- `examples/minimal/`：补 `quality.lock.json`（prototype 档）与资产等级。
- CI：新增 `build_assets.py` / `validate_assets.py` 编译与示例资产门校验。

## 1.0.0 — 2026-11-11

首次公开发布。

- `SKILL.md`：七阶段生产流程（S0 故事工程 → S6 验收）、三条铁律 +「场景图只是渲染适配器」、技术栈选型、数据模型、三档质量门、10 条失败模式、5 类题材适配。
- `references/`：
  - `cinematic-staging.md` 电影级分镜与调度（景别/角度/焦段/运镜/构图/走位/轴线/剪辑/信息释放/伏笔/自检）
  - `photoreal-scene.md` 逼真场景（色彩科学/PBR/三层光/阴影/AO/SSR/大气/水体/后期/多尺度细节契约）
  - `character-performance.md` 人物（VRM/骨骼/表情/口型/二次动作/表演方法/预算）
  - `asset-pipeline.md` 资产（授权/规范化/压缩/LOD/台账/一致性锁）
  - `sound-and-delivery.md` 声音（配音/拟音/环境/音乐/混音/导出/交付）
  - `component-catalog.md` 组件选型（star 已核实）+ ohmygame 可复用零件 + MCP 生成工具
- `templates/project/`：`story.schema.json`、`shot-card.md`、`compute-state.js`、`build_timeline.py`、`validate_shots.py`、`player-shell.html`、`export.js`、`REBUILD-SPEC.md`、`README.md`。
- `examples/minimal/`：20 秒三镜最小示例，可直接跑校验。
- CI：`.github/workflows/validate.yml`（Python 编译、JS 语法、JSON 解析、绝对路径与专有名词检查、示例校验）。

## 0.4.0 — 2026-11-11

完全重制为通用手册：删除「局限」导向结构；分镜改为可校验字段；新增组件选型表与项目脚手架；清理全部具体作品专有名词。

## 0.3.0 — 2026-11-11

新增人物与渲染细节：角色四档、程序化微动作、程序化细节纹理（固定 seed）、材质/光照/后期清单。

## 0.2.0 — 2026-11-11

新增画质分层（L0–L3）与分镜 DSL（状态机 + 校验规则），色彩管线并入 three 统一 tonemapping/colorspace。

## 0.1.0 — 2026-11-11

初版：以一部 90 秒单集为实例跑通「原著 → 剧本 → 分镜 → 实测时间轴 → Three.js 播放器」。
