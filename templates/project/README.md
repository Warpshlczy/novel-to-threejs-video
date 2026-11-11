# 项目脚手架使用说明

把本目录复制到你的项目根，按下面顺序改。**所有文件都与题材无关**，只换内容不换结构。

```bash
cp -r templates/project/* <your-project>/
cd <your-project>
mkdir -p tools && mv *.py tools/        # 构建脚本放 tools/，脚手架文件留在根
```

## 1. 填数据，不写代码

1. `design/story.json` — 按 `story.schema.json` 填：meta / characters / locations / props / shots / lines / events / curves。
2. `design/05-shots.md` — 用 `shot-card.md` 逐镜填，字段与 JSON 一一对应。
3. 跑校验：

```bash
python3 tools/validate_shots.py design/story.json
python3 tools/validate_assets.py design/story.json
```

error 清零、warning 逐条判断后再进入下一步。

## 2. 定资产等级并生产

1. 复制 `quality.lock.json`，确认 `grade`（prototype / production / hero）。
2. 写 `design/asset-plan.json`（schema：`asset-plan.schema.json`），每个资产给出 `tier` / `route` / `prompt` / `refs` / `out` / `license`。
3. 生成台账与作业单：

```bash
python3 tools/build_assets.py --plan design/asset-plan.json
# 产物：assets/manifest.json、assets/jobs/<id>.json、assets/CREDITS.md

python3 tools/build_assets.py --plan design/asset-plan.json --run   # 执行 local/manual 命令
python3 tools/build_assets.py --verify                              # 校验既有文件 hash
```

4. 资产门复查：

```bash
python3 tools/validate_assets.py design/story.json
```

**等级速查**：T0 只做 previz；T1 最多 MS；T2 最多 MCU；T3 才能 CU/ECU。
来源与做法见 `references/asset-pipeline.md`，引擎内精修见 `references/threejs-refinement.md`。

`asset-plan.json` 最小示例：

```jsonc
{
  "version": 1,
  "grade": "production",
  "providers": {
    "image": { "kind": "fal", "model": "fal-ai/flux/dev" },
    "mesh":  { "kind": "fal", "model": "fal-ai/trellis-2" },
    "rig":   { "kind": "fal", "model": "fal-ai/meshy/rigging" },
    "asset": { "kind": "manual", "command": "blender -b --python tools/import.py -- {out}" }
  },
  "assets": [
    {
      "id": "chr_lead", "kind": "character", "tier": "T3", "route": "image-to-3d",
      "prompt": "…逐字保存的正面三视图描述…",
      "refs": ["ref/chr_lead_front.png"],
      "out": "assets/models/chr_lead.glb",
      "targetTris": 60000, "texelDensity": 1024,
      "maps": ["baseColor", "normal", "roughness"],
      "rig": "humanoid", "blendshapes": 15,
      "license": "original",
      "lock": "…可原样粘贴的连续性锁…"
    }
  ]
}
```

## 3. 生成时间轴与配音

```bash
python3 tools/build_timeline.py          # 首次：合成 + 实测 + 排轴
python3 tools/build_timeline.py --reuse  # 改台词/镜头后：复用音频，秒级重排
```

产出 `src/story.js`（唯一数据源）、`assets/audio/*.mp3`、`assets/subtitles/ep.srt`、`qa/build-report.json`。

`story.json` 的 `voices` 段示例：

```jsonc
"voices": {
  "lead":  { "engine": "edge-tts", "name": "zh-CN-YunxiNeural", "rate": 0, "emotion": "calm" },
  "other": { "engine": "edge-tts", "name": "zh-CN-YunjianNeural", "rate": -4, "emotion": "tense" }
}
```

- `prototype` 档可用 macOS `say`；`production` 及以上必须是神经引擎（edge-tts / IndexTTS / CosyVoice）。
- 逐句情绪标注见 `references/sound-and-delivery.md`。

## 4. 写渲染层

- `src/timeline.js` ← 复制 `compute-state.js`，按需扩展 `curves` 与事件。
- `src/world.js` — 场景装配；所有资产只创建一次；`apply(t, state)` 只改 uniform/transform。
- `src/character.js` — 角色/动画/口型（见 `references/character-performance.md`）。
- `src/audio.js` — `scheduleFrom(t)` 调度配音；Web Audio 环境音。
- `src/main.js` — rAF 主循环 + 播放/暂停/拖动/逐帧/静音/字幕 + 导出按钮。

材质精修（triplanar / detail normal / decal / 接触阴影）见 `references/threejs-refinement.md`。

## 5. 起服务与验收

```bash
python3 -m http.server 8899 --bind 127.0.0.1
```

必须经 HTTP 打开（ES Module + importmap 在 `file://` 下会被拦截）。
加 QA 入口：`?t=45&preview=1`（停帧）、`?autoplay=1`（自动播）、`?grade=hero`（画质档）。

## 6. 导出成片

```js
// 伪代码：WebCodecs + mp4-muxer
const muxer = new Muxer({ target: new ArrayBufferTarget(), video: { codec: 'avc', width, height } });
const encoder = new VideoEncoder({ output: (c, m) => muxer.addVideoChunk(c, m), error: console.error });
encoder.configure({ codec: 'avc1.640028', width, height, bitrate: 12_000_000, framerate: 30 });
for (let f = 0; f * (1 / 30) <= TOTAL; f++) {
  renderAt(f / 30);                       // 用 computeState(t) 精确重建
  const frame = new VideoFrame(canvas, { timestamp: (f * 1e6) / 30 });
  encoder.encode(frame, { keyFrame: f % 60 === 0 });
  frame.close();
}
await encoder.flush();
muxer.finalize();
```

音频用 ffmpeg 与视频合成并做 loudnorm：

```bash
ffmpeg -i video.mp4 -i mix.wav -c:v copy -c:a aac -b:a 192k -af loudnorm=I=-14:TP=-1:LRA=11 out.mp4
```

## 7. 文件清单

| 文件 | 用途 |
|---|---|
| `story.schema.json` | 数据契约（含 tier / 表情 / 画幅字段） |
| `asset-plan.schema.json` | 资产生产计划契约 |
| `quality.lock.json` | 质量合同：等级阈值、配额、禁止项 |
| `shot-card.md` | 分镜卡模板 |
| `compute-state.js` | 纯函数时间轴骨架 |
| `build_assets.py` | asset-plan → manifest / jobs / CREDITS |
| `validate_assets.py` | 资产门：等级 vs 画幅、贴图、骨骼、许可 |
| `build_timeline.py` | TTS 实测 + 排轴 + 字幕 + story.js |
| `validate_shots.py` | 分镜/轴线/节奏校验 |
| `player-shell.html` | 播放器安全壳（CSP + sandbox iframe + 超时提示） |
| `export.js` | 成片导出：WebCodecs / MediaRecorder / mediabunny 裁剪 |
| `REBUILD-SPEC.md` | 重制规格书 |
