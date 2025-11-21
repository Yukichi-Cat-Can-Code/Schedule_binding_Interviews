import sys, os
print('CWD:', os.getcwd())
# ensure repo root is on sys.path
repo_root = os.getcwd()
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

modules = [
    'backend.scheduler.genetic_algorithm',
    'backend.scheduler.fitness',
    'backend.scheduler.repair_system',
    'backend.time_parser',
]
for m in modules:
    try:
        __import__(m)
        print('OK import', m)
    except Exception as e:
        print('FAIL import', m, e)
