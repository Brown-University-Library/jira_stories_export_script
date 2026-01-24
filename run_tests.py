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
