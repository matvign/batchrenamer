import pytest

import main
from batchren import _version

'''
tests for parser
'''

parser = main.parser


def test_parser_version():
    print(main.__version__, _version.__version__)
    assert main.__version__ == _version.__version__


@pytest.mark.parametrize("path_args, path_res", [
    (['tests', '-v'], 'tests/*'),
    (['tests/', '-v'], 'tests/*')
])
def test_parser_expanddir(path_args, path_res):
    args = parser.parse_args(path_args)
    print(args)
    assert args.path == path_res


def test_parser_translate():
    data = ['tests/testdir', '-tr', 'ab', 'cd', '-v']
    args = parser.parse_args(data)
    print(args.translate)
    assert args.translate == ('ab', 'cd')


@pytest.mark.parametrize("tr_errargs", [
    (['-v']),
    (['a', '-v']),
    (['a', 'b', 'c', '-v']),
    (['a', 'bc', '-v'])
])
def test_parser_translate_err(tr_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-tr', *tr_errargs])
        print(tr_errargs, "is erroneous")
        assert err.type == SystemExit