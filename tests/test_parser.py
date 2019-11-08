#!/usr/bin/env python3
import argparse
import os

import pytest

from batchren import bren, helper
parser = bren.parser

"""Tests for batchren.bren written with pytest.

Performs tests for the following:
- check_optional
- expand_dir
- validate_ext
- validate_esc
- parser arguments
- parser custom actions

pytest: http://doc.pytest.org/en/latest/contents.html

Some tests utilize the tmp_path_factory fixture, which is a pathlib object.
Details here: https://docs.python.org/3/library/pathlib.html
"""


@pytest.fixture(scope="session")
def directory(tmp_path_factory):
    fs = {
        "dir": ["filea", "fileb", "filec", "file01"],
        "dir/subdir": ["filea", "fileb", "filec"]
    }
    dir_ = tmp_path_factory.mktemp("")
    for key, val in fs.items():
        d_ = dir_ / key
        d_.mkdir()
        for v in val:
            f = d_ / v
            f.write_text(v)

    return dir_


@pytest.mark.parametrize("esc_path, esc_arg, esc_res", [
    ("file*", "*", "file[*]"),
    ("file?", "?", "file[?]"),
    ("file[720]", "[]", "file[[]720]"),
    ("file[720]", "[", "file[[]720]"),
    ("file[720]", "]", "file[[]720]")
])
def test_escape_path(esc_path, esc_arg, esc_res):
    """Test escaping of special characters in path argument """
    esc_arg = bren.validate_esc(esc_arg)
    esc = helper.escape_path(esc_path, esc_arg)
    assert esc == esc_res


@pytest.mark.parametrize("esc_errarg", [
    ".",
    ".*"
    ".?"
    ".()"
    ".{}"
])
def test_validate_esc_err(esc_errarg):
    """Validate escape argument only contains '*?[]' """
    with pytest.raises(argparse.ArgumentTypeError) as err:
        esc = bren.validate_esc(esc_errarg)
        print(esc_errarg, "is erroneous")
        print(err)


@pytest.mark.parametrize("glob_pattern, glob_files", [
    ("dir/*", ["dir/file01", "dir/filea", "dir/fileb", "dir/filec"]),
    ("dir/file[ab]", ["dir/filea", "dir/fileb"]),
    ("dir/file[abc]", ["dir/filea", "dir/fileb", "dir/filec"]),
    ("dir/file01", ["dir/file01"]),
    ("dir/filea", ["dir/filea"]),
    ("dir/subdir/*", ["dir/subdir/filea", "dir/subdir/fileb", "dir/subdir/filec"]),
    ("dir/subdir/file[a]", ["dir/subdir/filea"]),
    ("**/*",
        ["dir/file01", "dir/filea", "dir/fileb", "dir/filec",
        "dir/subdir/filea", "dir/subdir/fileb", "dir/subdir/filec"]),
    ("**/file[a]", ["dir/filea", "dir/subdir/filea"])
])
def test_parser_glob(directory, glob_pattern, glob_files):
    """Tests for globbing filesnames """
    os.chdir(directory)
    files = bren.glob_files(glob_pattern)
    print(files)
    assert files == glob_files


def test_parser_defaults():
    """Test the defaults of each option without arguments """
    args = parser.parse_args([])
    print(args)
    assert args.path == "*"
    assert args.esc is None
    assert args.quiet is False
    assert args.verbose is False
    assert args.dryrun is False
    assert args.extension is None
    assert args.raw is False
    assert args.sel is False
    assert args.sort == "asc"
    assert args.prepend is None
    assert args.postpend is None
    assert args.bracket_remove is None
    assert args.case is None
    assert args.shave is None
    assert args.slice is None
    assert args.spaces is None
    assert args.translate is None
    assert args.regex is None
    assert args.sequence is None


@pytest.mark.parametrize("opt_arg, opt_res", [
    (["dir", "-pre", "bla"], True),
    (["dir", "-post", "bla"], True),
    (["dir", "-sp"], True),
    (["dir", "-tr", "ab", "cd"], True),
    (["dir", "-c", "lower"], True),
    (["dir", "-sl", "0:1"], True),
    (["dir", "-sh", "1:1"], True),
    (["dir", "-bracr", "curly"], True),
    (["dir", "-re", "bla"], True),
    (["dir", "-seq", "%f"], True),
    (["dir", "--sort", "man", "-pre", "bla"], True),
    (["dir", "--sel", "-pre", "bla"], True),
    ([""], False),
    (["dir", "-v"], False),
    (["dir", "-q"], False),
    (["dir", "--dryrun"], False),
    (["dir", "--dryrun", "-v"], False),
    (["dir", "--dryrun", "-q"], False),
    (["dir", "--esc"], False),
    (["dir", "--esc", "-v"], False),
    (["dir", "--esc", "-q"], False),
    (["dir", "--raw"], False),
    (["dir", "--raw", "-v"], False),
    (["dir", "--raw", "-q"], False),
    (["dir", "--sort", "man"], False),
    (["dir", "--sel"], False),
])
def test_check_optional(opt_arg, opt_res):
    """Test which arguments have renaming effects on files """
    args = parser.parse_args(opt_arg)
    chk = bren.check_optional(args)
    assert chk == opt_res


