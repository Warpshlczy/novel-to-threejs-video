// 成片导出骨架（两种方案，按环境选一种）
// 关键前提：每一帧都必须用 computeState(t) 重建，不能依赖实时播放的累积状态。

/* ------------------------------------------------------------------
 * 方案 A：WebCodecs + mp4-muxer（精确、无音轨录制损耗）
 * 依赖：npm i mp4-muxer
 * ------------------------------------------------------------------ */
export async function exportWithWebCodecs({ canvas, total, fps = 30, renderAt, audioUrl }) {
  const { Muxer, ArrayBufferTarget } = await import('mp4-muxer');
  const muxer = new Muxer({
    target: new ArrayBufferTarget(),
    video: { codec: 'avc', width: canvas.width, height: canvas.height },
    fastStart: 'in-memory',
  });

  const encoder = new VideoEncoder({
    output: (chunk, meta) => muxer.addVideoChunk(chunk, meta),
    error: (e) => { throw e; },
  });
  encoder.configure({
    codec: 'avc1.640028', width: canvas.width, height: canvas.height,
    bitrate: 12_000_000, framerate: fps,
  });

  const frames = Math.ceil(total * fps);
  for (let f = 0; f < frames; f++) {
    const t = f / fps;
    await renderAt(t);                                  // 内部：computeState(t) → 渲染 → 等一帧
    const frame = new VideoFrame(canvas, { timestamp: Math.round((t * 1e6)) });
    encoder.encode(frame, { keyFrame: f % (fps * 2) === 0 });
    frame.close();
    if (f % 30 === 0) await new Promise(requestAnimationFrame); // 让出主线程
  }
  await encoder.flush();
  encoder.close();
  muxer.finalize();

  // 音轨：用 ffmpeg 与画面合成并做响度归一（浏览器内也可用 AudioEncoder）
  // ffmpeg -i video.mp4 -i mix.wav -c:v copy -c:a aac -b:a 192k \
  //        -af loudnorm=I=-14:TP=-1:LRA=11 out.mp4
  return new Blob([muxer.target.buffer], { type: 'video/mp4' });
}

/* ------------------------------------------------------------------
 * 方案 B：MediaRecorder（最简单，画质受实时编码影响）
 * ------------------------------------------------------------------ */
export async function exportWithMediaRecorder({ canvas, total, fps = 30, renderAt, audioStream }) {
  const stream = canvas.captureStream(fps);
  if (audioStream) for (const track of audioStream.getAudioTracks()) stream.addTrack(track);

  const chunks = [];
  const rec = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp9,opus', videoBitsPerSecond: 12_000_000 });
  rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  const done = new Promise((res) => { rec.onstop = res; });

  rec.start(1000);
  const frames = Math.ceil(total * fps);
  for (let f = 0; f < frames; f++) {
    await renderAt(f / fps);
    if (f % 2 === 0) await new Promise(requestAnimationFrame);
  }
  rec.stop();
  await done;
  return new Blob(chunks, { type: 'video/webm' });
}

/* ------------------------------------------------------------------
 * 方案 C：已有视频的裁剪/转码（mediabunny，纯 TS）
 * 参考 ohmygame src/renderer/video-trim.ts 的用法：
 *   Input + BlobSource → Output(Mp4OutputFormat/WebMOutputFormat) + BufferTarget → Conversion
 * ------------------------------------------------------------------ */
export async function trimWithMediabunny({ blob, start, end, keepMp4 = true }) {
  const { Input, BlobSource, Output, BufferTarget, Conversion,
          Mp4OutputFormat, WebMOutputFormat } = await import('mediabunny');

  const input = new Input({ formats: undefined, source: new BlobSource(blob) });
  const output = new Output({
    format: keepMp4 ? new Mp4OutputFormat() : new WebMOutputFormat(),
    target: new BufferTarget(),
  });

  const conversion = await Conversion.init({
    input,
    output,
    trim: { start, end },          // 秒
    // 需要重编码时再设 video/audio 选项；能直通则更快
  });
  await conversion.execute();
  return new Blob([output.target.buffer], { type: keepMp4 ? 'video/mp4' : 'video/webm' });
}

/* ------------------------------------------------------------------
 * 用法要点
 * 1) 导出前先 seek(0)、暂停播放、关掉实时音频调度，避免与导出抢时钟。
 * 2) renderAt 必须等一帧：await new Promise(r => requestAnimationFrame(() => r()))。
 * 3) 码率 ≥12Mbps；暗部多时提到 16–20Mbps。
 * 4) 导出后跑一次 loudnorm，并抽查首/中/尾三帧与播放器一致。
 * ------------------------------------------------------------------ */
