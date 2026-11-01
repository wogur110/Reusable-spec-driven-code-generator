"""Retained unittest runner that rejects empty/skipped required suites."""
import argparse
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
parser = argparse.ArgumentParser()
parser.add_argument('directory')
parser.add_argument('--report', required=True)
args = parser.parse_args()
suite = unittest.defaultTestLoader.discover(str(ROOT/args.directory), top_level_dir=str(ROOT))
result = unittest.TextTestRunner(verbosity=2).run(suite)
good = result.wasSuccessful() and result.testsRun > 0 and not result.skipped
report = {'status': 'PASS' if good else 'FAIL', 'collected': result.testsRun, 'passed': result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped), 'failed': len(result.failures)+len(result.errors), 'skipped': len(result.skipped), 'failures': [(str(t), text) for t,text in result.failures+result.errors]}
Path(args.report).parent.mkdir(parents=True, exist_ok=True)
Path(args.report).write_text(json.dumps(report, indent=2))
sys.exit(0 if good else 1)
