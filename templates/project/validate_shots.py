#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分镜 / 资产 / 时间轴校验器（改稿即跑）

用法：
  python3 tools/validate_shots.py design/story.json
退出码：0 = 全绿（可能有 warning），1 = 有 error。

规则来源：references/cinematic-staging.md 与 SKILL.md 的叙事门。
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

CHARS_PER_SEC = 4.5     # 中文估算语速；有实测时长时以实测为准
errors: list[str] = []
warns: list[str] = []


def err(msg: str):
    errors.append(msg)


def warn(msg: str):
    warns.append(msg)


def main(path: str) -> int:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    meta = d.get("meta", {})
    shots = d.get("shots", [])
    lines = d.get("lines", [])
    total = float(meta.get("duration", 0))
    chars = {c["id"] for c in d.get("characters", [])}
    locs = {l["id"] for l in d.get("locations", [])}
    props = {p["id"] for p in d.get("props", [])}
    assets = chars | locs | props

    if not shots:
        err("没有任何镜头")
    if total <= 0:
        err("meta.duration 缺失或 <= 0")

    # 1) 必填字段与时间连续性
    prev_end = 0.0
    for i, s in enumerate(shots):
        for k in ("id", "start", "end", "shotSize", "cutReason"):
            if s.get(k) in (None, ""):
                err(f"{s.get('id', f'#{i}')} 缺必填字段 {k}")
        if s.get("start", 0) < prev_end - 1e-6:
            err(f"{s['id']} 与上一镜重叠（start {s['start']} < prev end {prev_end}）")
        if s.get("end", 0) <= s.get("start", 0):
            err(f"{s['id']} 时长 <= 0")
        if len(str(s.get("cutReason", ""))) < 2:
            err(f"{s['id']} cutReason 过短：{s.get('cutReason')!r}")
        prev_end = s.get("end", prev_end)

    if abs(prev_end - total) > 0.05:
        err(f"镜头总长 {prev_end:.2f}s 与 meta.duration {total:.2f}s 不一致")

    # 2) 景别节奏
    for a, b in zip(shots, shots[1:]):
        if a.get("shotSize") == b.get("shotSize") and a.get("angle") == b.get("angle"):
            warn(f"{a['id']} → {b['id']} 景别与角度都相同，可能跳帧")

    # 3) 覆盖镜头：每场至少一个 coverage 或插入/反应镜
    scenes = {}
    for s in shots:
        scenes.setdefault(s.get("scene", "default"), []).append(s)
    for sc, ss in scenes.items():
        if len(ss) >= 2 and not any(s.get("coverage") for s in ss):
            warn(f"场次 {sc} 没有任何 coverage（插入/反应/空镜）")

    # 4) 轴线：同场 cameraSide 翻转必须有说明
    for sc, ss in scenes.items():
        sides = [s.get("cameraSide") for s in ss if s.get("cameraSide")]
        if len(set(sides)) > 1:
            for s in ss:
                if s.get("cameraSide") in ("A", "B") and "越轴" not in str(s.get("cutReason", "")):
                    warn(f"场次 {sc} 的 {s['id']} 疑似越轴（cameraSide={s['cameraSide']}），cutReason 未说明")

    # 5) 对白占比
    by_shot = {}
    for ln in lines:
        by_shot.setdefault(ln.get("shot"), []).append(ln)
    for s in shots:
        ls = by_shot.get(s["id"], [])
        if not ls:
            continue
        dur = 0.0
        for ln in ls:
            dur += ln.get("duration") or len(ln.get("voice") or ln.get("sub", "")) / CHARS_PER_SEC
        win = s["end"] - s["start"]
        if win > 0 and dur / win > 0.75:
            warn(f"{s['id']} 对白占比 {dur / win:.0%}（>75%），留给表演的空间不足")

    # 6) 资产引用
    for s in shots:
        for a in s.get("assets", []):
            if a not in assets:
                err(f"{s['id']} 引用了未登记的资产 {a}")

    # 7) 台词指向存在的镜头
    ids = {s["id"] for s in shots}
    for ln in lines:
        if ln.get("shot") not in ids:
            err(f"台词 {ln.get('id')} 指向不存在的镜头 {ln.get('shot')}")

    # 8) 伏笔三处
    for p in d.get("props", []):
        clue = p.get("clue", [])
        if clue and set(clue) != {"setup", "reinforce", "payoff"}:
            warn(f"道具 {p['id']} 线索不完整：{clue}（应为 setup/reinforce/payoff）")

    # 9) 节奏统计
    durs = [s["end"] - s["start"] for s in shots]
    if durs:
        avg = sum(durs) / len(durs)
        print(f"镜头数 {len(shots)} · 平均 {avg:.2f}s · 最短 {min(durs):.2f}s · 最长 {max(durs):.2f}s")
        print(f"景别分布 {dict(Counter(s.get('shotSize') for s in shots))}")
        if avg > 6:
            warn(f"平均镜长 {avg:.1f}s 偏长，考虑补覆盖镜头")

    for w in warns:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")
    print(f"\n结果：{len(errors)} error / {len(warns)} warning")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "design/story.json"))
