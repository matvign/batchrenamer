#!/usr/bin/env python3
import os

import pytest

from batchren import bren, renamer
parser = bren.parser

"""Tests for batchren.renamer written with pytest.

Performs tests for the following:
- partfile
- joinparts
- optional arguments
- conflict resolution
- renaming with temporary files

Some tests utilize the tmp_path_factory fixture, which is a pathlib object.
Details here: https://docs.python.org/3/library/pathlib.html
"""


@pytest.mark.parametrize("path_arg, path_res", [
    (["file", False], ("", "file", "")),
    (["file.txt", False], ("", "file", ".txt")),
    (["archive.tar.gz", False], ("", "archive.tar", ".gz")),
    (["dir/file", False], ("dir", "file", "")),
    (["dir/file.txt", False], ("dir", "file", ".txt")),
    (["dir/subdir/file", False], ("dir/subdir", "file", "")),
    (["dir/subdir/file.txt", False], ("dir/subdir", "file", ".txt")),
    (["file", True], ("", "file", "")),
    (["file.txt", True], ("", "file.txt", "")),
    (["archive.tar.gz", True], ("", "archive.tar.gz", "")),
    (["dir/file", True], ("dir", "file", "")),
    (["dir/file.txt", True], ("dir", "file.txt", "")),
    (["dir/subdir/file", True], ("dir/subdir", "file", "")),
    (["dir/subdir/file.txt", True], ("dir/subdir", "file.txt", ""))
])
def test_misc_partfile(path_arg, path_res):
    res = renamer.partfile(*path_arg)
    assert res == path_res


@pytest.mark.parametrize("join_arg, join_res", [
    (["", "file", "", False], ("file")),
    (["", " file", "", False], ("file")),
    (["", "  file  ", "", False], ("file")),
    (["", ".file", "", False], (".file")),
    (["", " .file", "", False], (".file")),
    (["", ". file", "", False], (". file")),

    (["dir", "file", "", False], ("dir/file")),
    (["dir", " file", "", False], ("dir/file")),
    (["dir", "  file  ", "", False], ("dir/file")),
    (["dir", ".file", "", False], ("dir/.file")),
    (["dir", " .file", "", False], ("dir/.file")),
    (["dir", ". file", "", False], ("dir/. file")),

    (["", "file", ".txt", False], ("file.txt")),
    (["", " file", ".txt", False], ("file.txt")),
    (["", "  file  ", ".txt", False], ("file.txt")),
    (["", ".file", ".txt", False], (".file.txt")),
    (["", " .file", ".txt", False], (".file.txt")),
    (["", ". file", ".txt", False], (". file.txt")),

    (["dir", "file", ".txt.sav", False], ("dir/file.txt.sav")),
    (["dir", "file", "...  e  xt?. ext. .."], ("dir/file.ext?.ext")),

    (["dir", "file  ", ".txt", True], ("dir/file  .txt")),
    (["dir", "  file", ".txt", True], ("dir/file.txt"))
])
def test_misc_joinparts(join_arg, join_res):
    res = renamer.joinparts(*join_arg)
    assert res == join_res


