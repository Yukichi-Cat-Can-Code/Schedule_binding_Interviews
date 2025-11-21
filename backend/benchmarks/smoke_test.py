import importlib, sys, os, importlib.util

print('Import-by-path smoke test:')

def load_by_path(name, path):
    if not os.path.exists(path):
        print(f'  SKIP: {path} does not exist')
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        print(f'  OK: loaded {path} as {name}')
        return mod
    except Exception as e:
        print(f'  FAIL: loading {path}: {e}')
        return None

# try loading core scheduler files by path (avoid package import issues)
core_paths = [
    ('genetic_algorithm', os.path.join('backend','scheduler','genetic_algorithm.py')),
    ('fitness', os.path.join('backend','scheduler','fitness.py')),
    ('repair_system', os.path.join('backend','scheduler','repair_system.py')),
    ('time_parser', os.path.join('backend','scheduler','time_parser.py')),
]

for nm, p in core_paths:
    load_by_path(nm, p)

# load plotting module and call functions directly
plot_mod = load_by_path('viz', os.path.join('backend','benchmarks','visualize_sweep_and_convergence.py'))

if plot_mod:
    try:
        # call functions: boxplot, zoom, single-run convergence (forced), aggregated
        print('\nCalling plotting functions...')
        try:
            plot_mod.make_boxplot()
            plot_mod.make_boxplot_zoom()
        except Exception as e:
            print('  Warning: boxplot functions raised:', e)
        try:
            # call single-run convergence forcing a known run by temporarily setting sys.argv
            old_argv = sys.argv.copy()
            sys.argv = [old_argv[0], 'backend/logs/ga_sweep_ext_sp=0.05_seed=101.ndjson']
            try:
                plot_mod.make_convergence_plot()
            finally:
                sys.argv = old_argv
        except Exception as e:
            print('  Warning: make_convergence_plot raised:', e)
        try:
            plot_mod.make_aggregated_convergence_plot()
        except Exception as e:
            print('  Warning: make_aggregated_convergence_plot raised:', e)
    except Exception as e:
        print('Error while executing plotting functions:', e)

# Check expected outputs
expected = [
    os.path.join('backend','benchmarks','boxplot_soft_penalty.png'),
    os.path.join('backend','benchmarks','boxplot_soft_penalty_zoom.png'),
    os.path.join('backend','benchmarks','convergence_aggregated__ieee.png'),
    os.path.join('backend','benchmarks','convergence_ga_sweep_ext_sp=0.05_seed=101__ieee.png'),
]

print('\nOutput files existence:')
all_ok = True
for p in expected:
    ok = os.path.exists(p)
    print(f'  {p}:', 'FOUND' if ok else 'MISSING')
    all_ok = all_ok and ok

if not all_ok:
    print('\nSmoke test: FAILED - missing expected outputs')
    sys.exit(2)
else:
    print('\nSmoke test: SUCCESS - all expected outputs present')
    sys.exit(0)
