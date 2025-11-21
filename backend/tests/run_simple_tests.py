"""Simple runner to execute repair_system tests without pytest.

This loads the test module and runs each function, reporting failures.
"""
import sys
import os
import traceback

TEST_ROOT = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(TEST_ROOT, '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import importlib
import glob

# Dynamically import all test_*.py modules in this directory
tests_mods = []
for path in glob.glob(os.path.join(TEST_ROOT, 'test_*.py')):
    modname = os.path.splitext(os.path.basename(path))[0]
    # import as tests.<modname>
    try:
        m = importlib.import_module(f'tests.{modname}')
    except Exception:
        m = importlib.import_module(modname)
    tests_mods.append(m)

# Collect callables that start with 'test_' from all modules
funcs = []
for tests_mod in tests_mods:
    for name in dir(tests_mod):
        if name.startswith('test_'):
            funcs.append(getattr(tests_mod, name))

failures = 0
for fn in funcs:
    print(f"Running {fn.__name__}...")
    try:
        fn()
        print(f"  OK: {fn.__name__}")
    except AssertionError as e:
        failures += 1
        print(f"  FAIL: {fn.__name__} -> AssertionError: {e}")
        traceback.print_exc()
    except Exception as e:
        failures += 1
        print(f"  ERROR: {fn.__name__} -> {e}")
        traceback.print_exc()

if failures:
    print(f"\n{failures} test(s) failed")
    sys.exit(2)
else:
    print("\nAll tests passed")
    sys.exit(0)
