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
- cycle renaming

Some tests utilize the tmp_path_factory fixture, which is a pathlib2 object.
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
    """Tests for pre argument. Add text before filename """
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
    """Tests for post argument. Add text after filename """
    args = parser.parse_args(["-post", *post_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(post_src, filters, args.extension, args.raw)
    print(dest)
    print(post_dest)
    assert dest == post_dest


@pytest.mark.parametrize("sp_arg, sp_src, sp_dest", [
    ("", ["file", "file a", "file b"], ["file", "filea", "fileb"]),
    (".", ["file", "file a", "file b"], ["file", "file.a", "file.b"])
])
def test_filter_spaces(sp_arg, sp_src, sp_dest):
    """Tests for spaces argument. Replace spaces with the specified character """
    args = parser.parse_args(["-sp", sp_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(sp_src, filters, args.extension, args.raw)
    print(dest)
    print(sp_dest)
    assert dest == sp_dest


def test_filter_spaces_noarg():
    """Special test case for spaces without arguments (defaults to '_') """
    args = parser.parse_args(["-sp"])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(["file a", "file b"], filters, args.extension, args.raw)
    assert dest == ["file_a", "file_b"]


@pytest.mark.parametrize("c_arg, c_src, c_dest", [
    ("upper", ["file", "FILE1"], ["FILE", "FILE1"]),
    ("upper", ["file1"], ["FILE1"]),
    ("lower", ["FILE", "FILE2"], ["file", "file2"]),
    ("lower", ["FiLe", "FiLe2"], ["file", "file2"]),
    ("swap", ["FILE", "file"], ["file", "FILE"]),
    ("swap", ["fiLE1", "FIle2"], ["FIle1", "fiLE2"]),
    ("cap", ["FileName", "file name"], ["Filename", "File Name"]),
    ("cap", ["file1 1name", "file1_1name"], ["File1 1Name", "File1_1Name"]),
])
def test_filter_case(c_arg, c_src, c_dest):
    """Tests for case argument. Switch case depending on argument """
    args = parser.parse_args(["-c", c_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(c_src, filters, args.extension, args.raw)
    assert dest == c_dest


@pytest.mark.parametrize("tr_arg, tr_src, tr_dest", [
    (["a", "b"], ["filea"], ["fileb"]),
    (["fle", "tbi"], ["filea"], ["tibia"]),
    (["1", "2"], ["file1"], ["file2"])
])
def test_filter_translate(tr_arg, tr_src, tr_dest):
    """Tests for translate argument. Translate characters from one to another """
    args = parser.parse_args(["-tr", *tr_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(tr_src, filters, args.extension, args.raw)
    assert dest == tr_dest


@pytest.mark.parametrize("sl_arg, sl_src, sl_dest", [
    (":4", ["filea"], ["file"]),
    ("1:5", ["filea"], ["ilea"]),
    ("2:", ["filea"], ["lea"])
])
def test_filter_slice(sl_arg, sl_src, sl_dest):
    """Tests for slice argument. Slice portion of filename as the new name """
    args = parser.parse_args(["-sl", sl_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(sl_src, filters, args.extension, args.raw)
    assert dest == sl_dest


@pytest.mark.parametrize("sh_arg, sh_src, sh_dest", [
    (":1", ["filea"], ["file"]),
    ("1:", ["filea"], ["ilea"]),
    ("1:1", ["filea"], ["ile"])
])
def test_filter_shave(sh_arg, sh_src, sh_dest):
    """Tests for shave argument. Shave away portion of filename """
    args = parser.parse_args(["-sh", sh_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(sh_src, filters, args.extension, args.raw)
    assert dest == sh_dest


@pytest.mark.parametrize("bracr_arg, bracr_src, bracr_dest", [
    (["round "], ["filea"], ["filea"]),
    (["round"], ["(filea)file(file)", "(file)(file)(file)file"], ["file", "file"]),
    (["round", "0"], ["(file)(file)(file)file"], ["file"]),
    (["round", "1"], ["(file)file(file)"], ["file(file)"]),
    (["round", "2"], ["(file)file(file)"], ["(file)file"]),
    (["round", "3"], ["(file)file(file)"], ["(file)file(file)"]),
    (["square", "1"], ["[file]file[file]"], ["file[file]"]),
    (["square", "2"], ["[file]file[file]"], ["[file]file"]),
    (["square", "3"], ["[file]file[file]"], ["[file]file[file]"]),
    (["curly", "1"], ["{file}file{file}"], ["file{file}"]),
    (["curly", "2"], ["{file}file{file}"], ["{file}file"]),
    (["curly", "3"], ["{file}file{file}"], ["{file}file{file}"]),
])
def test_filter_bracr(bracr_arg, bracr_src, bracr_dest):
    """Tests for bracket remove argument. Remove specified bracket type """
    args = parser.parse_args(["-bracr", *bracr_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(bracr_src, filters, args.extension, args.raw)
    assert dest == bracr_dest


@pytest.mark.parametrize("bracr_arg, bracr_src", [
    ("round", ["((file))file"]),
    ("square", ["[[file]]file"]),
    ("curly", ["{{file}}file"])
])
def test_filter_bracr_extra(bracr_arg, bracr_src):
    """Extra test for bracket remove. Bracket remove can't handle nested brackets (yet!) """
    args = parser.parse_args(['-bracr', bracr_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(bracr_src, filters, args.extension, args.raw)
    for f in dest:
        assert f != "file"


@pytest.mark.parametrize("re_arg, re_src, re_dest", [
    (['f', 'p'], ["file"], ["pile"]),
    (["fi", "pa"], ["file"], ["pale"]),
    (["d"], ["fiddle"], ["file"]),
    (["d", "", "1"], ["diddily"], ["iddily"]),
    (["d", "l", "1"], ["fiddle"], ["fildle"]),
    (["d", "", "4"], ["diddily do"], ["diddily o"]),
    # replace 5th 'd', which doesn't exist, so do nothing
    (["d", "", "5"], ["diddily do"], ["diddily do"]),
    (["\\d+", "no.2"], ["02bla"], ["no.2bla"])
])
def test_filter_regex(re_arg, re_src, re_dest):
    """Tests for regex argument. Replace text using regular expressions """
    args = parser.parse_args(['-re', *re_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(re_src, filters, args.extension, args.raw)
    assert dest == re_dest


@pytest.mark.parametrize("seq_arg, seq_src, seq_dest", [
    (["%f"], ["f1", "f2", "f3", "f4"], ["f1", "f2", "f3", "f4"]),
    (["%n"], ["f1", "f2", "f3", "f4"], ["01", "02", "03", "04"]),
    (["%n1"], ["f1", "f2", "f3", "f4"], ["1", "2", "3", "4"]),
    (["%n2"], ["f1", "f2", "f3", "f4"], ["01", "02", "03", "04"]),
    (["%n3"], ["f1", "f2", "f3", "f4"], ["001", "002", "003", "004"]),
    (["%n:2:4"], ["f1", "f2", "f3", "f4"], ["02", "03", "04", "02"]),

    (["%n:::"], ["f1", "f2", "f3", "f4"], ["01", "02", "03", "04"]),
    (["%n:1::"], ["f1", "f2", "f3", "f4"], ["01", "02", "03", "04"]),
    (["%n:1"], ["f1", "f2", "f3", "f4"], ["01", "02", "03", "04"]),
    (["%n:1:2"], ["f1", "f2", "f3", "f4"], ["01", "02", "01", "02"]),
    (["%n:2::"], ["f1", "f2", "f3", "f4"], ["02", "03", "04", "05"]),
    (["%n:2"], ["f1", "f2", "f3", "f4"], ["02", "03", "04", "05"]),
    (["%n::2:"], ["f1", "f2", "f3", "f4"], ["01", "02", "01", "02"]),
    (["%n::2"], ["f1", "f2", "f3", "f4"], ["01", "02", "01", "02"]),
    (["%n::6:2"], ["f1", "f2", "f3", "f4"], ["01", "03", "05", "01"]),
    (["%n:1:6:2"], ["f1", "f2", "f3", "f4"], ["01", "03", "05", "01"]),

    (["%f/_/%n"], ["f1", "f2", "f3", "f4"], ["f1_01", "f2_02", "f3_03", "f4_04"]),
    (["%f/_/%n::2:"], ["f1", "f2", "f3", "f4"], ["f1_01", "f2_02", "f3_01", "f4_02"]),
    (["%f/_/%n:::2"], ["f1", "f2", "f3", "f4"], ["f1_01", "f2_03", "f3_05", "f4_07"]),

    (["%a"], ["f1", "f2", "f3", "f4"], ["a", "b", "c", "d"]),
    (["%a:b"], ["f1", "f2", "f3", "f4"], ["b", "c", "d", "e"]),
    (["%a:b:c"], ["f1", "f2", "f3", "f4"], ["b", "c", "b", "c"]),
    (["%a::b"], ["f1", "f2", "f3", "f4"], ["a", "b", "a", "b"]),
    (["%a2"], ["f1", "f2", "f3", "f4"], ["aa", "ab", "ac", "ad"]),
    (["%a2:a:b"], ["f1", "f2", "f3", "f4"], ["aa", "ab", "ba", "bb"])
])
def test_filter_sequence(seq_arg, seq_src, seq_dest):
    """Tests for sequence argument. Create a sequence of text for a file """
    args = parser.parse_args(['-seq', *seq_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(seq_src, filters, args.extension, args.raw)
    assert dest == seq_dest


@pytest.mark.parametrize("ext_arg, ext_src, ext_dest", [
    (["-pre", "test_", "-ext", ""], ["file.txt"], ["test_file"]),
    (["-pre", "test_", "-ext", "mp4"], ["file.txt"], ["test_file.mp4"]),
    (["-pre", "test_", "-ext", "gz"], ["file.tar.sav"], ["test_file.tar.gz"]),
    (["-post", "bla", "-ext", "gz"], ["file.tar.sav"], ["file.tarbla.gz"]),
])
def test_filter_extension(ext_arg, ext_src, ext_dest):
    """Tests for extension argument. Remove/replace extensions in file """
    args = parser.parse_args([*ext_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(ext_src, filters, args.extension, args.raw)
    assert dest == ext_dest


def test_filter_raw():
    pass


def test_renamer_files():
    pass


def test_renamer_cycle():
    pass
