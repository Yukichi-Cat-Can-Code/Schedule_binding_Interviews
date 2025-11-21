import os
import csv
import json
import glob
import sys
from collections import defaultdict

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception as e:
    print('matplotlib not available:', e)
    print('\nPlease install matplotlib to generate plots:')
    print('\n    pip install matplotlib')
    sys.exit(2)

import numpy as np
import matplotlib.ticker as ticker
try:
    import seaborn as sns
except Exception:
    sns = None

from datetime import datetime

# --- Standard plotting style for high-contrast / publication figures ---
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
    'axes.labelsize': 12,
    'font.size': 11,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.figsize': [10, 6],
    'savefig.dpi': 300,
    'axes.grid': True,
    'grid.alpha': 0.25,
})

BASE = 'backend/benchmarks'
PER_RUN_CSV = os.path.join(BASE, 'soft_penalty_sweep_multi_results.csv')
AGG_CSV = os.path.join(BASE, 'soft_penalty_sweep_multi_aggregated.csv')

os.makedirs(BASE, exist_ok=True)

OUT_ROOT = os.path.join(BASE, 'images')
RUN_ID = os.environ.get('PLOT_RUN_DIR') or datetime.now().strftime('%Y%m%d_%H%M%S')
OUT_DIR = os.path.join(OUT_ROOT, RUN_ID)
os.makedirs(OUT_DIR, exist_ok=True)

