from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
tests = sorted(ROOT.rglob("TEST_*.py"))
tests = [p for p in tests if p.name != "FUTTATAS_OSSZES_TEST.py"]

passed = failed = 0
for test in tests:
    print("=" * 78)
    print(f"TEST: {test.relative_to(ROOT)}")
    result = subprocess.run(
        [sys.executable, str(test)],
        cwd=str(ROOT.parent.parent),
        text=True,
    )
    if result.returncode == 0:
        print(f"PASS: {test.relative_to(ROOT)}")
        passed += 1
    else:
        print(f"FAIL: {test.relative_to(ROOT)}")
        failed += 1

print("=" * 78)
print(f"TESZTEK: {len(tests)} | PASS: {passed} | FAIL: {failed}")
raise SystemExit(1 if failed else 0)
