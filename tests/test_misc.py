#!/usr/bin/env python3
import pytest

from batchren import renamer, bren

'''
tests for misc functions that do certain things.
Run this in the top level directory
'''
parser = bren.parser


@pytest.fixture(scope="session")
@pytest.mark.parametrize("path_args, path_res", [
    # tests for expanding directories
    (['testdir', '-v'], 'testdir/*'),
    (['testdir/', '-v'], 'testdir/*'),
    (['testdir/sub', '-v'], 'testdir/sub/*'),
    (['testdir/sub/', '-v'], 'testdir/sub/*')
])
def test_parser_expanddir(path_args, path_res, tmpdir):
    p = tmpdir.mkdir('testdir').sub('sub')
    args = parser.parse_args(path_args)
    print(args)
    assert args.path == path_res


@pytest.mark.parametrize("partf_name, partf_res", [
    # always take the last extension, the rest is the filename
    # filepath, (dirpath, file, ext)
    ("file", ("", "file", "")),
    ("file.mp4", ("", "file", ".mp4")),
    ("file.mp4.mp5", ("", "file.mp4", ".mp5")),
    ("parent/something", ("parent", "something", "")),
    ("parent/file.mp4", ("parent", "file", ".mp4")),
    ("parent/file.mp4.mp5", ("parent", "file.mp4", ".mp5")),
    ("parent/subdir/file.mp4.mp5", ("parent/subdir", "file.mp4", ".mp5"))
])
def test_partfile_param(partf_name, partf_res):
    res = renamer.partfile(partf_name)
    print(res)
    assert res == partf_res


@pytest.mark.parametrize("joinf_name, joinf_res", [
    # dirpath is the parent part of a file
    # bname is the basename of the file w/o extension
    # ext is the extension of the file
    # fname is the filename, which is bname combined with ext
    # newname is dirpath combined with fname
    #
    # when there is no parent, newname is the same as fname
    # bname has left whitespace and '._- ' characters removed on the right
    # ext has whitespace removed, dots collapsed and dots on left/right removed
    #
    # (dirpath, bname, ext), (fname, newname)
    (("", "file", ""), ("file", "file")),
    (("", "file_", ""), ("file", "file")),
    (("", "file-", ""), ("file", "file")),
    (("", "file.", ""), ("file", "file")),
    (("", "   file    ", ""), ("file", "file")),
    (("parent", "file", "mp4"), ("file.mp4", "parent/file.mp4")),
    (("/parent", "file", "mp4.sav"), ("file.mp4.sav", "/parent/file.mp4.sav")),
    (("parent", "file", "...  e  xt?. ext.  .ext?.."), ("file.ext?.ext.ext?", "parent/file.ext?.ext.ext?"))
])
def test_joinpart_param(joinf_name, joinf_res):
    res = renamer.joinpart(*joinf_name)
    print(res)
    assert res == joinf_res
