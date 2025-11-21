"""Aggregate per-run sweep CSV into per-weight aggregated CSV.
Reads `soft_penalty_sweep_multi_results.csv` and writes
`soft_penalty_sweep_multi_aggregated.csv` with mean/std for numeric fields.
"""
import csv
import statistics

infile = 'backend/benchmarks/soft_penalty_sweep_multi_results.csv'
outfile = 'backend/benchmarks/soft_penalty_sweep_multi_aggregated.csv'

rows = []
with open(infile, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        # convert numeric fields
        r['soft_penalty_weight'] = float(r['soft_penalty_weight'])
        r['final_fitness'] = float(r['final_fitness'])
        r['best_gene_count'] = int(r['best_gene_count'])
        r['soft_penalty_count'] = int(r['soft_penalty_count'])
        r['population_avg'] = float(r['population_avg'])
        r['population_std'] = float(r['population_std'])
        r['elapsed_s'] = float(r['elapsed_s'])
        rows.append(r)

groups = {}
for r in rows:
    k = r['soft_penalty_weight']
    groups.setdefault(k, []).append(r)

out_rows = []
for k, items in sorted(groups.items()):
    final_fitness_vals = [i['final_fitness'] for i in items]
    best_counts = [i['best_gene_count'] for i in items]
    soft_counts = [i['soft_penalty_count'] for i in items]
    pop_avgs = [i['population_avg'] for i in items]
    elapsed = [i['elapsed_s'] for i in items]

    out_rows.append({
        'soft_penalty_weight': k,
        'runs': len(items),
        'final_fitness_mean': statistics.mean(final_fitness_vals),
        'final_fitness_std': statistics.pstdev(final_fitness_vals) if len(final_fitness_vals)>1 else 0.0,
        'best_gene_count_mean': statistics.mean(best_counts),
        'soft_penalty_count_mean': statistics.mean(soft_counts),
        'population_avg_mean': statistics.mean(pop_avgs),
        'elapsed_mean_s': statistics.mean(elapsed)
    })

with open(outfile, 'w', newline='', encoding='utf-8') as f:
    fieldnames = list(out_rows[0].keys())
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in out_rows:
        writer.writerow(r)

print('Wrote aggregated results to', outfile)