def make_boxplot():
    if not os.path.exists(PER_RUN_CSV):
        print('Per-run CSV not found:', PER_RUN_CSV)
        return
    data = defaultdict(list)
    with open(PER_RUN_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            k = float(r['soft_penalty_weight'])
            val = float(r['final_fitness'])
            data[k].append(val)

    weights = sorted(data.keys())
    groups = [data[w] for w in weights]
    # White background, crisp lines for printing
    if sns:
        sns.set_style('white')
    else:
        plt.style.use('default')
    fig, ax = plt.subplots(figsize=(8, 5))
    bp = ax.boxplot(groups, labels=[str(w) for w in weights], showmeans=True, patch_artist=True,
                    boxprops=dict(facecolor='white', color='black'), medianprops=dict(color='firebrick'))
    # overlay jittered points to reveal micro-variance (deterministic jitter)
    np.random.seed(0)
    for i, w in enumerate(weights):
        vals = np.array(data[w])
        xs = (np.ones_like(vals) * (i + 1)) + np.random.normal(0, 0.04, size=len(vals))
        ax.scatter(xs, vals, color='#2ca02c', alpha=0.8, s=18, marker='^')
    ax.set_title('Impact of Penalty Weight on Final Fitness')
    ax.set_xlabel('Soft Penalty Weight')
    ax.set_ylabel('Final Fitness')
    out = os.path.join(OUT_DIR, 'boxplot_soft_penalty.png')
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('Wrote box plot to', out)

def make_boxplot_zoom(ymin=0.78, ymax=0.82):
    if not os.path.exists(PER_RUN_CSV):
        print('Per-run CSV not found:', PER_RUN_CSV)
        return
    data = defaultdict(list)
    with open(PER_RUN_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            k = float(r['soft_penalty_weight'])
            val = float(r['final_fitness'])
            data[k].append(val)

    weights = sorted(data.keys())
    groups = [data[w] for w in weights]

    if sns:
        sns.set_style('white')
    else:
        plt.style.use('default')
    fig, ax = plt.subplots(figsize=(7, 4))
    bp = ax.boxplot(groups, labels=[str(w) for w in weights], showmeans=True, patch_artist=True,
                    boxprops=dict(facecolor='white', color='black'), medianprops=dict(color='firebrick'))
    # overlay jittered points
    np.random.seed(0)
    all_vals = []
    for i, w in enumerate(weights):
        vals = np.array(data[w])
        all_vals.extend(vals.tolist())
        xs = (np.ones_like(vals) * (i + 1)) + np.random.normal(0, 0.04, size=len(vals))
        ax.scatter(xs, vals, color='#2ca02c', alpha=0.8, s=18, marker='^')
    # dynamic zoom if user didn't pass custom bounds
    if ymin is None or ymax is None:
        if all_vals:
            vmin = min(all_vals)
            vmax = max(all_vals)
            span = max(1e-6, vmax - vmin)
            margin = max(0.0005, span * 0.25)
            ymin, ymax = vmin - margin, vmax + margin
        else:
            ymin, ymax = 0.0, 1.0
    ax.set_title('Final Fitness by Soft Penalty (zoom)')
    ax.set_xlabel('Soft Penalty Weight')
    ax.set_ylabel('Final Fitness')
    ax.set_ylim(ymin, ymax)
    ax.grid(axis='y', alpha=0.2)

    out_png = os.path.join(OUT_DIR, 'boxplot_soft_penalty_zoom.png')
    out_svg = os.path.join(OUT_DIR, 'boxplot_soft_penalty_zoom.svg')
    fig.tight_layout()
    fig.savefig(out_png, dpi=600, bbox_inches='tight')
    fig.savefig(out_svg)
    plt.close(fig)
    print('Wrote zoomed box plot to', out_png, 'and', out_svg)

    # write LaTeX-ready caption
    caption = (
        "Box plot showing distribution of final GA fitness across different SOFT_PENALTY values. "
        "Each box summarizes N independent runs (multi-seed sweep). The narrow vertical range emphasizes "
        "small variations in final fitness (zoomed to [%.2f, %.2f]). Robustness is indicated by nearly identical "
        "box shapes across weights, suggesting low sensitivity to SOFT_PENALTY in the tested interval."
        % (ymin, ymax)
    )
    caption_path = os.path.join(OUT_DIR, 'boxplot_soft_penalty_caption.txt')
    with open(caption_path, 'w', encoding='utf-8') as cf:
        cf.write(caption)
    print('Wrote LaTeX-ready caption to', caption_path)

def make_boxplot_ieee(width_in=6.5, height_in=2.8, dpi=600):
    if not os.path.exists(PER_RUN_CSV):
        print('Per-run CSV not found:', PER_RUN_CSV)
        return
    data = defaultdict(list)
    with open(PER_RUN_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            k = float(r['soft_penalty_weight'])
            val = float(r['final_fitness'])
            data[k].append(val)

    weights = sorted(data.keys())
    groups = [data[w] for w in weights]

    plt.rcParams.update({'font.size': 9, 'font.family': 'serif'})
    if sns:
        sns.set_style('white')
    else:
        plt.style.use('default')
    fig, ax = plt.subplots(figsize=(width_in, height_in))

    boxprops = dict(facecolor='white', color='black')
    medianprops = dict(color='firebrick', linewidth=1.5)
    meanprops = dict(marker='D', markeredgecolor='black', markerfacecolor='black')

    bp = ax.boxplot(groups, labels=[str(w) for w in weights], showmeans=True,
                    patch_artist=True, boxprops=boxprops, medianprops=medianprops, meanprops=meanprops)
    # overlay jittered points to show individual runs
    np.random.seed(0)
    for i, w in enumerate(weights):
        vals = np.array(data[w])
        xs = (np.ones_like(vals) * (i + 1)) + np.random.normal(0, 0.03, size=len(vals))
        ax.scatter(xs, vals, color='#2ca02c', alpha=0.9, s=12, marker='^')

    # annotate mean ± std above each box
    for i, w in enumerate(weights):
        vals = np.array(data[w])
        mean = float(np.mean(vals))
        std = float(np.std(vals, ddof=0))
        x = i + 1
        # place label above top whisker with a small margin
        y = max(vals) + (0.004 * (ax.get_ylim()[1] - ax.get_ylim()[0]))
        txt = f"{mean:.3f} ± {std:.3f}"
        ax.text(x, y, txt, ha='center', va='bottom', fontsize=7)

    ax.set_xlabel('SOFT_PENALTY')
    ax.set_ylabel('Final Fitness')
    ax.set_title('Final Fitness by SOFT_PENALTY — IEEE figure')
    ax.grid(axis='y', alpha=0.25)

    out_png = os.path.join(OUT_DIR, 'boxplot_soft_penalty_ieee.png')
    out_svg = os.path.join(OUT_DIR, 'boxplot_soft_penalty_ieee.svg')
    fig.tight_layout()
    fig.savefig(out_png, dpi=dpi)
    fig.savefig(out_svg)
    plt.close(fig)
    print('Wrote IEEE boxplot to', out_png, 'and', out_svg)

def make_convergence_plot():
    # allow overriding which NDJSON to use via command-line argument
    forced = None
    try:
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            forced = sys.argv[1]
    except Exception:
        forced = None

    if forced:
        path = forced
    else:
        # pick the newest sensitivity NDJSON log (prefer sensitivity, else sweep)
        logs = glob.glob('backend/logs/ga_sensitivity_*.ndjson')
        if not logs:
            logs = glob.glob('backend/logs/ga_sweep_*.ndjson')
        if not logs:
            print('No NDJSON logs found in backend/logs/')
            return
        # choose the most recent file by modification time
        path = max(logs, key=os.path.getmtime)
    gens = []
    bests = []
    softs = []

    def find_soft_penalty(obj):
        if not isinstance(obj, dict):
            return None
        # known places
        biz = obj.get('biz_kpi') if isinstance(obj.get('biz_kpi'), dict) else None
        if biz:
            for k in ('total_soft_penalties', 'soft_penalties', 'soft_penalty_count'):
                if k in biz and biz[k] is not None:
                    try:
                        return int(biz[k])
                    except Exception:
                        pass

        ah = obj.get('algo_health') if isinstance(obj.get('algo_health'), dict) else None
        if ah:
            for k in ('soft_penalty_count', 'soft_penalties'):
                if k in ah and ah[k] is not None:
                    try:
                        return int(ah[k])
                    except Exception:
                        pass

        for k in ('total_soft_penalties', 'soft_penalty_count', 'soft_penalties'):
            if k in obj and obj[k] is not None:
                try:
                    return int(obj[k])
                except Exception:
                    pass

        # recursive search
        def recursive_search(d):
            if not isinstance(d, dict):
                return None
            for key, val in d.items():
                lk = str(key).lower()
                if 'soft' in lk and ('penal' in lk or 'pen' in lk):
                    try:
                        return int(val)
                    except Exception:
                        pass
                if isinstance(val, dict):
                    found = recursive_search(val)
                    if found is not None:
                        return found
            return None

        return recursive_search(obj)

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            # support both older and new schema
            meta = obj.get('meta', {}) if isinstance(obj.get('meta', {}), dict) else {}
            gen = meta.get('gen') if meta.get('gen') is not None else obj.get('generation')
            if gen is None:
                continue
            gens.append(int(gen))

            fitness_block = obj.get('fitness') if isinstance(obj.get('fitness'), dict) else None
            if fitness_block is not None:
                fitness = fitness_block.get('best')
            else:
                fitness = obj.get('best_fitness')
            bests.append(float(fitness) if fitness is not None else np.nan)

            soft_val = find_soft_penalty(obj)
            if soft_val is None:
                softs.append(0)
            else:
                softs.append(int(soft_val))

    if not gens:
        print('No generation records found in', path)
        return

    # sort by generation
    pairs = sorted(zip(gens, bests, softs), key=lambda x: x[0])
    gens, bests, softs = zip(*pairs)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    color_fit = '#003f5c'  # dark blue
    ax1.plot(gens, bests, color=color_fit, linewidth=2, linestyle='-', label='Best Fitness')
    # show markers sparsely to avoid overplotting
    step = max(1, int(len(gens) / 30))
    ax1.plot(gens[::step], np.array(bests)[::step], 'o', color=color_fit, markersize=5)
    ax1.set_xlabel('Generation')
    ax1.set_ylabel('Best Fitness', color=color_fit)
    ax1.tick_params(axis='y', labelcolor=color_fit)
    ax1.grid(alpha=0.25)

    ax2 = ax1.twinx()
    # publication-friendly purple-red color
    color_pen = '#bc5090'
    ax2.plot(gens, softs, color=color_pen, linestyle='--', linewidth=2, marker='s', markersize=5, label='Total Soft Penalties')
    ax2.set_ylabel('Total Soft Penalties (count)', color=color_pen)
    ax2.tick_params(axis='y', labelcolor=color_pen)
    # enforce integer ticks for right axis using MaxNLocator
    try:
        locator = ticker.MaxNLocator(integer=True)
        ax2.yaxis.set_major_locator(locator)
        # if constant series, expand range a bit so point is visible
        ymin = min(softs)
        ymax = max(softs)
        if ymin == ymax:
            # expand padding proportionally but at least by 1
            pad = max(1, int(0.2 * max(1, ymin)))
            ax2.set_ylim(max(0, ymin - pad), ymax + pad)
        else:
            ax2.set_ylim(0, ymax * 1.2)
    except Exception:
        pass

    # warn if extracted penalty series is all zeros (likely schema mismatch)
    if all(s == 0 for s in softs):
        print('Warning: extracted soft-penalty series is all zeros. Please verify log schema or run with updated logging.')

    plt.title('Convergence Dynamics: Optimization vs. Constraints')
    # add combined legend
    try:
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        if h1 or h2:
            ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=9)
    except Exception:
        pass

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, 'convergence_{}.png'.format(os.path.basename(path).replace('.ndjson','')))
    out_svg = os.path.join(OUT_DIR, 'convergence_{}.svg'.format(os.path.basename(path).replace('.ndjson','')))
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_svg)

    # IEEE-sized export (smaller font, high-dpi)
    try:
        old_size = fig.get_size_inches()
        fig.set_size_inches(6.5, 2.8)
        # reduce font sizes for IEEE
        ax1.title.set_fontsize(9)
        ax1.xaxis.label.set_fontsize(9)
        ax1.yaxis.label.set_fontsize(9)
        ax2.yaxis.label.set_fontsize(9)
        for label in (ax1.get_xticklabels() + ax1.get_yticklabels() + ax2.get_yticklabels()):
            label.set_fontsize(8)
        out_png_ieee = os.path.join(OUT_DIR, 'convergence_{}__ieee.png'.format(os.path.basename(path).replace('.ndjson','')))
        out_svg_ieee = os.path.join(OUT_DIR, 'convergence_{}__ieee.svg'.format(os.path.basename(path).replace('.ndjson','')))
        fig.savefig(out_png_ieee, dpi=600, bbox_inches='tight')
        fig.savefig(out_svg_ieee)
        # restore size
        fig.set_size_inches(old_size)
        print('Wrote convergence plots to', out_png, 'and', out_svg, 'and IEEE variants', out_png_ieee, out_svg_ieee)
    except Exception:
        plt.close()
        print('Wrote convergence plots to', out_png, 'and', out_svg)
    plt.close()


