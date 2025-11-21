"""Diagnostic plot for suspicious perfect fitness values.

Scans `soft_penalty_sweep_multi_results.csv` for final_fitness per run and
scans `backend/logs/*.ndjson` for any generation-level best_fitness >= 0.995.

Outputs a scatter plot highlighting runs with final_fitness >= 0.995 and
writes a small text report of any NDJSON lines that reached near-1.0.
"""
import os
import json
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
from glob import glob

BASE = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE, 'soft_penalty_sweep_multi_results.csv')
LOG_DIR = os.path.join(os.path.dirname(BASE), 'logs')
OUT_ROOT = os.path.join(BASE, 'images')
RUN_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
OUT_DIR = os.path.join(OUT_ROOT, RUN_ID)
os.makedirs(OUT_DIR, exist_ok=True)


def read_csv():
    rows = []
    if not os.path.exists(CSV_PATH):
        return rows
    with open(CSV_PATH, newline='') as f:
        r = csv.DictReader(f)
        for rec in r:
            try:
                rows.append({
                    'soft_penalty_weight': float(rec.get('soft_penalty_weight', 0)),
                    'seed': rec.get('seed'),
                    'final_fitness': float(rec.get('final_fitness', 0)),
                    'elapsed_s': float(rec.get('elapsed_s', 0)) if rec.get('elapsed_s') else None,
                })
            except Exception:
                continue
    return rows


def scan_logs(threshold=0.995):
    findings = []
    if not os.path.isdir(LOG_DIR):
        return findings
    for p in glob(os.path.join(LOG_DIR, '*.ndjson')):
        with open(p, 'r', encoding='utf-8') as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                except Exception:
                    continue
                # direct top-level best_fitness
                bf = None
                if isinstance(obj, dict):
                    if 'best_fitness' in obj:
                        try:
                            bf = float(obj.get('best_fitness') or 0)
                        except Exception:
                            bf = None
                    # nested ga_gen_stat or perf blocks
                    if 'ga_gen_stat' in obj and isinstance(obj['ga_gen_stat'], dict):
                        try:
                            bf = float(obj['ga_gen_stat'].get('best_fitness') or obj['ga_gen_stat'].get('fitness') or 0)
                        except Exception:
                            bf = bf
                    # legacy 'perf' / 'fitness' patterns
                    if 'perf' in obj and isinstance(obj['perf'], dict):
                        try:
                            bf = float(obj['perf'].get('best_fitness') or obj['perf'].get('fitness') or bf or 0)
                        except Exception:
                            pass
                if bf is not None and bf >= threshold:
                    findings.append({'path': p, 'line': ln, 'best_fitness': bf})
    return findings


def make_plot(csv_rows, findings):
    # scatter final_fitness vs weight
    if not csv_rows:
        print('No CSV rows to plot')
        return None
    weights = [r['soft_penalty_weight'] for r in csv_rows]
    fitness = [r['final_fitness'] for r in csv_rows]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(weights, fitness, c='tab:blue', label='Final fitness (runs)')

    # highlight suspicious points
    suspicious_x = [w for w, f in zip(weights, fitness) if f >= 0.995]
    suspicious_y = [f for f in fitness if f >= 0.995]
    if suspicious_x:
        ax.scatter(suspicious_x, suspicious_y, c='red', s=80, label='Suspicious (>=0.995)')

    ax.set_xlabel('soft_penalty_weight')
    ax.set_ylabel('final_fitness')
    ax.set_title('Diagnostic: Final fitness by soft_penalty_weight')
    ax.axhline(0.995, color='gray', linestyle='--', linewidth=1)
    ax.legend()

    out_png = os.path.join(OUT_DIR, 'diagnostic_fitness_scatter.png')
    fig.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return out_png


def main():
    csv_rows = read_csv()
    findings = scan_logs()
    out = make_plot(csv_rows, findings)
    report_path = os.path.join(OUT_DIR, 'diagnostic_report.txt')
    with open(report_path, 'w', encoding='utf-8') as rep:
        rep.write('Diagnostic run\n')
        rep.write('CSV rows: %d\n' % len(csv_rows)
                  )
        rep.write('Log findings (best_fitness >= 0.995): %d\n' % len(findings))
        for f in findings:
            rep.write('---\n')
            rep.write('file: %s\n' % f['path'])
            rep.write('best_fitness: %s\n' % f['best_fitness'])
            rep.write('line: %s\n' % f['line'][:1000])
    print('Wrote', out)
    print('Wrote', report_path)


if __name__ == '__main__':
    main()
