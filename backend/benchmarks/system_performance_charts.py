"""Generate two performance charts:
- Left: "Thời Gian Chạy & Tối Ưu Hóa" (bar chart comparing sequential vs parallel)
- Right: "Tối Ưu Độ Phức Tạp Thuật Toán" (complexity curves O(n), O(n log n), O(n^2))

Saves PNG and SVG files under `backend/benchmarks/images/<timestamp>/`.
"""
from datetime import datetime
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


BASE = os.path.join(os.path.dirname(__file__), '')
OUT_ROOT = os.path.join(BASE, 'images')
RUN_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
import csv
from collections import defaultdict
from statistics import mean
OUT_DIR = os.path.join(OUT_ROOT, RUN_ID)
os.makedirs(OUT_DIR, exist_ok=True)


def make_runtime_barplot():
    # Example data (milliseconds) — adjust if you have real measurements
    # If benchmark CSV exists, read mean elapsed seconds grouped by soft_penalty_weight.
    csv_path = os.path.join(os.path.dirname(__file__), 'soft_penalty_sweep_multi_results.csv')
    if os.path.exists(csv_path):
        groups = defaultdict(list)
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    w = float(r.get('soft_penalty_weight', r.get('weight', 0)))
                    elapsed = float(r.get('elapsed_s', r.get('elapsed', r.get('elapsed_mean_s', 0))))
                    groups[w].append(elapsed)
                except Exception:
                    continue

        if not groups:
            labels = ['Demo small', 'Demo med', 'Demo large']
            seq = np.array([0.5, 1.2, 2.5])
            par = seq * 0.45
        else:
            weights = sorted(groups.keys())
            labels = [str(w) for w in weights]
            seq_vals = [mean(groups[w]) for w in weights]
            seq = np.array(seq_vals)
            # Simulate an optimized/parallel variant as a fraction of the measured runtime
            par = seq * 0.45
    else:
        # Example data (milliseconds) — adjust if you have real measurements
        labels = ['Dữ liệu nhỏ', 'Dữ liệu trung bình', 'Dữ liệu lớn']
        seq = np.array([500, 1200, 2500])
        par = np.array([200, 600, 1100])
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width/2, seq, width, label='Tuần tự', color='#0b5a8a')
    # If CSV provided elapsed in seconds, convert to milliseconds for plot readability
    if seq.max() < 10:
        # likely seconds, convert to ms
        seq_plot = seq * 1000.0
        par_plot = par * 1000.0
        y_label = 'Thời gian chạy (ms)'
    else:
        seq_plot = seq
        par_plot = par
        y_label = 'Thời gian chạy (ms)'

    ax.set_ylabel(y_label)
    bars1 = ax.bar(x - width/2, seq_plot, width, label='Tuần tự', color='#0b5a8a')
    bars2 = ax.bar(x + width/2, par_plot, width, label='Song song (sim) ', color='#2ca02c')
    ax.set_ylabel('Thời gian chạy (ms)')
    caption = (
        'Song song hóa phân chia tác vụ, giảm thời gian xử lý đáng kể và cải thiện thông lượng. '
        '"Song song" bars are simulated (45% of measured runtime) when using CSV-derived data.'
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    fig.text(0.02, 0.02, caption, fontsize=9, va='bottom')
    # add small caption box
    caption = (
        'Song song hóa phân chia tác vụ, giảm thời gian xử lý đáng kể và cải thiện thông lượng.'
    )
    fig.text(0.02, 0.02, caption, fontsize=9, va='bottom')

    out_png = os.path.join(OUT_DIR, 'runtime_vs_optimization.png')
    out_svg = os.path.join(OUT_DIR, 'runtime_vs_optimization.svg')
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg)
    plt.close(fig)
    print('Wrote', out_png)


def make_complexity_plot():
    # n range
    ns = np.linspace(50, 500, 250)
    on = ns
    onlogn = ns * np.log2(ns)
    on2 = ns**2

    # By default produce normalized curves so they're visually comparable.
    # If the environment variable `SYSTEM_CHARTS_ABSOLUTE=1` is set, plot absolute values instead.
    import os as _os
    if _os.environ.get('SYSTEM_CHARTS_ABSOLUTE') == '1':
        on_plot = on
        onlogn_plot = onlogn
        on2_plot = on2
    else:
        # scale for visual comparison (normalize by max)
        on_plot = on / np.max(on)
        onlogn_plot = onlogn / np.max(onlogn)
        on2_plot = on2 / np.max(on2)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(ns, on_plot, label='O(n)', color='#004c6d', linewidth=2)
    ax.plot(ns, onlogn_plot, label='O(n log n)', color='#2a9d8f', linewidth=2)
    ax.plot(ns, on2_plot, label='O(n²)', color='#ff7f0e', linewidth=2)

    ax.set_xlabel('Kích thước dữ liệu (n)')
    ax.set_ylabel('Độ lớn tương đối (chuẩn hoá)')
    ax.set_title('Tối Ưu Độ Phức Tạp Thuật Toán')
    ax.legend()
    ax.grid(alpha=0.25)

    # small explanatory box
    caption = (
        'Giảm độ phức tạp từ O(n²) xuống O(n log n) hay O(n) là bước tiến lớn, đảm bảo hệ thống ' \
        'duy trì tốc độ và độ ổn định khi dữ liệu tăng.'
    )
    fig.text(0.02, 0.02, caption, fontsize=9, va='bottom')

    out_png = os.path.join(OUT_DIR, 'complexity_vs_scale.png')
    out_svg = os.path.join(OUT_DIR, 'complexity_vs_scale.svg')
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg)
    plt.close(fig)
    print('Wrote', out_png)


def main():
    make_runtime_barplot()
    make_complexity_plot()


if __name__ == '__main__':
    main()
