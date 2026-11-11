# 配音、声音与成片交付

> 目标：让声音承担一半的叙事，让成片能直接播、能上平台。
> 顺序：**音色设计 → 配音合成 → 对齐/口型 → 拟音 → 环境 → 音乐 → 混音 → 交付**。

## 1. 配音引擎（按质量排序）

| 引擎 | 类型 | 中文 | 音色克隆 | 情绪控制 | 许可 | 接入 |
|---|---|---|---|---|---|---|
| IndexTTS 2.5 | 神经 | 强 | 零样本（3–10s 参考音） | 时长/情绪解耦 | bilibili 模型许可（核对商用） | 本地 GPU / HTTP 服务 |
| CosyVoice 3 | 神经 | 强 | 零样本 | 指令控制 | Apache 2.0 | 本地 GPU / HTTP |
| GPT-SoVITS | 神经 | 强 | 少样本微调 | 参考音决定 | MIT | 本地 GPU |
| Fish-Speech | 神经 | 强 | 零样本 | 参考音决定 | 社区许可（营收阈值） | 本地 GPU / 托管 |
| Chatterbox | 神经 | 中 | 零样本 | 有限 | MIT | 本地 GPU |
| VibeVoice | 神经 | 中 | 长对话 | 有限 | MIT | 本地 GPU |
| edge-tts | 云端神经 | 强 | 无 | SSML 有限 | 服务条款 | `edge-tts` CLI，免费 |
| macOS `say` / espeak | 波形拼接 | 中 | 无 | 无 | 系统 | 离线，**仅 prototype** |

**档位门禁**

| 档 | 允许的引擎 |
|---|---|
| prototype | 任意（`say` / `edge-tts`） |
| production | 神经引擎（edge-tts 及以上） |
| hero | IndexTTS 2.5 / CosyVoice 3 / GPT-SoVITS + 人工校听 |

> `say` 的问题是韵律：中文多音字、停顿、气口、重音全靠猜，句与句之间能量不连续。它不是"差一点的配音"，是"另一种东西"。

## 2. 音色设计（先定，再合成）

每个角色在 `design/voice.json` 里锁一份音色档案：

```jsonc
{
  "lead": {
    "engine": "indextts",
    "refAudio": "assets/voice/ref_lead.wav",   // 3–10s 干净人声
    "gender": "male", "age": 28,
    "timbre": "偏低、略沙、胸腔共鸣",
    "pace": 0.95,
    "emotionDefault": "calm",
    "notes": "句尾不上扬；情绪压在字下面"
  }
}
```

- **参考音**：3–10 秒、无混响、无背景音乐、单一说话人。
- **一致性**：全片同一角色用同一参考音 + 同一引擎版本；不要中途换引擎。
- **区分度**：主角与配角在音高/语速/音色上至少差两项，观众才能闭眼分辨。

## 3. 情绪标注

在 `lines` 里逐句标：

```jsonc
{ "id": "V07", "shot": "S12", "speaker": "lead", "sub": "……", "emotion": "tense", "intensity": 0.6, "pauseAfter": 0.4 }
```

| 标注 | 合成处理 |
|---|---|
| `calm` | 基准语速，句尾降 |
| `tense` | 语速 +8%，句间缩短，气口变浅 |
| `broken` | 语速 -12%，加停顿，音量 -3dB |
| `whisper` | 音量 -12dB，气声比例提高（需引擎支持） |
| `shout` | 音量 +3dB，语速 +5%，慎用（易破音） |

- `intensity` 0–1，用于插值；不要一句一个极端值。
- **停顿是表演**：`pauseAfter` 0.2–0.6s；峰值前留 0.8s 静默。

## 4. 自动配音流水线

