import csv, statistics, os
from collections import defaultdict
# Resolve CSV path relative to this script so it works regardless of cwd
BASE_DIR = os.path.dirname(__file__)
path = os.path.join(BASE_DIR, 'soft_penalty_sweep_multi_results.csv')
rows=defaultdict(list)
with open(path,'r',encoding='utf-8') as f:
    r=csv.DictReader(f)
    for rec in r:
        k=float(rec['soft_penalty_weight'])
        rows[k].append(rec)

print('Summary per soft_penalty_weight:')
print('weight, runs, mean_final_fitness, std_final_fitness, mean_soft_penalty_count, mean_population_std')
for k in sorted(rows.keys()):
    recs=rows[k]
    fits=[float(x['final_fitness']) for x in recs]
    softs=[float(x['soft_penalty_count']) for x in recs]
    popstd=[float(x['population_std']) for x in recs]
    print(f"{k}, {len(recs)}, {statistics.mean(fits):.6f}, {statistics.pstdev(fits):.6f}, {statistics.mean(softs):.3f}, {statistics.mean(popstd):.6f}")
