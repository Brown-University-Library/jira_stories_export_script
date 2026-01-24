"""
Runs tests for this webap.

Usage examples:
    (all) uv run ./run_tests.py -v
    (app) uv run ./run_tests.py -v pdf_checker_app
    (file) uv run ./run_tests.py -v tests.test_environment_checks
    (class) uv run ./run_tests.py -v tests.test_environment_checks.TestEnvironmentChecks
    (method) uv run ./run_tests.py -v tests.test_environment_checks.TestEnvironmentChecks.test_check_branch_non_main_raises
"""

import argparse
import sys
import unittest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'test_path',
        nargs='?',
        default='tests',
        help='Optional test module/class/method, or a directory to discover tests from.',
    )
    args = parser.parse_args()

    if args.test_path.endswith('.py'):
        args.test_path = args.test_path[:-3]

    if args.test_path in {'tests', 'test', '.'}:
        suite = unittest.defaultTestLoader.discover('tests')
    else:
        suite = unittest.defaultTestLoader.loadTestsFromName(args.test_path)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
