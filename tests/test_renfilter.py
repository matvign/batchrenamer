import pytest

from main import parser
from batchren import renamer

'''
tests for filters of names
'''


@pytest.mark.parametrize("pre_arg, pre_dirpath, pre_fname, pre_res", [
    # tests for prepend filter
    # dirpath is only used in sequence filter
    # arg, dirpath, filename, expected result
    ('PRE_', '', 'file', 'PRE_file'),
    ('PRE_', 'parent', 'file', 'PRE_file'),
    ('PRE_', '', 'file.mp4', 'PRE_file.mp4')
])
def test_filter_prepend(pre_arg, pre_dirpath, pre_fname, pre_res):
    args = parser.parse_args(['-pre', pre_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, pre_dirpath, pre_fname)
    print('oldname: {} --> newname: {}'.format(pre_fname, newname))
    assert newname == pre_res


@pytest.mark.parametrize("post_arg, post_dirpath, post_fname, post_res", [
    # tests for postpend filter
    # dirpath is only used in sequence filter
    # postpend to fname even when extension is present
    # arg, dirpath, filename, expected result
    ('_POST', '', 'file', 'file_POST'),
    ('_POST', 'parent', 'file', 'file_POST'),
    ('_POST', '', 'file.mp4', 'file.mp4_POST')
])
def test_filter_postpend(post_arg, post_dirpath, post_fname, post_res):
    args = parser.parse_args(['-post', post_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, post_dirpath, post_fname)
    print('oldname: {} --> newname: {}'.format(post_fname, newname))
    assert newname == post_res


@pytest.mark.parametrize("sp_arg, sp_dirpath, sp_fname, sp_res", [
    # tests for space filter
    # dirpath is only used in sequence filter
    # arg, dirpath, filename, expected result
    ('_', '', 'file a', 'file_a'),
    ('.', '', 'file b', 'file.b'),
    ('THIS', '', 'file c', 'fileTHISc'),
    ('.', '', 'f i l e', 'f.i.l.e')
])
def test_filter_spaces(sp_arg, sp_dirpath, sp_fname, sp_res):
    args = parser.parse_args(['-sp', sp_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, sp_dirpath, sp_fname)
    print('oldname: {} --> newname: {}'.format(sp_fname, newname))
    assert newname == sp_res


def test_filter_spaces_extra():
    # special test case where there is a missing argument for spaces, defaults to _
    args = parser.parse_args(['-sp'])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, '', 'file a')
    print('oldname: {} --> newname: {}'.format('file a', newname))
    assert newname == 'file_a'


@pytest.mark.parametrize("c_arg, c_dirpath, c_fname, c_res", [
    # tests for case filter
    # dirpath is only used in sequence filter
    # arg, dirpath, filename, expected result
    ('upper', '', 'file', 'FILE'),
    ('upper', '', 'file1', 'FILE1'),
    ('lower', '', 'FILE', 'file'),
    ('lower', '', 'FILE1', 'file1'),
    ('swap', '', 'fIle', 'FiLE'),
    ('swap', '', 'fIle1', 'FiLE1'),
    ('cap', '', 'file name', 'File Name'),
    ('cap', '', 'file1 1name', 'File1 1Name'),
    ('cap', '', 'file1_1name', 'File1_1Name')
])
def test_filter_cases(c_arg, c_dirpath, c_fname, c_res):
    args = parser.parse_args(['-c', c_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, c_dirpath, c_fname)
    print('oldname: {} --> newname: {}'.format(c_fname, newname))
    assert newname == c_res


@pytest.mark.parametrize("tr_arg, tr_dirpath, tr_fname, tr_res", [
    # tests for translate filter
    # dirpath is only used in sequence filter
    # arg, dirpath, filename, expected result
    (['a', 'b'], '', 'filea', 'fileb'),
    (['fle', 'tbi'], '', 'filea', 'tibia'),
    (['1', '2'], '', 'file1', 'file2')
])
def test_filter_translate(tr_arg, tr_dirpath, tr_fname, tr_res):
    args = parser.parse_args(['-tr', *tr_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, tr_dirpath, tr_fname)
    print('oldname: {} --> newname: {}'.format(tr_fname, newname))
    assert newname == tr_res


@pytest.mark.parametrize("sl_arg, sl_dirpath, sl_fname, sl_res", [
    # tests for slice filter
    # dirpath is only used in sequence filter
    # arg, dirpath, filename, expected result
    (':4', '', 'filea', 'file'),
    ('1:5', '', 'filea', 'ilea')
])
def test_filter_slice(sl_arg, sl_dirpath, sl_fname, sl_res):
    args = parser.parse_args(['-sl', sl_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, sl_dirpath, sl_fname)
    print('oldname: {} --> newname: {}'.format(sl_fname, newname))
    assert newname == sl_res