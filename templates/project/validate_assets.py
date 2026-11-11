#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产门校验器（asset gate）

校验「资产等级 vs 镜头画幅」以及资产本身的质量阈值。
与 validate_shots.py 分工：它管叙事/轴线/节奏；本脚本管资产能力。

用法：
  python3 tools/validate_assets.py design/story.json
  python3 tools/validate_assets.py design/story.json --lock quality.lock.json --manifest assets/manifest.json

退出码：0 = 通过（可有 warning），1 = 有 error。
grade=prototype 时放宽资产门（只保留结构与引用检查）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SHOT_ORDER = ["ELS", "LS", "MLS", "MS", "MCU", "CU", "ECU"]
TIER_ORDER = ["T0", "T1", "T2", "T3"]
KIND_OF_SECTION = {"characters": "character", "locations": "location", "props": "prop"}

errors: list[str] = []
warns: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warns.append(msg)


def tier_rank(t: str | None) -> int:
    return TIER_ORDER.index(t) if t in TIER_ORDER else -1


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_file(start: Path, rel: str) -> Path | None:
    for base in (start, start.parent, start.parent.parent):
        p = base / rel
        if p.exists():
            return p
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("story", nargs="?", default="design/story.json")
    ap.add_argument("--lock", default="")
    ap.add_argument("--manifest", default="")
    args = ap.parse_args()

    story_path = Path(args.story)
    if not story_path.exists():
        print(f"找不到 {story_path}")
        return 1
    story = load_json(story_path)
    base = story_path.parent.parent if story_path.parent.name == "design" else story_path.parent

    lock_path = Path(args.lock) if args.lock else (find_file(base, "quality.lock.json") or find_file(story_path.parent, "quality.lock.json"))
    lock = load_json(lock_path) if lock_path and lock_path.exists() else {}
    grade = lock.get("grade", "production")
    relaxed = grade == "prototype"

    manifest_path = Path(args.manifest) if args.manifest else (find_file(base, "assets/manifest.json"))
    manifest = {}
    if manifest_path and manifest_path.exists():
        manifest = {a["id"]: a for a in load_json(manifest_path).get("assets", [])}

    # 台账：story 登记 + manifest 合并（manifest 优先）
    registry: dict[str, dict] = {}
    for section, kind in KIND_OF_SECTION.items():
        for item in story.get(section, []):
            registry[item["id"]] = {**item, "kind": kind}
    for aid, m in manifest.items():
        registry[aid] = {**registry.get(aid, {}), **m}

    shots = story.get("shots", [])
    tier_rules = lock.get("tierRules", {})
    budgets = lock.get("budgets", {})
    asset_rules = lock.get("assets", {})
    required_maps = lock.get("requiredMaps", {})

    # 1) 结构：tier / license / 引用
    for aid, a in registry.items():
        if not a.get("tier"):
            (warn if relaxed else err)(f"资产 {aid} 缺 tier（缺省视为 T0，不能进成片）")
        elif a["tier"] == "T0" and not relaxed:
            err(f"资产 {aid} 为 T0（blocking），不得进入成片")
        if not a.get("license"):
            (warn if relaxed else err)(f"资产 {aid} 缺 license")

    shot_ids = {s["id"] for s in shots}
    for s in shots:
        for aid in s.get("assets", []):
            if aid not in registry and not aid.startswith(("cam_", "fx_")):
                warn(f"{s['id']} 引用了未登记资产 {aid}")

    # 2) 画幅 vs 资产等级
    cu_ecu = 0
    tele = 0
    for s in shots:
        size = s.get("shotSize")
        lens = s.get("lens", 0) or 0
        if size in ("CU", "ECU"):
            cu_ecu += 1
        if lens >= 85:
            tele += 1
        if relaxed or not size:
            continue

        refs = [registry.get(a) for a in s.get("assets", []) if registry.get(a)]
        chars = [a for a in refs if a.get("kind") == "character"]
        subject = max((tier_rank(a.get("tier")) for a in (chars or refs) if a.get("tier")), default=-1)
        declared = s.get("subjectTier")
        if declared:
            if tier_rank(declared) > subject:
                err(f"{s['id']} 声明 subjectTier={declared}，但实际主体最高只有 {TIER_ORDER[max(subject, 0)]}")
            subject = min(tier_rank(declared), subject) if subject >= 0 else tier_rank(declared)

        if size in ("CU", "ECU") and chars:
            for a in chars:
                if a.get("tier") != "T3":
                    err(f"{s['id']} 是 {size}，但角色 {a['id']} 为 {a.get('tier')}（CU/ECU 需要 T3）")
        if lens >= 85 and subject < tier_rank("T2"):
            err(f"{s['id']} 用 {lens}mm，主体等级不足 T2")

        allowed = tier_rules.get(TIER_ORDER[max(subject, 0)], {}).get("maxShotSize") if subject >= 0 else None
        if allowed and size in SHOT_ORDER and SHOT_ORDER.index(size) > SHOT_ORDER.index(allowed):
            err(f"{s['id']} 景别 {size} 超出主体等级上限 {allowed}")

    # 3) 配额
    if shots and not relaxed:
        ratio = cu_ecu / len(shots)
        if ratio > budgets.get("maxCuEcuRatio", 0.25):
            warn(f"CU+ECU 占比 {ratio:.0%}，超过 {budgets.get('maxCuEcuRatio', 0.25):.0%}（除非主角色全 T3）")
        tr = tele / len(shots)
        if tr > budgets.get("maxTeleRatio", 0.3):
            warn(f"85mm+ 占比 {tr:.0%}，超过 {budgets.get('maxTeleRatio', 0.3):.0%}")

    # 4) 资产阈值
    if not relaxed:
        for aid, a in registry.items():
            kind = a.get("kind")
            tier = a.get("tier")
            if kind not in asset_rules or not tier:
                continue
            rules = asset_rules[kind]
            mx = rules.get("maxTris", {}).get(tier)
            if mx and a.get("tris") and a["tris"] > mx:
                err(f"{aid} 三角面 {a['tris']} 超过 {tier} 上限 {mx}")
            min_bones = rules.get("minBones", {}).get(tier)
            if min_bones and a.get("bones") is not None and a["bones"] < min_bones:
                err(f"{aid} 骨骼 {a['bones']} < {tier} 要求 {min_bones}")
            min_bs = rules.get("minBlendshapes", {}).get(tier)
            if min_bs and (a.get("blendshapes") or 0) < min_bs:
                err(f"{aid} blendshape {(a.get('blendshapes') or 0)} < {tier} 要求 {min_bs}")
            min_texel = rules.get("minTexelDensity", {}).get(tier)
            if min_texel and a.get("texelDensity") and a["texelDensity"] < min_texel:
                err(f"{aid} 纹素密度 {a['texelDensity']} < {tier} 要求 {min_texel}")
            need = required_maps.get(kind)
            procedural = a.get("model") == "procedural" or a.get("route") == "procedural"
            if need and contiguous(a) and not procedural and not set(need).issubset(set(a.get("maps") or [])):
                err(f"{aid} 缺贴图：{sorted(set(need) - set(a.get('maps') or []))}")
            if kind == "character" and a.get("model") == "procedural" and not budgets.get("allowProceduralHero", False):
                err(f"{aid} 使用 procedural 角色；如确为风格化请显式设 allowProceduralHero=true")

    # 5) 配音引擎
    audio = lock.get("audio", {})
    banned = set(audio.get("bannedEngines", []))
    for key, v in story.get("voices", {}).items():
        eng = str(v.get("engine", "")).lower()
        if eng and eng in banned:
            (warn if relaxed else err)(f"音色 {key} 使用被禁引擎 {eng}（{grade} 档要求 {audio.get('minEngine', 'neural')}）")

    for w in warns:
        print(f"[WARN]  {w}")
    for e in errors:
        print(f"[ERROR] {e}")
    print(f"\ngrade={grade} · {len(registry)} 资产 · {len(shots)} 镜 · {len(errors)} error / {len(warns)} warning")
    return 0 if not errors else 1


def contiguous(a: dict) -> bool:
    """只有 manifest 记录的资产才校验贴图，避免对纯登记项误报。"""
    return bool(a.get("file") or a.get("hash"))


if __name__ == "__main__":
    sys.exit(main())
