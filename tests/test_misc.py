#!/usr/bin/env python3
import pytest

from batchren import renamer, bren

'''
tests for misc functions in renamer
Run this in the top level directory

tmpdir is a py.path.local object, more details here:
https://py.readthedocs.io/en/latest/path.html
'''
parser = bren.parser


@pytest.mark.parametrize("path_arg, path_res", [
    # tests for expanding directories
    ('sub/', 'sub/*'),
    ('sub', 'sub/*'),
    ('sub/ssub', 'sub/ssub/*'),
    # not a directory, don't change anything
    ('file.txt', 'file.txt')
])
def test_parser_expanddir(path_arg, path_res, tmpdir):
    # create directory structure
    tmpdir.mkdir('sub').mkdir('ssub')
    tmpdir.chdir()

    res = bren.expand_dir(path_arg)
    print(res)
    assert res == path_res


@pytest.mark.parametrize("partf_name, partf_res", [
    # split a path into its directory, basename and extension
    # take the last extension present
    #
    # filepath, (dirpath, file, ext)
    ("file", ("", "file", "")),
    ("file.mp4", ("", "file", ".mp4")),
    ("file.mp4.mp5", ("", "file.mp4", ".mp5")),
    ("parent/file.mp4.mp5", ("parent", "file.mp4", ".mp5")),
    ("dir/subdir/file", ("dir/subdir", "file", "")),
    ("dir/subdir/file.mp4", ("dir/subdir", "file", ".mp4")),
    ("parent/subdir/file.mp4.mp5", ("parent/subdir", "file.mp4", ".mp5"))
])
def test_partfile_param(partf_name, partf_res):
    res = renamer.partfile(partf_name)
    print(res)
    assert res == partf_res


@pytest.mark.parametrize("joinf_name, joinf_res", [
    # combine dirpath, basename and extension and
    # return filename with new full path
    # dirpath is the directory part of a file
    # basename is the basename of the file
    # extension is the extension type of the file
    # filename is the combined basename with extension
    # path is the full path of the renamed file
    #
    # filename is the same as path when there is no parent
    # basename has whitespace removed from both ends and '._- ' from the right end
    # ext has whitespace removed, dots collapsed and dots on both ends removed
    #
    # (dirpath, basename, ext), (filename, path)
    (("", "file", ""), ("file", "file")),
    (("", "file_", ""), ("file", "file")),
    (("", "file-", ""), ("file", "file")),
    (("", "file.", ""), ("file", "file")),
    (("", "file -_-. ", ""), ("file", "file")),
    (("", "file", ".txt"), ("file.txt", "file.txt")),
    (("", "   file    ", ".txt"), ("file.txt", "file.txt")),
    (("parent", "file", ".txt"), ("file.txt", "parent/file.txt")),
    (("/parent", "file", ".txt.sav"), ("file.txt.sav", "/parent/file.txt.sav")),
    (("parent", "file", "...  e  xt?. ext.  .ext?.."), ("file.ext?.ext.ext?", "parent/file.ext?.ext.ext?"))
])
def test_joinpart_param(joinf_name, joinf_res):
    res = renamer.joinpart(*joinf_name)
    print(res)
    assert res == joinf_res
