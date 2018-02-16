from tests import list_project_files


class TestLineEndings(object):
    """ Test that lines do not end with backslash - use parenthesis instead """

    def test_line_endings(self):
        for file_ in list_project_files():
            with open(file_, 'r') as f:
                for l in f.readlines():
                    assert not l.rstrip().endswith("\\"), file_ + " @ " + l
