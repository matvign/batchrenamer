import pytest

import main
from batchren import _version

parser = main.parser

def test_parser_version():
    print(main.__version__, _version.__version__)
    assert main.__version__ == _version.__version__

def test_parser_expanddir_01():
    data = ['tests', '-v']
    args = parser.parse_args(data)
    print(args)
    assert args.path == 'tests/*'

def test_parser_expanddir_02():
    data = ['tests/', '-v']
    args = parser.parse_args(data)
    print(args)
    assert args.path == 'tests/*'

def test_parser_translate_01():
    data = ['tests/testdir', '-tr', 'ab', 'cd', '-v']
    args = parser.parse_args(data)
    print(args.translate)
    assert args.translate == ('ab', 'cd')

def test_parser_translate_02():
    data = ['tests/testdir', '-tr', '-v']
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(data)
        print("No arguments, should exit")
        assert err.type == SystemExit

def test_parser_translate_03():
    data = ['tests/testdir', '-tr', 'a', '-v']
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(data)
        print("Missing argument, should exit")
        assert err.type == SystemExit

def test_parser_translate_04():
    data = ['tests/testdir', '-tr', 'a', 'b', 'c', '-v']
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(data)
        print("Too many arguments, should exit")
        assert err.type == SystemExit

def test_parser_translate_04():
    data = ['tests/testdir', '-tr', 'a', 'bc', '-v']
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(data)
        print("lengths aren't equal, should exit")
        assert err.type == SystemExit