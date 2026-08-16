from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
tests = sorted(ROOT.glob("GUI_*.py"))
passed = failed = 0

for test in tests:
    print("=" * 78)
    print(f"TEST: 08_GUI_INTEGRACIO/{test.name}")
    result = subprocess.run([sys.executable, str(test)],
                            cwd=str(ROOT.parent.parent),
                            text=True)
    if result.returncode == 0:
        print(f"PASS: {test.name}")
        passed += 1
    else:
        print(f"FAIL: {test.name}")
        failed += 1

print("=" * 78)
print(f"GUI TESZTEK: {len(tests)} | PASS: {passed} | FAIL: {failed}")
raise SystemExit(1 if failed else 0)