```bash
# 1) 合成（示例：edge-tts 兜底；生产换 IndexTTS/CosyVoice HTTP）
edge-tts --voice zh-CN-YunxiNeural \
  --text "台词文本" \
  --write-media assets/audio/V01.mp3

# 2) 统一采样率与响度（对白单独归一，不跟音乐一起压）
ffmpeg -y -i assets/audio/V01.mp3 -ar 48000 -ac 1 assets/audio/V01.wav
ffmpeg -i assets/audio/V01.wav -af loudnorm=I=-18:TP=-2:LRA=7 -ar 48000 assets/audio/V01.norm.wav

# 3) 词级对齐（字幕 + 口型共用）
whisperx assets/audio/V01.norm.wav --model large-v3 --language zh \
  --output_format json --output_dir assets/audio/aligned

# 4) viseme（离线查表）
rhubarb -f json -o assets/visemes/V01.json assets/audio/V01.norm.wav

# 5) 整轨混音后统一到交付响度
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 assets/audio/mix.norm.wav
```

**批量规则**

- 逐句合成，逐句缓存；用文本 hash 命名，改一句只重跑一句。
- 句间留 0.2–0.5s；同一角色连续台词不要每句单独归一（会"一句一个音量"），按场景整段归一。
- 字幕与朗读分离：字幕保留原文（缩写、术语），朗读用可读写法（`voice` 字段）。

## 5. 拟音（Foley）事件表

每个声音事件写进时间轴，跟 `t` 对齐：

```jsonc
[
  { "t": 12.4, "event": "mug_set_down", "layer": "foley", "gain": -18 },
  { "t": 39.2, "event": "wind_hit",     "layer": "foley", "gain": -8 },
  { "t": 47.0, "event": "metal_creak",  "layer": "foley", "gain": -14 },
  { "t": 66.4, "event": "silence",      "layer": "master", "gain": -60 }
]
```

常见层：脚步、衣物摩擦、金属吱嘎、水拍、门轴、无线电噪声、心跳、耳鸣。
来源：Freesound（CC0/CC-BY）、自制拟音、生成式音效（记录模型与许可）。

## 6. 环境（三层）

1. **底噪**：房间/室外的持续低频（-30 dB）。
2. **中景**：风、雨、引擎、人群（-18 dB）。
3. **近场**：靠近麦克风的细节（水珠、呼吸、布料）（-24 dB）。

三层都随时间变化；高潮段把中景推高 6–10 dB，峰值前 0.5s 全抽空。

## 7. 音乐

- **主题动机**：2–4 个音，全片变奏；不要整段铺。
- **Spotting**：标出需要音乐的位置与"进/出"点；对白处让位。
- **动态**：峰值前留白，峰值后一记低频。

## 8. 混音

| 项 | 标准 |
|---|---|
| 整体响度 | -14 LUFS（流媒体）/ -23 LUFS（广播） |
| 真峰值 | ≤ -1 dBTP |
| 对白 | -16 至 -12 LUFS，清晰优先 |
| 音乐/环境 | 比对白低 6–12 dB |
| Ducking | 旁白起时环境降 4–6 dB，释放 300ms |
| 混响 | 室内短混响（IR），干湿比 15–25%；室外 5–10% |
| 声道 | 立体声；可选 5.1（L/R/C/LFE/Ls/Rs） |

**实现参数**：节点内视频/配音出声时，音乐降到 **0.25**（约 -12 dB）、**0.4s** 淡出；音乐跨镜延续不重启；浏览器不允许自动播放时，在**第一次点击或按键**启动音频上下文。

```bash
# 两遍 loudnorm（先测后压）
ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -
ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1:LRA=11:measured_I=... -c:a aac -b:a 192k out.m4a
```

## 9. 成片交付

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

## 10. 验收

- [ ] 整体 -14 LUFS ±0.5，峰值 ≤ -1 dBTP
- [ ] production 档未使用系统 TTS
- [ ] 同一角色全片同一音色（引擎 + 参考音 + 版本）
- [ ] 对白清晰，环境不盖人声
- [ ] 口型对齐 ≤80ms
- [ ] 每个拟音事件与画面动作同帧（±2 帧）
- [ ] 峰值前有静默设计
- [ ] 字幕与音频同源、不越安全区
- [ ] 成片可离线播放，无外部依赖
