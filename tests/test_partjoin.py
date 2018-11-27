#!/usr/bin/env python3
import pytest

from batchren import renamer

'''
tests for splitting/joining file parts
'''

@pytest.mark.parametrize("partfname, partfres", [
    # filepath, (dirpath, file, ext)
    ("file", ("", "file", "")),
    ("file.mp4", ("", "file", ".mp4")),
    ("file.mp4.mp5", ("", "file.mp4", ".mp5")),
    ("parent/something", ("parent", "something", "")),
    ("parent/file.mp4", ("parent", "file", ".mp4")),
    ("parent/file.mp4.mp5", ("parent", "file.mp4", ".mp5")),
    ("parent/subdir/file.mp4.mp5", ("parent/subdir", "file.mp4", ".mp5"))
])
def test_partfile_param(partfname, partfres):
    res = renamer.partfile(partfname)
    print(res)
    assert res == partfres


@pytest.mark.parametrize("joinfname, joinfres", [
    # (dirpath, file, ext), (fullname fullpath)
    (("", "file", ""), ("file", "file")),
    (("parent", "file", "mp4"), ("file.mp4", "parent/file.mp4")),
    (("/parent", "file", "mp4.sav"), ("file.mp4.sav", "/parent/file.mp4.sav")),
    (("parent", "file", "...ext?.ext..ext?.."), ("file.ext?.ext.ext?", "parent/file.ext?.ext.ext?"))
])
def test_joinpart_param(joinfname, joinfres):
    res = renamer.joinpart(*joinfname)
    print(res)
    assert res == joinfres