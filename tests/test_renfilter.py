import pytest

from batchren import bren, renamer, _version

'''
tests for filters of names
Run this in the top level directory
'''
parser = bren.parser


def test_parser_version():
    assert _version.__version__ == '0.6.0'


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
    ('', '', 'file a', 'filea'),
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
    # special test case for no arguments
    # sets spaces to _
    args = parser.parse_args(['-sp'])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, '', 'file a')
    print('oldname: {} --> newname: {}'.format('file a', newname))
    assert newname == 'file_a'


@pytest.mark.parametrize("c_errarg", [
    # tests for case filter
    (['-v']),
    (['bla', '-v']),
    (['garbage', '-v']),
    (['bug', '-v']),
    (['1', '-v']),
    (['1', '2', '-v'])
])
def test_filter_case_err(c_errarg):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-c', *c_errarg])
        print(c_errarg, "is erroneous")
        assert err.type == SystemExit


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
    ('cap', '', 'file1_1name', 'File1_1Name'),
    ('cap', '', 'file1.1name', 'File1.1Name'),
    ('upper  ', '', 'file', 'FILE'),
    ('lower  ', '', 'FILE', 'file'),
    ('swap   ', '', 'fIle', 'FiLE')
])
def test_filter_cases(c_arg, c_dirpath, c_fname, c_res):
    args = parser.parse_args(['-c', c_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, c_dirpath, c_fname)
    print('oldname: {} --> newname: {}'.format(c_fname, newname))
    assert newname == c_res


@pytest.mark.parametrize("tr_errargs", [
    # errors for translate parser
    # let nargs=2 handle length of arguments
    # translate expects two arguments, both same length
    (['-v']),
    (['a']),
    (['a', '-v']),
    # (['a', 'b', 'c', '-v']),  # let argparse deal with this error
    (['a', 'bc', '-v'])
])
def test_filter_translate_err(tr_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-tr', *tr_errargs])
        print(tr_errargs, "is erroneous")
        assert err.type == SystemExit


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


@pytest.mark.parametrize("sl_errargs", [
    # errors for slice parser
    (['-v']),
    (['a', 'b', '-v']),
    (['a', 'b', 'c', '-v']),
    (['1:2:3:4', '-v']),
    (['1:2:3:4:', '-v']),
    (['a:', '-v']),
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


@pytest.mark.parametrize("sh_errargs", [
    # errors for shave parser
    (['-v']),
    (['1a', '-v']),
    (['a', '-v']),
    (['a:', '-v']),
    (['a:b', '-v']),
    ([':b', '-v']),
    (['a:b:c', '-v']),
    (['1:2:3', '-v']),
    (['1:a', '-v']),
    (['1:-1', '-v']),
    (['-1:1', '-v']),
    (['-1:', '-v']),
    ([':-1', '-v'])
])
def test_filter_shave_err(sh_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-sh', *sh_errargs])
        print(sh_errargs, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("sh_arg, sh_dirpath, sh_fname, sh_res", [
    # tests for shave filter
    # dirpath is only used in sequence filter
    # arg, dirpath, filename, expected result
    (':1', '', 'filea', 'file'),
    ('1:', '', 'filea', 'ilea'),
    ('1:1', '', 'filea', 'ile')
])
def test_filter_shave(sh_arg, sh_dirpath, sh_fname, sh_res):
    args = parser.parse_args(['-sh', sh_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, sh_dirpath, sh_fname)
    print('oldname: {} --> newname: {}'.format(sh_fname, newname))
    assert newname == sh_res


@pytest.mark.parametrize("bracr_errargs", [
    (['-v']),
    (['something', '-v']),
    (['roun', '-v']),
    (['CURLY', '-v']),
    (['ROUND', '-v']),
    (['SQUARE', '-v']),
    (['SOMETHING', 'HERE', '-v']),
    (['10', '-v'])
])
def test_filter_bracr_err(bracr_errargs):
    with pytest.raises(SystemExit) as err:
        args = parser.parse_args(['-bracr', *bracr_errargs])
        print(bracr_errargs, "is erroneous")
        assert err.type == SystemExit


@pytest.mark.parametrize("bracr_arg, bracr_dirpath, bracr_fname, bracr_res", [
    # tests for bracket removal
    (['round'], '', '(filea)file(file)', 'file'),
    (['round'], '', 'filea', 'filea'),
    (['round '], '', 'filea', 'filea'),
    (['round'], '', '(file)(file)(file)file', 'file'),
    (['round', '1'], '', '(file)file(file)', 'file(file)'),
    (['  round  ', ' 1 '], '', '(file)file(file)', 'file(file)'),
    (['round', '2'], '', '(file)file(file)', '(file)file'),
    (['round', '3'], '', '(file)file(file)', '(file)file(file)'),
    (['square', '1'], '', '[file]file[file]', 'file[file]'),
    (['square', '2'], '', '[file]file[file]', '[file]file'),
    (['square', '3'], '', '[file]file[file]', '[file]file[file]'),
    (['curly', '1'], '', '{file}file{file}', 'file{file}'),
    (['curly', '2'], '', '{file}file{file}', '{file}file'),
    (['curly', '3'], '', '{file}file{file}', '{file}file{file}'),
])
def test_filter_bracr(bracr_arg, bracr_dirpath, bracr_fname, bracr_res):
    args = parser.parse_args(['-bracr', *bracr_arg])
    filters = renamer.initfilters(args)
    newname = renamer.runfilters(filters, bracr_dirpath, bracr_fname)
    print('oldname: {} --> newname: {}'.format(bracr_fname, newname))
    print('expected:', bracr_res)
    assert newname == bracr_res
