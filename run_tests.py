import pytest


def run_tests():
    pytest.main([
        '--cov=painless_sqlalchemy',
        # '--cov-report',
        # 'html'
    ])


if __name__ == '__main__':
    run_tests()
