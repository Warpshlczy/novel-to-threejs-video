#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用配音 / 字幕 / 时间轴构建器

读 design/story.json（唯一源），产出：
  assets/audio/*.mp3       离线 TTS（macOS say + ffmpeg）
  assets/subtitles/ep.srt  与音频同源的字幕
  src/story.js             前端唯一数据源（含实测 start/end）
  qa/build-report.json     构建报告

规则：
  * 对白时长用 ffmpeg 实测，不按字数估算
  * 语音总长超出目标时：先提语速（≤1.45x），仍超则按 optional 优先级删台词
  * 镜头窗按实测需求重排，并把所有 curves / events 的设计时间按镜头比例 remap

用法：
  python3 tools/build_timeline.py [--reuse]
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "design"
AUDIO = ROOT / "assets" / "audio"
SUBS = ROOT / "assets" / "subtitles"
SRC = ROOT / "src"
QA = ROOT / "qa"
for d in (AUDIO, SUBS, SRC, QA):
    d.mkdir(parents=True, exist_ok=True)

REUSE = "--reuse" in sys.argv
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
STORY = json.loads((DESIGN / "story.json").read_text(encoding="utf-8"))
TOTAL = float(STORY["meta"]["duration"])
MIN_GAP = 0.22
TAIL = 0.25          # 每镜尾部留白
TAIL_LAST = 1.8      # 末镜留给标题卡


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duration(path: Path) -> float:
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", run([FFMPEG, "-i", str(path)]).stderr)
    if not m:
        raise RuntimeError(f"无法读取时长: {path}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def synth(line: dict, rate_scale: float) -> float:
    mp3 = AUDIO / f"{line['id']}.mp3"
    if REUSE and mp3.exists():
        return duration(mp3)
    vcfg = STORY["voices"][line["voiceKey"]]
    rate = max(120, min(300, round(int(line.get("rate", vcfg["rate"])) * rate_scale)))
    text = line.get("voice") or line["sub"]
    with tempfile.TemporaryDirectory(prefix="tts-") as td:
        aiff = Path(td) / f"{line['id']}.aiff"
        for voice in (vcfg["name"], vcfg.get("fallback", vcfg["name"])):
            r = run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text])
            if r.returncode == 0 and aiff.exists():
                break
        else:
            raise RuntimeError(f"TTS 失败: {line['id']}")
        c = run([FFMPEG, "-y", "-loglevel", "error", "-i", str(aiff),
                 "-codec:a", "libmp3lame", "-qscale:a", "4", str(mp3)])
        if c.returncode != 0:
            raise RuntimeError(f"转码失败: {line['id']}")
    line["_rate"], line["_voice"] = rate, voice
    return duration(mp3)


def by_shot(lines):
    out = {s["id"]: [] for s in STORY["shots"]}
    for ln in lines:
        out[ln["shot"]].append(ln)
    return out


def min_total(durs, lines):
    return sum(durs[l["id"]] for l in lines) + MIN_GAP * len(lines) + TAIL_LAST + TAIL * (len(STORY["shots"]) - 1)


# 1) 合成 + 自适应
lines = [dict(l) for l in STORY["lines"]]
scale, durs, dropped, notes = 1.0, {}, [], []
for _ in range(6):
    durs = {l["id"]: synth(l, scale) for l in lines}
    need = min_total(durs, lines)
    if need <= TOTAL - 1.0:
        notes.append(f"scale={scale:.2f} speech={sum(durs.values()):.2f}s need={need:.2f}s")
        break
    if scale < 1.45:
        scale += 0.10
    else:
        cand = sorted([l for l in lines if l.get("optional", 0) > 0], key=lambda l: -l["optional"])
        if not cand:
            raise RuntimeError("压稿后仍超时，且无可删台词")
        victim = cand[0]
        lines.remove(victim)
        dropped.append(victim["id"])
        durs.pop(victim["id"], None)
        notes.append(f"drop {victim['id']} to fit {TOTAL}s")
else:
    raise RuntimeError("语速自适应未收敛")

groups = by_shot(lines)
speech = {sid: sum(durs[l["id"]] for l in ls) for sid, ls in groups.items()}
need = {sid: speech[sid] + MIN_GAP * len(groups[sid]) + (TAIL_LAST if sid == STORY["shots"][-1]["id"] else TAIL)
        for sid in groups}

# 2) 镜头窗：按需求重排（保持顺序与总时长）
slack = TOTAL - sum(need.values())
weights = {sid: 1.0 for sid in groups}
for sid in weights:
    if any(k in sid for k in ("S1", "S2")):
        weights[sid] = 1.3          # 铺陈多留白
wsum = sum(weights.values())
windows = {sid: need[sid] + slack * weights[sid] / wsum for sid in groups}

shots_out, cursor = [], 0.0
for s in STORY["shots"]:
    o = dict(s)
    o["start"] = round(cursor, 3)
    o["end"] = TOTAL if s["id"] == STORY["shots"][-1]["id"] else round(cursor + windows[s["id"]], 3)
    cursor = o["end"]
    shots_out.append(o)

DESIGN_SHOTS = STORY["shots"]


def remap(t: float) -> float:
    for i, (ds, fs) in enumerate(zip(DESIGN_SHOTS, shots_out)):
        if t <= ds["end"] or i == len(DESIGN_SHOTS) - 1:
            span = ds["end"] - ds["start"]
            u = 0 if span <= 0 else max(0.0, min(1.0, (t - ds["start"]) / span))
            return round(fs["start"] + u * (fs["end"] - fs["start"]), 3)
    return round(t, 3)


# 3) 台词时间
subs = []
for s in shots_out:
    ls = groups[s["id"]]
    if not ls:
        continue
    win = s["end"] - s["start"]
    tail = TAIL_LAST if s["id"] == shots_out[-1]["id"] else TAIL
    gap = max(MIN_GAP, (win - speech[s["id"]] - tail) / max(1, len(ls)))
    t = s["start"] + gap * 0.55
    for ln in ls:
        d = durs[ln["id"]]
        o = {k: v for k, v in ln.items() if not k.startswith("_") and k != "optional"}
        o.update(start=round(t, 3), end=round(t + d, 3), duration=round(d, 3),
                 file=f"assets/audio/{ln['id']}.mp3",
                 rate=ln.get("_rate"), ttsVoice=ln.get("_voice"))
        subs.append(o)
        t += d + gap

# 4) 输出
out = {
    "meta": STORY["meta"], "palette": STORY.get("palette", {}),
    "characters": STORY.get("characters", []), "locations": STORY.get("locations", []),
    "props": STORY.get("props", []),
    "shots": shots_out,
    "lines": subs,
    "events": [{**e, "t": remap(e.get("t", e.get("from", 0))),
                **({"from": remap(e["from"])} if "from" in e else {}),
                **({"to": remap(e["to"])} if "to" in e else {})} for e in STORY.get("events", [])],
    "curves": {k: [[remap(p), v] for p, v in pts] for k, pts in STORY.get("curves", {}).items()},
    "build": {"total": TOTAL, "speech": round(sum(durs.values()), 3),
              "rateScale": round(scale, 2), "dropped": dropped},
}
(SRC / "story.js").write_text(
    "// generated by tools/build_timeline.py — do not edit\n"
    "export const STORY = " + json.dumps(out, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


srt = []
for i, ln in enumerate(subs, 1):
    prefix = "" if ln.get("type") == "VO" else f"{ln['speaker']}："
    srt.append(f"{i}\n{ts(ln['start'])} --> {ts(ln['end'])}\n{prefix}{ln['sub']}\n")
(SUBS / "ep.srt").write_text("\n".join(srt), encoding="utf-8")

report = {"status": "PASS", "total": TOTAL, "speech": round(sum(durs.values()), 3),
          "lines": len(subs), "dropped": dropped, "notes": notes,
          "shots": {s["id"]: [s["start"], s["end"]] for s in shots_out}}
(QA / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"✅ {len(subs)} 段 / 语音 {sum(durs.values()):.2f}s / 总 {TOTAL:.1f}s / scale {scale:.2f} / 删 {dropped or '无'}")
for s in shots_out:
    print(f"   {s['id']:>3} {s['start']:6.2f}–{s['end']:6.2f}  {s.get('beat', '')[:28]}")
