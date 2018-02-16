import pytest


def run_tests():
    pytest.main([
        '--cov=painless_sqlalchemy',
        '--cov=tests',
        '--cov-report=html',
        '--cov-report=term-missing:skip-covered',
        '--cov-config=.coveragerc'
    ])


if __name__ == '__main__':
    run_tests()
