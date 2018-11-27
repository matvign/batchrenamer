#!/usr/bin/env python3
import pytest

from batchren import renamer

'''
tests for splitting/joining file parts
'''


@pytest.mark.parametrize("partf_name, partf_res", [
    # filepath, (dirpath, file, ext)
    # when there is more than one extension, take the last extension
    # the rest is treated as filename
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
    # (dirpath, file, ext), (fullname fullpath)
    # when there is no parent, fullname is just the filename
    # when parent is present, join parts together
    # for extensions, remove whitespace and collapse adjacent dots
    (("", "file", ""), ("file", "file")),
    (("parent", "file", "mp4"), ("file.mp4", "parent/file.mp4")),
    (("/parent", "file", "mp4.sav"), ("file.mp4.sav", "/parent/file.mp4.sav")),
    (("parent", "file", "...  e  xt?. ext.  .ext?.."), ("file.ext?.ext.ext?", "parent/file.ext?.ext.ext?"))
])
def test_joinpart_param(joinf_name, joinf_res):
    res = renamer.joinpart(*joinf_name)
    print(res)
    assert res == joinf_res