# 项目脚手架使用说明

把本目录复制到你的项目根，按下面顺序改。**所有文件都与题材无关**，只换内容不换结构。

```bash
cp -r templates/project/* <your-project>/
cd <your-project>
```

## 1. 先填数据，不写代码

1. `design/story.json` — 按 `story.schema.json` 填：meta / characters / locations / props / shots / lines / events / curves。
2. `design/05-shots.md` — 用 `shot-card.md` 逐镜填，字段与 JSON 一一对应。
3. 跑校验：

```bash
python3 tools/validate_shots.py design/story.json
```

error 清零、warning 逐条判断后再进入下一步。

## 2. 生成时间轴与配音

```bash
python3 tools/build_timeline.py          # 首次：合成 + 实测 + 排轴
python3 tools/build_timeline.py --reuse  # 改台词/镜头后：复用音频，秒级重排
```

产出 `src/story.js`（唯一数据源）、`assets/audio/*.mp3`、`assets/subtitles/ep.srt`、`qa/build-report.json`。

`story.json` 的 `voices` 段示例：

```jsonc
"voices": {
  "lead":  { "name": "Eddy (中文（中国大陆）)", "rate": 180, "fallback": "Tingting" },
  "other": { "name": "Grandpa (中文（中国大陆）)", "rate": 172, "fallback": "Tingting" }
}
```

## 3. 写渲染层

- `src/timeline.js` ← 复制 `compute-state.js`，按需扩展 `curves` 与事件。
- `src/world.js` — 场景装配；所有资产只创建一次；`apply(t, state)` 只改 uniform/transform。
- `src/character.js` — 角色/动画/口型（见 `references/character-performance.md`）。
- `src/audio.js` — `scheduleFrom(t)` 调度配音；Web Audio 程序化环境音。
- `src/main.js` — rAF 主循环 + 播放/暂停/拖动/逐帧/静音/字幕 + 导出按钮。

## 4. 起服务与验收

```bash
python3 -m http.server 8899 --bind 127.0.0.1
```

必须经 HTTP 打开（ES Module + importmap 在 `file://` 下会被拦截）。
加 QA 入口：`?t=45&preview=1`（停帧）、`?autoplay=1`（自动播）、`?grade=aces`（画质档）。

## 5. 导出成片

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

## 6. 文件清单

| 文件 | 用途 |
|---|---|
| `story.schema.json` | 数据契约（校验/IDE 补全） |
| `shot-card.md` | 分镜卡模板 |
| `compute-state.js` | 纯函数时间轴骨架 |
| `build_timeline.py` | TTS 实测 + 排轴 + 字幕 + story.js |
| `validate_shots.py` | 分镜/资产/时间轴校验 |
| `player-shell.html` | 播放器安全壳（CSP + sandbox iframe + 超时提示） |
| `export.js` | 成片导出：WebCodecs / MediaRecorder / mediabunny 裁剪 |
| `REBUILD-SPEC.md` | 重制规格书 |
