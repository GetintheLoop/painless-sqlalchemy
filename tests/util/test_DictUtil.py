from painless_sqlalchemy.util.DictUtil import flatten_dict


class TestDictUtil(object):

    def test_flatten_dict(self):
        assert flatten_dict({
            'a': {
                'b': {
                    'c': 'd',
                    'e': 'f'
                },
                'g': [{
                    'h': 'i'
                }, {
                    'j': 'k'
                }],
                'l': None
            }
        }, filter_none=True) == {
            'a.b.c': 'd',
            'a.b.e': 'f',
            'a.g.h': 'i',
            'a.g.j': 'k'
        }
