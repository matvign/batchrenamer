#!/usr/bin/env python3
import os

import pytest

from batchren import bren, renamer
from tests.data import file_dirs
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
    (["dir", "  file", ".txt", True], ("dir/  file.txt"))
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
    (["f", "p"], ["file"], ["pile"]),
    (["fi", "pa"], ["file"], ["pale"]),
    (["d"], ["fiddle"], ["file"]),
    (["d", "", "1"], ["diddily"], ["iddily"]),
    (["d", "l", "1"], ["fiddle"], ["fildle"]),
    (["d", "", "4"], ["diddily do"], ["diddily o"]),
    # replace non-existent 5th 'd', do nothing
    (["d", "", "5"], ["diddily do"], ["diddily do"]),
    (["\\d+", "no.2"], ["02bla"], ["no.2bla"]),
    # add more regex tests...
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
    (["%a::c"], ["f1", "f2", "f3", "f4"], ["a", "b", "c", "a"]),
    (["%a:a:c"], ["f1", "f2", "f3", "f4"], ["a", "b", "c", "a"]),
    (["%a:a:bb"], ["f1", "f2", "f3", "f4"], ["aa", "ab", "ba", "bb"]),
    (["%a:aa:b"], ["f1", "f2", "f3", "f4"], ["aa", "ba", "aa", "ba"]),

    (["%a2"], ["f1", "f2", "f3", "f4"], ["aa", "ab", "ac", "ad"]),
    (["%a2:a:b"], ["f1", "f2", "f3", "f4"], ["aa", "ab", "ba", "bb"]),
    (["%a2::bb"], ["f1", "f2", "f3", "f4"], ["aaaa", "aaab", "aaba", "aabb"]),

    (["%a:B"], ["f1", "f2", "f3", "f4"], ["B", "C", "D", "E"]),
    (["%a:A:C"], ["f1", "f2", "f3", "f4"], ["A", "B", "C", "A"]),
    (["%a:y:B"], ["f1", "f2", "f3", "f4"], ["y", "z", "A", "B"]),
    (["%a:B:z"], ["f1", "f2", "f3", "f4"], ["B", "B", "B", "B"]),
])
def test_filter_sequence(seq_arg, seq_src, seq_dest):
    """Tests for sequence argument. Create a sequence of text for a file """
    args = parser.parse_args(['-seq', *seq_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(seq_src, filters, args.extension, args.raw)
    assert dest == seq_dest


@pytest.mark.parametrize("ext_arg, ext_src, ext_dest", [
    (["-pre", "f", "-ext", ""], ["file.txt"], ["ffile"]),
    (["-pre", "f", "-ext", "mp4"], ["file.txt"], ["ffile.mp4"]),
    (["-pre", "f", "-ext", ".mp4"], ["file.txt"], ["ffile.mp4"]),
    (["-pre", "f", "-ext", ".mp4 "], ["file.txt"], ["ffile.mp4"]),
    (["-pre", "f", "-ext", ".mp4 ."], ["file.txt"], ["ffile.mp4"]),
    (["-pre", "f", "-ext", "...mp4."], ["file.txt"], ["ffile.mp4"]),
    (["-pre", "f", "-ext", "gz"], ["file.tar.sav"], ["ffile.tar.gz"]),
    (["-pre", "f", "-ext", ".gz"], ["file.tar.sav"], ["ffile.tar.gz"]),
    (["-post", "bla", "-ext", "gz"], ["file.tar.sav"], ["file.tarbla.gz"]),
])
def test_filter_extension(ext_arg, ext_src, ext_dest):
    """Tests for extension argument. Remove/replace extensions in file """
    args = parser.parse_args([*ext_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(ext_src, filters, args.extension, args.raw)
    assert dest == ext_dest


@pytest.mark.parametrize("raw_arg, raw_src, raw_dest", [
    (["-ext", "txt", "--raw"], ["files", "files.txt"], ["files.txt", "files.txt.txt"]),
    (["-post", "bla", "--raw"], ["files.txt"], ["files.txtbla"]),
    (["-post", "bla", "-ext", ".txt", "--raw"], ["files.txt"], ["files.txtbla.txt"])
])
def test_filter_raw(raw_arg, raw_src, raw_dest):
    """Tests for raw argument. Treat extensions as part of filename """
    args = parser.parse_args([*raw_arg])
    filters = renamer.initfilters(args)
    dest = renamer.get_renames(raw_src, filters, args.extension, args.raw)
    assert dest == raw_dest


@pytest.fixture
def fs(tmp_path_factory):
    """Fixture for fixed tmp_path_factory """
    dir_ = tmp_path_factory.mktemp("")
    for key, val in file_dirs.fs1.items():
        d_ = dir_ / key
        d_.mkdir()
        for v in val:
            f = d_ / v
            f.write_text(v)

    return dir_


@pytest.mark.parametrize("src, dest", [
    (["dir/filea", "dir/fileb"], ["dir/filee", "dir/filef"]),
    (["dir/filea", "dir/fileb"], ["dir/fileb", "dir/filea"]),
    (["dir/filea", "dir/fileb", "dir/filec"], ["dir/fileb", "dir/filec", "dir/filea"]),
    (["dir/filea", "dir/fileb", "dir/filec"], ["dir/fileb", "dir/filec", "dir/filee"])
])
def test_rentable_valid(fs, src, dest):
    """Test that the rename table will resolve the following:\n
    -   No conflict rename
    -   Sequence of resolvable conflicts
    """
    os.chdir(fs)
    table = renamer.generate_rentable(src, dest)
    print(table)
    assert not table["conflicts"]
    assert not table["unresolvable"]
    assert len(table["renames"]) == len(src)


@pytest.mark.parametrize("src, dest", [
    pytest.param(["dir/filea", "dir/fileb"], ["dir/filea"], marks=pytest.mark.xfail),
    # name is unchanged
    (["dir/filea"], ["dir/filea"]),
    (["dir/filea"], ["dir//filea"]),
    # name cannot be empty
    (["dir/filea"], [""]),
    # name cannot start with '.'
    (["dir/filea"], ["dir/.filea"]),
    (["dir/filea"], ["dir/."]),
    (["dir/filea"], ["dir/.."]),
    (["dir/filea"], ["dir/.other"]),
    (["dir/filea"], ["dir/..other"]),
    # name cannot exceed 255 characters
    (["dir/filea"], ["dir/" + "a" * 256]),
    # cannot change file to directory + empty name
    (["dir/filea"], ["dir/filea/"]),
    # cannot change location of file
    (["dir/filea"], ["dir/fil/a"]),
    # shared name conflict
    (["dir/filea"], ["dir/fileb"]),
])
def test_rentable_invalid(fs, src, dest):
    """Test that the rename table will not resolve the following:\n
    -   name is unchanged
    -   name cannot be empty
    -   name cannot start with '.'
    -   name cannot exceed 255 characters
    -   cannot change file to directory
    -   cannot change location of file
    -   shared name conflict
    """
    os.chdir(fs)
    table = renamer.generate_rentable(src, dest)
    print(table["conflicts"])
    print(table["unresolvable"])
    assert table["conflicts"]
    assert table["unresolvable"]
    assert not table["renames"]


@pytest.fixture
def param_fs(tmp_path_factory, request):
    """Parametrized tmp_path_factory fixture """
    dir_ = tmp_path_factory.mktemp("")
    for key, val in request.param.items():
        d_ = dir_ / key
        d_.mkdir()
        for v in val:
            f = d_ / v
            print(os.path.join(key, v))
            f.write_text(os.path.join(key, v))

    return dir_


@pytest.mark.parametrize("param_fs, src, dest", [
    (file_dirs.fs1, ["dir/filea"], ["dir/filez"]),
    (file_dirs.fs1, ["dir/fileb"], ["dir/filez"]),
    (file_dirs.fs2, ["dir1/01", "dir1/02", "dir1/03"],
        ["dir1/02", "dir1/03", "dir1/01"])],
    indirect=["param_fs"]
)
def test_renamer_files(monkeypatch, param_fs, src, dest):
    """Test that files are renamed as expected """
    monkeypatch.setattr("builtins.input", lambda: "Y")
    os.chdir(param_fs)
    table = renamer.generate_rentable(src, dest)
    queue = renamer.print_rentable(table)
    renamer.rename_queue(queue)
    for s, d in zip(src, dest):
        f = param_fs / d
        assert f.read_text() == s


@pytest.mark.parametrize("param_fs, src, dest", [
    (file_dirs.fs1, ["dir/filea"], ["dir/filez"]),
    (file_dirs.fs1, ["dir/fileb"], ["dir/filez"])],
    indirect=["param_fs"]
)
def test_renamer_dryrun(monkeypatch, param_fs, src, dest):
    """Test that there is no change in files """
    monkeypatch.setattr("builtins.input", lambda: "Y")
    os.chdir(param_fs)
    table = renamer.generate_rentable(src, dest)
    queue = renamer.print_rentable(table)
    renamer.rename_queue(queue, dryrun=True)
    for s, d in zip(src, dest):
        f = param_fs / s
        assert f.read_text() == s


@pytest.mark.parametrize("param_fs, queue", [
    (file_dirs.fs1, [("dir/filea", "dir/filex"), ("dir/fileb", "dir/filey"), ("dir/filec", 10)]),
    (file_dirs.fs1, [("dir/filea", "dir/fileb"), ("dir/fileb", "dir/filey"), ("dir/filec", 10)])
], indirect=["param_fs"])
def test_renamer_rollback(param_fs, queue):
    os.chdir(param_fs)
    with pytest.raises(BaseException):
        renamer.rename_queue(queue)
        for src in file_dirs.fs1["dir"]:
            f = param_fs / src
            assert f.read_text() == src
    # assert False
