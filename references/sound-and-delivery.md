# 声音与成片交付

> 目标：让声音承担一半的叙事，让成片能直接播、能上平台。
> 顺序：**对白 → 拟音 → 环境 → 音乐 → 混音 → 交付**。

## 1. 配音

| 路线 | 工具 | 适用 |
|---|---|---|
| 系统 TTS | macOS `say`（Eddy/Grandpa zh_CN） | 快速原型、无网络 |
| 神经 TTS | `met4citizen/HeadTTS`（Kokoro，浏览器内）、edge-tts | 音色自然、带时间戳 |
| 真人配音 | 录音 + 降噪 | 最高质量 |

- **情绪标注**：每句台词标 `calm / tense / broken / whisper`，TTS 用不同 rate/volume 近似，真人按标注演。
- **口型**：`rhubarb-lip-sync` 或 HeadTTS viseme，对齐误差 ≤80ms。
- **台词与字幕分离**：字幕保留原文（GPS/VHF），朗读用中文读法。
- **呼吸与气口**：句间留 0.2–0.5s；峰值前留 0.8s 静默。

## 2. 拟音（Foley）事件表

每个声音事件写进时间轴，跟 `t` 对齐：

```jsonc
[
  { "t": 12.4, "event": "mug_set_down", "layer": "foley", "gain": -18 },
  { "t": 39.2, "event": "wind_hit_bridge", "layer": "foley", "gain": -8 },
  { "t": 47.0, "event": "metal_creak", "layer": "foley", "gain": -14 },
  { "t": 66.4, "event": "silence", "layer": "master", "gain": -60 }
]
```

常见层：脚步、衣物摩擦、金属吱嘎、水拍船壳、门轴、无线电噪声、心跳、耳鸣。

## 3. 环境（三层）

1. **底噪**：房间/海面的持续低频（-30 dB）。
2. **中景**：风、浪、雨、引擎（-18 dB）。
3. **近场**：靠近麦克风的细节（水珠、呼吸、布料）（-24 dB）。

三层都随时间变化；高潮段把中景推高 6–10 dB，峰值前 0.5s 全抽空。

## 4. 音乐

- **主题动机**：2–4 个音，全片变奏；不要整段铺。
- **Spotting**：标出需要音乐的位置与"进/出"点；对白处让位。
- **动态**：峰值前留白，峰值后一记低频。

## 5. 混音

| 项 | 标准 |
|---|---|
| 整体响度 | -14 LUFS（流媒体）/ -23 LUFS（广播） |
| 真峰值 | ≤ -1 dBTP |
| 对白 | -16 至 -12 LUFS，清晰优先 |
| 音乐/环境 | 比对白低 6–12 dB |
| Ducking | 旁白起时环境降 4–6 dB，释放 300ms |
| 混响 | 室内短混响（IR），干湿比 15–25%；室外 5–10% |
| 声道 | 立体声；可选 5.1（L/R/C/LFE/Ls/Rs） |

**实现参数**（可直接照搬）：节点内视频/配音出声时，音乐降到 **0.25**（约 -12 dB）、**0.4s** 淡出；音乐跨镜延续不重启；浏览器不允许自动播放时，在**第一次点击或按键**启动音频上下文。

```bash
# 两遍 loudnorm（先测后压）
ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -
ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1:LRA=11:measured_I=... -c:a aac -b:a 192k out.m4a
```

## 6. 成片交付

| 方式 | 做法 |
|---|---|
| 浏览器实时播放 | 现有播放器（canvas + Web Audio） |
| 录制导出 | `MediaRecorder`（canvas.captureStream + audio destination）→ WebM |
| 精确导出 | WebCodecs `VideoEncoder` + `AudioEncoder` → MP4（H.264/AAC） |
| 纯 TS 转码/裁剪 | `mediabunny`：`Input+BlobSource → Conversion → Output(Mp4/WebM)`，`CanvasSink` 取帧 |
| 服务端合成 | Playwright 逐帧截图 + ffmpeg 拼接（质量最高，慢） |

交付物：
- `ep01.mp4`（H.264 / AAC / 1080p 或 720p）
- `ep01.srt`（与音频同源）
- 播放器（可交互）
- 响度报告（LUFS/TP）
- 字幕安全区检查（不越界、对比度 ≥4.5:1）

## 7. 验收

- [ ] 整体 -14 LUFS ±0.5，峰值 ≤ -1 dBTP
- [ ] 对白清晰，环境不盖人声
- [ ] 口型对齐 ≤80ms
- [ ] 每个拟音事件与画面动作同帧（±2 帧）
- [ ] 峰值前有静默设计
- [ ] 字幕与音频同源、不越安全区
- [ ] 成片可离线播放，无外部依赖