def make_aggregated_convergence_plot(pattern='backend/logs/ga_sweep_ext_*.ndjson', right_ylim=(20, 30), use_ci=True, confidence=0.95):
    """Aggregate multiple NDJSON runs matching `pattern` and plot mean ± std bands for
    Best Fitness and biz_kpi['soft_penalties'] across generations.

    pattern: glob pattern to find NDJSON files (default targets extended sweep logs).
    right_ylim: tuple (ymin,ymax) for penalty axis; used if plausible given data.
    """
    files = sorted(glob.glob(pattern))
    if not files:
        print('No files found for aggregated convergence pattern:', pattern)
        return

    runs_fitness = []
    runs_soft = []
    runs_gens = []

    # loader that explicitly reads biz_kpi['soft_penalties']
    for p in files:
        gens = []
        fitness = []
        soft = []
        try:
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    meta = obj.get('meta', {}) if isinstance(obj.get('meta', {}), dict) else {}
                    gen = meta.get('gen') if meta.get('gen') is not None else obj.get('generation')
                    if gen is None:
                        continue
                    # fitness
                    fitness_block = obj.get('fitness') if isinstance(obj.get('fitness'), dict) else None
                    if fitness_block is not None:
                        fval = fitness_block.get('best')
                    else:
                        fval = obj.get('best_fitness')
                    # penalty: direct target
                    biz = obj.get('biz_kpi') if isinstance(obj.get('biz_kpi'), dict) else {}
                    sval = biz.get('soft_penalties') if biz.get('soft_penalties') is not None else None

                    if fval is None or sval is None:
                        # skip generations lacking either metric
                        continue
                    gens.append(int(gen))
                    fitness.append(float(fval))
                    try:
                        soft.append(int(sval))
                    except Exception:
                        soft.append(int(float(sval)))
        except Exception as e:
            print('Failed to read', p, e)
            continue

        if gens:
            runs_gens.append(gens)
            runs_fitness.append(fitness)
            runs_soft.append(soft)

    if not runs_gens:
        print('No usable runs found for aggregation under pattern:', pattern)
        return

    # compute common generation intersection across runs
    common_gens = set(runs_gens[0])
    for g in runs_gens[1:]:
        common_gens &= set(g)
    if not common_gens:
        # as fallback, use gens present in majority - take intersection of sorted first N gens
        # here take minimal contiguous gens across runs
        min_len = min(len(g) for g in runs_gens)
        common_gens = set(range(min_len))
    common_gens = sorted(common_gens)

    # align runs to common_gens
    aligned_fitness = []
    aligned_soft = []
    for gens, fit, sof in zip(runs_gens, runs_fitness, runs_soft):
        gen_to_idx = {g: i for i, g in enumerate(gens)}
        fvec = []
        svec = []
        for g in common_gens:
            if g in gen_to_idx:
                idx = gen_to_idx[g]
                fvec.append(fit[idx])
                svec.append(sof[idx])
            else:
                # pad with nan so aggregation ignores
                fvec.append(np.nan)
                svec.append(np.nan)
        aligned_fitness.append(fvec)
        aligned_soft.append(svec)

    F = np.array(aligned_fitness, dtype=float)
    S = np.array(aligned_soft, dtype=float)

    mean_f = np.nanmean(F, axis=0)
    std_f = np.nanstd(F, axis=0)
    mean_s = np.nanmean(S, axis=0)
    std_s = np.nanstd(S, axis=0)

    # compute uncertainty band: either ±1 std or approximate z-based CI
    if use_ci:
        # map common confidence levels to z-scores; fallback to 1.96 for 95%
        z_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_map.get(round(confidence,2), 1.96)
        # standard error across runs (ignore NaNs)
        n_runs = float(F.shape[0]) if F.shape[0] > 0 else 1.0
        se_f = std_f / np.sqrt(max(1.0, n_runs))
        se_s = std_s / np.sqrt(max(1.0, n_runs))
        band_f = z * se_f
        band_s = z * se_s
    else:
        band_f = std_f
        band_s = std_s

    gens_arr = np.array(common_gens)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    color_fit = '#003f5c'
    ax1.plot(gens_arr, mean_f, color=color_fit, linewidth=2, label='Mean Best Fitness')
    ax1.fill_between(gens_arr, mean_f - band_f, mean_f + band_f, color=color_fit, alpha=0.15)
    ax1.set_xlabel('Generation')
    ax1.set_ylabel('Best Fitness', color=color_fit)
    ax1.tick_params(axis='y', labelcolor=color_fit)
    ax1.grid(alpha=0.2)

    ax2 = ax1.twinx()
    color_pen = '#d62728'
    ax2.plot(gens_arr, mean_s, color=color_pen, linewidth=2, linestyle='--', label='Mean Soft Penalties')
    ax2.fill_between(gens_arr, mean_s - band_s, mean_s + band_s, color=color_pen, alpha=0.12)
    ax2.set_ylabel('Total Soft Penalties (count)', color=color_pen)
    ax2.tick_params(axis='y', labelcolor=color_pen)
    # set suggested right axis limits if they make sense for data
    try:
        ymin_req, ymax_req = right_ylim
        data_min = np.nanmin(mean_s - std_s)
        data_max = np.nanmax(mean_s + std_s)
        # if requested window covers the data, use it; else extend a bit beyond observed
        if data_min >= ymin_req and data_max <= ymax_req:
            ax2.set_ylim(ymin_req, ymax_req)
        else:
            pad = max(1, int(0.1 * max(1, data_max - data_min)))
            ax2.set_ylim(max(0, data_min - pad), data_max + pad)
    except Exception:
        pass

    plt.title('Aggregated Convergence: Mean ± CI (N={})'.format(F.shape[0]))
    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, 'convergence_aggregated.png')
    out_svg = os.path.join(OUT_DIR, 'convergence_aggregated.svg')
    fig.savefig(out_png, dpi=300, bbox_inches='tight')
    fig.savefig(out_svg)
    # add legend combining both axes
    try:
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        if h1 or h2:
            ax1.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=9)
    except Exception:
        pass

    # IEEE-sized aggregated export
    try:
        old_size = fig.get_size_inches()
        fig.set_size_inches(6.5, 2.8)
        ax1.title.set_fontsize(9)
        ax1.xaxis.label.set_fontsize(9)
        ax1.yaxis.label.set_fontsize(9)
        ax2.yaxis.label.set_fontsize(9)
        for label in (ax1.get_xticklabels() + ax1.get_yticklabels() + ax2.get_yticklabels()):
            label.set_fontsize(8)
        out_png_ieee = os.path.join(OUT_DIR, 'convergence_aggregated__ieee.png')
        out_svg_ieee = os.path.join(OUT_DIR, 'convergence_aggregated__ieee.svg')
        fig.savefig(out_png_ieee, dpi=600, bbox_inches='tight')
        fig.savefig(out_svg_ieee)
        fig.set_size_inches(old_size)
        # annotate start/end mean and CI for soft penalties (right axis)
        try:
            # pick first/last non-nan index
            valid_idx = [i for i in range(len(mean_s)) if not np.isnan(mean_s[i])]
            if valid_idx:
                i0 = valid_idx[0]
                i1 = valid_idx[-1]
                # band_s contains half-width of CI if use_ci True, else std
                start_mean = mean_s[i0]
                start_band = band_s[i0] if 'band_s' in locals() else std_s[i0]
                end_mean = mean_s[i1]
                end_band = band_s[i1] if 'band_s' in locals() else std_s[i1]
                txt = (
                    f"Start Soft Penalties: {start_mean:.1f} \u00B1 {start_band:.2f} (95% CI)\n"
                    f"End   Soft Penalties: {end_mean:.1f} \u00B1 {end_band:.2f} (95% CI)"
                )
                # place box in upper right inside figure
                fig.text(0.72, 0.75, txt, ha='left', va='top', fontsize=9,
                         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='0.8'))
                # also write a small caption for the aggregated figure
                caption = (
                    f"Aggregated convergence across {F.shape[0]} runs. "
                    f"Start soft penalties mean = {start_mean:.2f} (±{start_band:.2f}), "
                    f"End mean = {end_mean:.2f} (±{end_band:.2f})."
                )
                with open(os.path.join(BASE, 'convergence_aggregated_caption.txt'), 'w', encoding='utf-8') as cf:
                    cf.write(caption)
        except Exception:
            pass

        print('Wrote aggregated convergence plots to', out_png, 'and', out_svg, 'and IEEE variants', out_png_ieee, out_svg_ieee)
    except Exception:
        print('Wrote aggregated convergence plots to', out_png, 'and', out_svg)
    plt.close(fig)

if __name__ == '__main__':
    make_boxplot()
    make_boxplot_zoom()
    make_convergence_plot()
    # also generate aggregated convergence plot across extended sweep logs
    try:
        make_aggregated_convergence_plot()
    except Exception as e:
        print('Failed to generate aggregated convergence plot:', e)
