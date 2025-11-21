#!/usr/bin/env python3
"""
Parse NDJSON produced by GA runs and create PNG plots + CSV summary.

Saves to `backend/tmp/` by default:
- ga_hard_test_best_avg.png
- ga_hard_test_components.png
- ga_hard_test_penalties.png
- ga_hard_test_summary.csv

Usage:
  python plot_ga_ndjson.py [--input PATH] [--outdir PATH]

This script will attempt to install `matplotlib` if it's missing in the current
environment using `python -m pip install matplotlib`.
"""
from __future__ import annotations
import json
import sys
import csv
from pathlib import Path
import subprocess


def ensure_matplotlib():
    try:
        import matplotlib  # type: ignore
        return
    except Exception:
        print("matplotlib not found; installing via pip...", flush=True)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"]) 


def parse_ndjson(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            # we expect event ga_gen_stat but tolerate other entries
            meta = obj.get("meta", {})
            gen = meta.get("gen")
            fitness = obj.get("fitness", {})
            best = fitness.get("best")
            avg = fitness.get("avg")
            comps = fitness.get("best_components", {}) or {}
            row = {
                "gen": gen,
                "best": best,
                "avg": avg,
                "conflict": comps.get("conflict"),
                "fairness": comps.get("fairness"),
                "idle": comps.get("idle"),
                "matching": comps.get("matching"),
                "penalty": comps.get("penalty"),
                "penalty_count": comps.get("penalty_count"),
            }
            rows.append(row)
    # sort by gen
    rows = [r for r in rows if r.get("gen") is not None]
    rows.sort(key=lambda r: int(r["gen"]))
    return rows


def save_csv(rows, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    keys = ["gen", "best", "avg", "conflict", "fairness", "idle", "matching", "penalty", "penalty_count"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def plot_rows(rows, outdir: Path, prefix: str = "ga_hard_test"):
    ensure_matplotlib()
    import matplotlib.pyplot as plt  # type: ignore

    gens = [int(r["gen"]) for r in rows]
    best = [float(r["best"]) for r in rows]
    avg = [float(r["avg"]) for r in rows]

    # Best / Avg plot
    plt.figure(figsize=(8, 4))
    plt.plot(gens, best, marker="o", label="best")
    plt.plot(gens, avg, marker="s", label="avg")
    plt.xlabel("generation")
    plt.ylabel("fitness")
    plt.title("GA: Best and Average Fitness per Generation")
    plt.grid(alpha=0.3)
    plt.legend()
    out_best = outdir / f"{prefix}_best_avg.png"
    plt.tight_layout()
    plt.savefig(out_best)
    plt.close()

    # Components plot (conflict, fairness, idle, matching, penalty)
    comps = ["conflict", "fairness", "idle", "matching", "penalty"]
    plt.figure(figsize=(9, 5))
    for c in comps:
        vals = [float(r[c]) if r[c] is not None else float('nan') for r in rows]
        plt.plot(gens, vals, marker=".", label=c)
    plt.xlabel("generation")
    plt.ylabel("component score")
    plt.title("GA: Best Components per Generation")
    plt.grid(alpha=0.2)
    plt.legend()
    out_comp = outdir / f"{prefix}_components.png"
    plt.tight_layout()
    plt.savefig(out_comp)
    plt.close()

    # Penalty count bar
    penalty_counts = [int(r.get("penalty_count") or 0) for r in rows]
    plt.figure(figsize=(9, 3))
    plt.bar(gens, penalty_counts, color="#d9534f")
    plt.xlabel("generation")
    plt.ylabel("penalty_count")
    plt.title("GA: Penalty Count per Generation")
    plt.grid(axis="y", alpha=0.2)
    out_pen = outdir / f"{prefix}_penalties.png"
    plt.tight_layout()
    plt.savefig(out_pen)
    plt.close()

    return out_best, out_comp, out_pen


def main(argv=None):
    import argparse
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", default="backend/tmp/ga_hard_test.ndjson", help="NDJSON input path")
    p.add_argument("--outdir", "-o", default="backend/tmp", help="Output directory for PNG/CSV")
    p.add_argument("--prefix", default="ga_hard_test", help="Filename prefix")
    args = p.parse_args(argv)

    inpath = Path(args.input)
    outdir = Path(args.outdir)
    if not inpath.exists():
        print(f"Input file not found: {inpath}")
        sys.exit(2)

    rows = parse_ndjson(inpath)
    if not rows:
        print("No GA generation records found in the NDJSON file.")
        sys.exit(1)

    csv_path = outdir / f"{args.prefix}_summary.csv"
    save_csv(rows, csv_path)
    best_png, comp_png, pen_png = plot_rows(rows, outdir, prefix=args.prefix)

    print("Plots and CSV written:")
    print(f" - {csv_path}")
    print(f" - {best_png}")
    print(f" - {comp_png}")
    print(f" - {pen_png}")


if __name__ == '__main__':
    main()
