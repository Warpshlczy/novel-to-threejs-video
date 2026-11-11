# Changelog

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
