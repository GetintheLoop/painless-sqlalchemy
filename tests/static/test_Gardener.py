import os

from py_gardener.StaticTestBase import StaticTestBase


class TestGardener(StaticTestBase):
    ROOT_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
    TEST_DIR = os.path.join(ROOT_DIR, "tests")
    LIB_DIR = os.path.join(ROOT_DIR, "painless_sqlalchemy")
