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


"""
@pytest.mark.parametrize("bracr_rec_arg, bracr_type", [
    ('((file))file', 'round'),
    ('[[file]]file', 'square'),
    ('{{file}}file', 'curly')
])
def test_filter_bracr_extra(bracr_rec_arg, bracr_type):
    args = parser.parse_args(['-bracr', bracr_type])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, '', '', bracr_rec_arg)
    assert newname != 'file'


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
"""
