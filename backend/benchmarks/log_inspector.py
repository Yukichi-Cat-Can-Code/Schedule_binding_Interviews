import glob, json, os

LOG_DIR = os.path.join('..', 'backend', 'logs') if os.path.exists(os.path.join('..','backend','logs')) else 'backend/logs'
files = sorted(glob.glob(os.path.join('backend','logs','*.ndjson')))

if not files:
    print('No log files found in backend/logs')
    raise SystemExit(1)

def find_soft_penalty(obj):
    if not isinstance(obj, dict):
        return None
    # known places
    biz = obj.get('biz_kpi') if isinstance(obj.get('biz_kpi'), dict) else None
    if biz:
        for k in ('total_soft_penalties','soft_penalties','soft_penalty_count'):
            if k in biz and biz[k] is not None:
                try:
                    return int(biz[k])
                except Exception:
                    pass
    ah = obj.get('algo_health') if isinstance(obj.get('algo_health'), dict) else None
    if ah:
        for k in ('soft_penalty_count','soft_penalties'):
            if k in ah and ah[k] is not None:
                try:
                    return int(ah[k])
                except Exception:
                    pass
    for k in ('total_soft_penalties','soft_penalty_count','soft_penalties'):
        if k in obj and obj[k] is not None:
            try:
                return int(obj[k])
            except Exception:
                pass
    # recursive
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

summary = []
for p in files:
    vals = []
    sample_lines = []
    total_lines = 0
    try:
        with open(p,'r',encoding='utf-8') as f:
            for i,line in enumerate(f):
                total_lines += 1
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                v = find_soft_penalty(obj)
                if v is not None:
                    vals.append(v)
                    sample_lines.append((i+1,v,obj))
    except Exception as e:
        print('Failed to read',p, e)
        continue
    unique = sorted(set(vals))
    has = len(unique)>0
    sample = sample_lines[0][1] if sample_lines else None
    summary.append((os.path.basename(p), has, unique[:5], sample, total_lines))

# Print short table
print('filename,found,unique_values(example),sample_value,total_lines')
for row in summary:
    print(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}")

# Print a short human readable block for files with values
print('\nDetailed files with soft-penalties:')
for row in summary:
    if row[1]:
        print(f"- {row[0]}: sample values {row[2]}, sample first={row[3]}")
