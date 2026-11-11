#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产生产计划器（S2 → S3）

读 design/asset-plan.json，产出：
  assets/manifest.json     资产台账（id / tier / provider / seed / hash / status）
  assets/jobs/<id>.json    单资产作业单（可交给人工或外部流水线）
  assets/CREDITS.md        来源与许可汇总（不覆盖已有内容）

规则：
  * 不猜、不下载、不调未知 API；provider 只在 asset-plan 里声明
  * 已存在且 hash 一致的资产默认跳过（可复现、省成本）
  * 所有生成资产必须记录 prompt + seed + 模型版本，否则拒绝入账

用法：
  python3 tools/build_assets.py --plan design/asset-plan.json          # 只出计划与台账
  python3 tools/build_assets.py --plan design/asset-plan.json --run    # 执行 kind=local/manual 的命令
  python3 tools/build_assets.py --verify                               # 校验既有文件 hash
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parent if _HERE.name == "tools" else _HERE
ID_RE = re.compile(r"^(chr|prop|env)_[a-z0-9_]+$")
KIND_PREFIX = {"character": "chr_", "prop": "prop_", "location": "env_"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def stable_seed(asset_id: str) -> int:
    return int(hashlib.sha256(asset_id.encode()).hexdigest()[:8], 16) % 2_000_000_000


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"缺少 {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate(plan: dict) -> list[str]:
    errs: list[str] = []
    if plan.get("version") != 1:
        errs.append("version 必须为 1")
    seen: set[str] = set()
    for a in plan.get("assets", []):
        aid = a.get("id", "")
        if not ID_RE.match(aid):
            errs.append(f"{aid or '(空 id)'} 命名不合规（应为 chr_/prop_/env_ + 小写）")
        if aid in seen:
            errs.append(f"{aid} 重复登记")
        seen.add(aid)
        kind = a.get("kind")
        if kind not in KIND_PREFIX:
            errs.append(f"{aid} kind 非法：{kind}")
        elif not aid.startswith(KIND_PREFIX[kind]):
            errs.append(f"{aid} 前缀与 kind={kind} 不匹配")
        if a.get("tier") not in {"T0", "T1", "T2", "T3"}:
            errs.append(f"{aid} 缺 tier 或值非法")
        if not a.get("out"):
            errs.append(f"{aid} 缺 out 路径")
        if a.get("route") in {"image-to-3d", "hybrid"}:
            if not a.get("prompt"):
                errs.append(f"{aid} 生成资产必须保存 prompt")
            if not a.get("refs"):
                errs.append(f"{aid} 生成资产必须保存 refs（参考图）")
        if a.get("route") not in {"procedural", "vrm", "cc0", "image-to-3d", "scan", "hybrid"}:
            errs.append(f"{aid} route 非法：{a.get('route')}")
        if not a.get("license"):
            errs.append(f"{aid} 缺 license")
    return errs


def provider_chain(asset: dict, providers: dict) -> list[dict]:
    route = asset.get("route")
    if route in {"vrm", "cc0", "procedural", "manual"}:
        keys = ["asset"]
    elif route == "image-to-3d":
        keys = ["image", "mesh"]
    elif route == "hybrid":
        keys = ["image", "mesh", "rig"]
    elif route == "scan":
        keys = ["scan"]
    else:
        keys = ["asset"]
    if asset.get("rig") not in (None, "none"):
        keys = keys + ["rig"]
    chain = []
    for k in keys:
        p = providers.get(k)
        if not p:
            continue
        chain.append({"stage": k, **p})
    return chain


def job_sheet(asset: dict, chain: list[dict], out_path: Path) -> dict:
    return {
        "id": asset["id"],
        "kind": asset["kind"],
        "tier": asset["tier"],
        "route": asset.get("route"),
        "prompt": asset.get("prompt", ""),
        "refs": asset.get("refs", []),
        "seed": asset.get("seed", stable_seed(asset["id"])),
        "target": {
            "out": asset.get("out"),
            "tris": asset.get("targetTris"),
            "texelDensity": asset.get("texelDensity"),
            "maps": asset.get("maps", []),
            "rig": asset.get("rig", "none"),
            "blendshapes": asset.get("blendshapes", 0),
            "size": asset.get("size"),
        },
        "chain": chain,
        "license": asset.get("license"),
        "lock": asset.get("lock", ""),
        "status": "ready" if out_path.exists() else "pending",
    }


def run_command(template: str, asset: dict, out_path: Path) -> tuple[bool, str]:
    cmd = template.format(
        prompt=shlex.quote(asset.get("prompt", "")),
        out=shlex.quote(str(out_path)),
        ref=shlex.quote(asset["refs"][0] if asset.get("refs") else ""),
        seed=asset.get("seed", stable_seed(asset["id"])),
    )
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT)
    return r.returncode == 0, (r.stderr or r.stdout)[-800:]


