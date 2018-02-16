import os
import ast
from tests import ROOT_DIR


class TestStructure(object):

    test_dir = os.path.join(ROOT_DIR, "tests")
    lib_dir = os.path.join(ROOT_DIR, "painless_sqlalchemy")

    def test_test_class_names(self):
        """ Test that test class names are correct."""
        for root, dirs, files in os.walk(self.test_dir):
            for a_file in files:
                if a_file.startswith("test_") and a_file.endswith(".py"):
                    path = os.path.join(root, a_file)

                    # extract camel case class name from file name
                    name = a_file[5:][:-3]
                    camel_case = ""
                    for word in filter(None, name.split("_")):
                        camel_case += word[0].upper() + word[1:]
                    name = "Test" + camel_case

                    # extract class in test file (assuming it has exactly one)
                    source = open(path, 'r').read()
                    p = ast.parse(source)
                    classes = [node.name for node in ast.walk(p)
                               if isinstance(node, ast.ClassDef)]
                    if len(classes) > 0:
                        class_name = classes[0]

                        # these should be equal
                        assert class_name == name, (
                            "Class name and file name don't match for %s. "
                            "They are \"%s\" vs \"%s\"." % (
                                path, name, class_name)
                        )

    def test_test_structure(self):
        """ Check that that test files are in correct position. """

        # find directories in the app folder
        dirs = [
            name for name in os.listdir(self.lib_dir)
            if os.path.isdir(os.path.join(self.lib_dir, name))
        ]

        # check for all files in test folder
        for a_dir in dirs:
            test_sub_dir = os.path.join(self.test_dir, a_dir)
            for root, dirs, files in os.walk(test_sub_dir):
                for a_file in files:
                    if a_file.endswith(".py") and a_file != "__init__.py":
                        assert a_file.startswith("test_"), (
                            "Test file needs to start with prefix \"test_\"")
                        ref_file = a_file[5:]
                        if ref_file != '__init__.py':
                            ref_file = ref_file.lstrip('_')
                        app_file = os.path.join(
                            self.lib_dir,
                            os.path.relpath(root, self.test_dir),
                            ref_file
                        )
                        assert os.path.isfile(app_file), (
                            "Test file " + a_file + " needs to have "
                            "corresponding file in the gitl folder."
                        )

    def test_test_init_files(self):
        """ Check that each test folder has an init file """
        assert os.path.isfile(os.path.join(self.test_dir, "__init__.py"))
        # loop over all sub directories
        for root, dirs, files in os.walk(self.test_dir):
            has_tests = False
            for a_file in files:
                if a_file.startswith("test_") and a_file.endswith(".py"):
                    has_tests = True
            if has_tests:
                # check all parent directories for init files as well
                cur_dir = root
                while (
                    os.path.normpath(cur_dir) !=
                    os.path.normpath(self.test_dir)
                ):
                    init_file = os.path.join(cur_dir, "__init__.py")
                    assert os.path.isfile(init_file), (
                        "Directory " + cur_dir + " is missing __init__ file."
                    )
                    cur_dir = os.path.join(cur_dir, "..")