@pytest.mark.parametrize("pre_arg, pre_src, pre_dest", [
    (["lecture"], ["01", "02"], ["lecture01", "lecture02"]),
    (["lecture"], ["dir/01", "dir/02"], ["dir/lecture01", "dir/lecture02"])
])
def test_filter_prepend(pre_arg, pre_src, pre_dest):
    args = parser.parse_args(["-pre", *pre_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(pre_src, filters, args.extension, args.raw)
    print(dest)
    print(pre_dest)
    assert dest == pre_dest


@pytest.mark.parametrize("post_arg, post_src, post_dest", [
    (["pend"], ["ap", "pre"], ["append", "prepend"]),
    (["_unsw"], ["dir/lec01", "dir/lec02"], ["dir/lec01_unsw", "dir/lec02_unsw"]),
    (["_usyd"], ["dir/lec01.pdf", "dir/lec02.pdf"], ["dir/lec01_usyd.pdf", "dir/lec02_usyd.pdf"])
])
def test_filter_postpend(post_arg, post_src, post_dest):
    args = parser.parse_args(["-post", *post_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(post_src, filters, args.extension, args.raw)
    print(dest)
    print(post_dest)
    assert dest == post_dest


"""
def pairwise(lst1, lst2, tmpdir=None):
    if len(lst1) != len(lst2):
        raise Exception('list lengths must be equal!')
    it1, it2 = iter(lst1), iter(lst2)
    try:
        while True:
            if not tmpdir:
                yield next(it1), next(it2)
            else:
                yield tmpdir.join(next(it1)), tmpdir.join(next(it2))
    except StopIteration:
        return

@pytest.mark.parametrize("pre_args, pre_before, pre_after", [
    (['-pre', 'pre_', '-v'], ['file1', 'file2'], ['pre_file1', 'pre_file2']),
    (['-pre', 'pre_', '-v'], ['FILE1', 'FILE2'], ['pre_FILE1', 'pre_FILE2'])
])
def test_rename_prepend(pre_args, pre_before, pre_after, tmpdir, monkeypatch):
    monkeypatch.setattr('builtins.input', lambda x: 'y')
    before_lst, after_lst = [], []
    for before, after in pairwise(pre_before, pre_after, tmpdir):
        before.write(before)
        before_lst.append(before)
        after_lst.append(after)

        assert before.check(file=1)
        assert after.check(file=0)

    tmpdir.chdir()
    args = parser.parse_args(pre_args)
    main.main(args, parser)
    for before, after in pairwise(before_lst, after_lst):
        assert before.check(file=0)
        assert after.check(file=1)
        assert after.read() == before


@pytest.mark.parametrize("sp_arg, sp_origpath, sp_dirpath, sp_fname, sp_res", [
    # tests for space
    # arg, origpath, dirpath, filename, expected result
    ('_', '', '', 'file a', 'file_a'),
    ('', '', '', 'file a', 'filea'),
    ('.', '', '', 'file b', 'file.b'),
    ('THIS', '', '', 'file c', 'fileTHISc'),
    ('.', '', '', 'f i l e', 'f.i.l.e')
])
def test_filter_spaces(sp_arg, sp_origpath, sp_dirpath, sp_fname, sp_res):
    args = parser.parse_args(['-sp', sp_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, sp_dirpath, sp_dirpath, sp_fname)
    print('oldname: {} --> newname: {}'.format(sp_fname, newname))
    assert newname == sp_res


def test_filter_spaces_extra():
    # special test case for spaces with no arguments
    # sets spaces to _
    args = parser.parse_args(['-sp'])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, 'file a', '', 'file a')
    print('oldname: {} --> newname: {}'.format('file a', newname))
    assert newname == 'file_a'


@pytest.mark.parametrize("c_arg, c_origpath, c_dirpath, c_fname, c_res", [
    # tests for case
    # case is only applied to the filename, not any extension
    # which is why extensions aren't tested here
    # arg, origpath, dirpath, filename, expected result
    ('upper', '', '', 'file', 'FILE'),
    ('upper', '', '', 'file1', 'FILE1'),
    ('lower', '', '', 'FILE', 'file'),
    ('lower', '', '', 'FILE1', 'file1'),
    ('swap', '', '', 'FILE', 'file'),
    ('swap', '', '', 'file', 'FILE'),
    ('swap', '', '', 'fiLE', 'FIle'),
    ('swap', '', '', 'FIle', 'fiLE'),
    ('cap', '', '', 'FileName', 'Filename'),
    ('cap', '', '', 'file name', 'File Name'),
    ('cap', '', '', 'file1 1name', 'File1 1Name'),
    ('cap', '', '', 'file1_1name', 'File1_1Name'),
    ('cap', '', '', 'file1.1name', 'File1.1Name'),
    ('upper  ', '', '', 'file', 'FILE'),
    ('lower  ', '', '', 'FILE', 'file'),
    ('swap   ', '', '', 'fIle', 'FiLE')
])
def test_filter_cases(c_arg, c_origpath, c_dirpath, c_fname, c_res):
    args = parser.parse_args(['-c', c_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, c_dirpath, c_dirpath, c_fname)
    print('oldname: {} --> newname: {}'.format(c_fname, newname))
    assert newname == c_res


@pytest.mark.parametrize("c_errarg", [
    # errors for case
    (['-v']),
    (['bla', '-v']),
    (['garbage', '-v']),
    (['bug', '-v']),
    (['1', '-v']),
])
def test_filter_case_err(c_errarg):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-c', *c_errarg])
        print(c_errarg, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("tr_arg, tr_origpath, tr_dirpath, tr_fname, tr_res", [
    # tests for translate
    # arg, origpath, dirpath, filename, expected result
    (['a', 'b'], '', '', 'filea', 'fileb'),
    (['fle', 'tbi'], '', '', 'filea', 'tibia'),
    (['1', '2'], '', '', 'file1', 'file2')
])
def test_filter_translate(tr_arg, tr_origpath, tr_dirpath, tr_fname, tr_res):
    args = parser.parse_args(['-tr', *tr_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, tr_origpath, tr_dirpath, tr_fname)
    print('oldname: {} --> newname: {}'.format(tr_fname, newname))
    assert newname == tr_res


@pytest.mark.parametrize("tr_errargs", [
    # errors for translate parser
    # error if no values, both values are empty or not same length
    # note: argparse handles len(args) > 2
    (['-v']),
    (['', '', '-v']),
    (['a', '-v']),
    (['a', 'bc', '-v']),
    (['', 'bc', '-v'])
])
def test_filter_translate_err(tr_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-tr', *tr_errargs])
        print(tr_errargs, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("sl_arg, sl_origpath, sl_dirpath, sl_fname, sl_res", [
    # tests for slice
    # arg, origpath, dirpath, filename, expected result
    (':4', '', '', 'filea', 'file'),
    ('1:5', '', '', 'filea', 'ilea'),
    ('2:', '', '', 'filea', 'lea')
])
def test_filter_slice(sl_arg, sl_origpath, sl_dirpath, sl_fname, sl_res):
    args = parser.parse_args(['-sl', sl_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, sl_origpath, sl_dirpath, sl_fname)
    print('oldname: {} --> newname: {}'.format(sl_fname, newname))
    assert newname == sl_res


@pytest.mark.parametrize("sl_errargs", [
    # errors for slice parser
    # error if slice is empty, cannot convert into slice object,
    # value is not an integer
    # note: argparse handles len(args) > 1
    (['-v']),
    (['', '-v']),
    (['1:2:3:', '-v']),
    (['1:2:3:4', '-v']),
    (['1:2:3:4:', '-v']),
    (['a:', '-v']),
    (['a:1', '-v']),
    (['1:b', '-v']),
    ([':b', '-v']),
    (['a:b', '-v']),
    (['a:b:c', '-v']),
    (['a::c', '-v']),
    (['a:b:', '-v']),
    (['1e:2b:3c', '-v'])
])
def test_filter_slice_err(sl_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-sl', *sl_errargs])
        print(sl_errargs, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("sh_arg, sh_origpath, sh_dirpath, sh_fname, sh_res", [
    # tests for shave
    # arg, origpath, dirpath, filename, expected result
    (':1', '', '', 'filea', 'file'),
    ('1:', '', '', 'filea', 'ilea'),
    ('1:1', '', '', 'filea', 'ile')
])
def test_filter_shave(sh_arg, sh_origpath, sh_dirpath, sh_fname, sh_res):
    args = parser.parse_args(['-sh', sh_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, sh_origpath, sh_dirpath, sh_fname)
    print('oldname: {} --> newname: {}'.format(sh_fname, newname))
    assert newname == sh_res


@pytest.mark.parametrize("sh_errargs", [
    # errors for shave parser
    # error if value is empty, non-numeric character,
    # more than two values, both values are none,
    # any value is negative
    # note: argparse handles len(args) > 1
    (['-v']),
    (['', '-v']),
    (['a', '-v']),
    (['a:', '-v']),
    ([':b', '-v']),
    (['a:b', '-v']),
    (['1:b', '-v']),
    (['a:1', '-v']),
    (['1:2:3', '-v']),
    (['1:2:3:', '-v']),
    (['1:2:3:4', '-v']),
    (['a:b:c', '-v']),
    ([':', '-v']),
    (['-1:', '-v']),
    ([':-1', '-v']),
    (['1:-1', '-v']),
    (['-1:1', '-v']),
    (['1:-1:5', '-v']),
    (['-1:1:5', '-v']),
])
def test_filter_shave_err(sh_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-sh', *sh_errargs])
        print(sh_errargs, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("bracr_arg, bracr_origpath, bracr_dirpath, bracr_fname, bracr_res", [
    # tests for bracket removal
    # arg, origpath, dirpath, filename, expected result
    (['round'], '', '', '(filea)file(file)', 'file'),
    (['round'], '', '', 'filea', 'filea'),
    (['round '], '', '', 'filea', 'filea'),
    (['round'], '', '', '(file)(file)(file)file', 'file'),
    (['round', '0'], '', '', '(file)(file)(file)file', 'file'),
    (['round', '1'], '', '', '(file)file(file)', 'file(file)'),
    (['  round  ', ' 1 '], '', '', '(file)file(file)', 'file(file)'),
    (['round', '2'], '', '', '(file)file(file)', '(file)file'),
    (['round', '3'], '', '', '(file)file(file)', '(file)file(file)'),
    (['square', '1'], '', '', '[file]file[file]', 'file[file]'),
    (['square', '2'], '', '', '[file]file[file]', '[file]file'),
    (['square', '3'], '', '', '[file]file[file]', '[file]file[file]'),
    (['curly', '1'], '', '', '{file}file{file}', 'file{file}'),
    (['curly', '2'], '', '', '{file}file{file}', '{file}file'),
    (['curly', '3'], '', '', '{file}file{file}', '{file}file{file}'),
])
def test_filter_bracr(bracr_arg, bracr_origpath, bracr_dirpath, bracr_fname, bracr_res):
    args = parser.parse_args(['-bracr', *bracr_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, bracr_origpath, bracr_dirpath, bracr_fname)
    print('oldname: {} --> newname: {}'.format(bracr_fname, newname))
    print('expected:', bracr_res)
    assert newname == bracr_res


@pytest.mark.parametrize("bracr_rec_arg, bracr_type", [
    # special test cases for bracr
    # bracr doesn't handle recursive brackets and should fail
    ('((file))file', 'round'),
    ('[[file]]file', 'square'),
    ('{{file}}file', 'curly')
])
def test_filter_bracr_extra(bracr_rec_arg, bracr_type):
    args = parser.parse_args(['-bracr', bracr_type])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, '', '', bracr_rec_arg)
    assert newname != 'file'


@pytest.mark.parametrize("bracr_errargs", [
    # errors for bracket remove
    # error if no arguments, too many arguments
    # first argument not in (round, square, curly)
    # second argument is not an integer >= 0
    # nargs = *, so argparse doesn't handle argument lengths
    (['-v']),
    (['something', '-v']),
    (['roun', '-v']),
    (['CURLY', '-v']),
    (['ROUND', '-v']),
    (['SQUARE', '-v']),
    (['curly', 'HERE', '-v']),
    (['curly', '', '-v']),
    (['curly', '1a', '-v']),
    (['curly', '-1', '-v']),
    (['curly', '1', '2', '-v'])     # len(args) > 2
])
def test_filter_bracr_err(bracr_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-bracr', *bracr_errargs])
        print(bracr_errargs, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("re_arg, re_origpath, re_dirpath, re_fname, re_res", [
    # tests for regex
    # arg, origpath, dirpath, filename, expected result
    (['f', 'p'], '', '', 'file', 'pile'),
    (['fi', 'pa'], '', '', 'file', 'pale'),
    (['d', 'e'], '', '', 'fiddle', 'fieele'),
    (['d'], '', '', 'fiddle', 'file'),                # remove all 'd'
    (['d', 'l'], '', '', 'fiddle', 'fillle'),         # replace all 'd' with 'l'
    (['d', 'l', '1'], '', '', 'fiddle', 'fildle'),    # replace 1st 'd' with 'l'
    (['d', '', '1'], '', '', 'diddily', 'iddily'),
    (['d', '', '4'], '', '', 'diddily do', 'diddily o'),
    # replace 5th 'd', which doesn't exist, so do nothing
    (['d', '', '5'], '', '', 'diddily do', 'diddily do'),
    (['\\d+', 'no.2'], '', '', '02bla', 'no.2bla')
])
def test_filter_regex(re_arg, re_origpath, re_dirpath, re_fname, re_res):
    args = parser.parse_args(['-re', *re_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, re_origpath, re_dirpath, re_fname)
    print('oldname: {} --> newname: {}'.format(re_fname, newname))
    print('expected:', re_res)
    assert newname == re_res


@pytest.mark.parametrize("re_errargs", [
    # errors for regex
    # nargs = *, so argparse doesn't handle argument lengths
    (['-v']),
    (['', '-v']),
    (['a', 'b', '2', '2', '-v'])  # len(args) > 3
])
def test_filter_re_err(re_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-re', *re_errargs])
        print(re_errargs, "is erroneous")
        assert err.type == SystemExit
"""
