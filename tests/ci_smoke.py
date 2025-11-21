import os, subprocess, sys

# CI-friendly smoke test: ensure repo root on PYTHONPATH and run smoke_test.py
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env = os.environ.copy()
env['PYTHONPATH'] = repo_root + os.pathsep + env.get('PYTHONPATH','')

cmd = [sys.executable, os.path.join('backend','benchmarks','smoke_test.py')]
print('Running:', ' '.join(cmd))
proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
print(proc.stdout)
if proc.returncode != 0:
    raise SystemExit(proc.returncode)