@pytest.mark.parametrize("path_arg, path_res", [
    # tests for expanding directories
    ("dir/", "dir/*"),
    ("dir", "dir/*"),
    ("dir/subdir", "dir/subdir/*"),
    # not directories, don't change anything
    ("file.txt", "file.txt"),
    ("dir/subdir/hello.txt", "dir/subdir/hello.txt")
])
def test_expand_dir(tmpdir, path_arg, path_res):
    """Test directory expansion with directories and files """
    tmpdir.mkdir("dir").mkdir("subdir")
    tmpdir.chdir()
    p = tmpdir.join("hello.txt")

    res = bren.expand_dir(path_arg)
    print(res)
    assert res == path_res


@pytest.mark.parametrize("ext_errarg", [
    "/ext",
    "e/xt",
    "ex/t",
    "/ex/t",
    r"\ext",
    r"e\xt",
    r"ex\t",
    r"\ex\t"
])
def test_validate_ext(ext_errarg):
    """Validate extension argument does not contain '/' characters """
    with pytest.raises(argparse.ArgumentTypeError) as err:
        ext = bren.validate_ext(ext_errarg)
        print(ext_errarg, "is erroneous")
        print(err)


@pytest.mark.parametrize("tr_arg", [
    (["ab", "cd"]),
    (["cd", "cd"])
])
def test_parser_translate(tr_arg):
    """Test translate argument returns a tuple of values """
    args = parser.parse_args(["-tr", *tr_arg])
    print(args.translate)
    assert args.translate == tuple(tr_arg)


@pytest.mark.parametrize("tr_errarg", [
    ([""]),
    (["ab"]),
    (["ab", "cde"]),
    (["abc", "de"])
])
def test_parser_translate_err(tr_errarg):
    """Test translate argument errors """
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(["-tr", *tr_errarg])
        print(tr_errarg, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("sl_arg, sl_res", [
    (["1"], [None, 1, None]),
    (["1:"], [1, None, None]),
    (["1:2"], [1, 2, None]),
    (["1:2:"], [1, 2, None]),
    (["1:2:3"], [1, 2, 3]),
    ([" 1 "], [None, 1, None]),
    ([" 1: "], [1, None, None]),
    (["1: 2"], [1, 2, None]),
    (["1:2 "], [1, 2, None]),
    (["1 :2: 3 "], [1, 2, 3]),
    ([":1"], [None, 1, None]),
    ([":1:"], [None, 1, None]),
    ([":1:2"], [None, 1, 2]),
    (["1::2"], [1, None, 2]),
    ([":1:2"], [None, 1, 2]),
    (["::2"], [None, None, 2])
])
def test_parser_slice(sl_arg, sl_res):
    """Test slice argument returns correct slice object """
    args = parser.parse_args(["-sl", *sl_arg])
    sl = slice(*sl_res)
    assert args.slice == sl


@pytest.mark.parametrize("sl_errarg", [
    ([""]),
    (["1:2:1:"]),
    (["1:2:1:2"]),
    (["a"]),
    (["a:"]),
    (["1:a"]),
    (["1:1:a"])
])
def test_parser_slice_err(sl_errarg):
    """Test slice argument errors """
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(["-sl", *sl_errarg])
        print(sl_errarg, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("sh_arg, sh_res", [
    ("1", (slice(1, None, None), slice(None))),
    ("1:", (slice(1, None, None), slice(None))),
    (":1", (slice(None), slice(None, -1, None))),
    ("1:1", (slice(1, None, None), slice(None, -1, None))),
    ("2:2", (slice(2, None, None), slice(None, -2, None)))
])
def test_parser_shave(sh_arg, sh_res):
    """Test shave argument returns correct shave object """
    args = parser.parse_args(["-sh", sh_arg])
    head, tail = sh_res
    assert args.shave == (head, tail)


@pytest.mark.parametrize("sh_errarg", [
    ([""]),
    (["1:2:"])
])
def test_parser_shave_err(sh_errarg):
    """Test shave argument errors """
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(["-sh", *sh_errarg])
        print(sh_errarg, "is erroneous")
        assert err.type == SystemExit


# tests for reg_arg, reg_res


@pytest.mark.parametrize("reg_errarg", [
    ([""]),
    (["", "reg"]),
    (["lecture", "lec", "a"]),
    (["lecture", "lec", "1", "2"])
    # add more regex tests...
])
def test_parser_regex_err(reg_errarg):
    """Test regular expression argument errors """
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(["-re", *reg_errarg])
        print(reg_errarg, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("bracr_arg, bracr_res", [
    (["curly"], ("curly", 0)),
    (["round"], ("round", 0)),
    (["square"], ("square", 0)),
    (["curly", "2"], ("curly", 2))
])
def test_parser_bracket(bracr_arg, bracr_res):
    """Test bracket remove argument returns appropriate tuple """
    args = parser.parse_args(["-bracr", *bracr_arg])
    val1, val2 = bracr_res
    assert args.bracket_remove == (val1, val2)


@pytest.mark.parametrize("bracr_errarg", [
    ([""]),
    (["squiggle"]),
    (["bracket"]),
    (["curly", "round"]),
    (["curly", "round", "square"])
])
def test_parser_bracket_err(bracr_errarg):
    """Test bracket remove argument error """
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(["-bracr", *bracr_errarg])
        print(bracr_errarg, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("seq_errarg", [
    (["%na"]),
    (["%n2:1:4:1:"]),
    (["%n2:1:4:2:1"]),
    (["%n-1:1:4"]),
    (["%n:-1:"]),
    (["%ab"]),
    (["%a-:a:b"]),
    (["%a:1"]),
    (["%a:b:1"]),
    (["%a:%b:1"])
])
def test_parser_sequence_err(seq_errarg):
    """Test sequence argument errors """
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(["-seq", *seq_errarg])
        print(seq_errarg, "is errorneous")
        assert err.type == SystemExit