def write_credits(entries: list[dict]) -> None:
    path = ROOT / "assets" / "CREDITS.md"
    header = "# 资产来源与许可\n\n| 资产 | 等级 | 来源 | 许可 |\n|---|---|---|---|\n"
    rows = "".join(
        f"| `{e['id']}` | {e['tier']} | {e.get('source', e.get('route', '-'))} | {e.get('license', '-')} |\n"
        for e in entries
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + rows, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="design/asset-plan.json")
    ap.add_argument("--run", action="store_true", help="执行 kind=local/manual 的命令")
    ap.add_argument("--verify", action="store_true", help="只校验既有文件 hash")
    args = ap.parse_args()

    plan_path = ROOT / args.plan
    plan = load(plan_path)
    providers = plan.get("providers", {})
    assets = plan.get("assets", [])

    errs = validate(plan)
    if errs:
        for e in errs:
            print(f"[ERROR] {e}")
        print(f"\n计划无效：{len(errs)} error")
        return 1

    manifest_path = ROOT / "assets" / "manifest.json"
    old = {}
    if manifest_path.exists():
        try:
            old = {e["id"]: e for e in json.loads(manifest_path.read_text(encoding="utf-8"))["assets"]}
        except Exception:
            old = {}

    jobs_dir = ROOT / "assets" / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    failed = 0
    for a in assets:
        out_path = ROOT / a["out"]
        chain = provider_chain(a, providers)
        job = job_sheet(a, chain, out_path)
        (jobs_dir / f"{a['id']}.json").write_text(
            json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if args.run and not out_path.exists():
            for stage in chain:
                cmd = stage.get("command")
                if stage.get("kind") in {"local", "manual"} and cmd:
                    ok, log = run_command(cmd, a, out_path)
                    print(f"[{'OK' if ok else 'FAIL'}] {a['id']} · {stage['stage']} · {cmd[:60]}")
                    if not ok:
                        failed += 1
                        print(log)
                        break
        elif args.run and out_path.exists():
            print(f"[SKIP] {a['id']} 已存在（hash 一致即复用）")

        digest = sha256(out_path) if out_path.exists() else None
        prev = old.get(a["id"], {})
        entry = {
            "id": a["id"],
            "kind": a["kind"],
            "tier": a["tier"],
            "route": a.get("route"),
            "source": a.get("route", "unknown"),
            "file": a["out"],
            "hash": digest,
            "size": a.get("size"),
            "tris": a.get("targetTris"),
            "bones": (a.get("bones") if "bones" in a else prev.get("bones")),
            "blendshapes": a.get("blendshapes", 0),
            "texelDensity": a.get("texelDensity"),
            "maps": a.get("maps", []),
            "license": a.get("license"),
            "prompt": a.get("prompt", ""),
            "seed": job["seed"],
            "derivedFrom": a.get("derivedFrom", []),
            "lock": a.get("lock", ""),
            "status": "ready" if digest else "pending",
            "provider": [f"{s['stage']}:{s.get('model', s.get('kind'))}" for s in chain],
        }
        if args.verify and prev.get("hash") and digest and prev["hash"] != digest:
            print(f"[ERROR] {a['id']} hash 不一致：{prev['hash']} != {digest}")
            failed += 1
        entries.append(entry)

    if not args.verify:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "grade": plan.get("grade", "production"),
                    "assets": entries,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        write_credits(entries)

    ready = sum(1 for e in entries if e["status"] == "ready")
    print(f"\n{len(entries)} 个资产 · ready {ready} · pending {len(entries) - ready} · failed {failed}")
    if not args.verify:
        print(f"台账 {manifest_path.relative_to(ROOT)} · 作业单 {jobs_dir.relative_to(ROOT)}/")
    for e in entries:
        flag = "✓" if e["status"] == "ready" else "·"
        print(f"  {flag} {e['id']:<22} {e['tier']}  {e['route'] or '-':<12} {e['file']}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
