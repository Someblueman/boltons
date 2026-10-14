import re
from collections import namedtuple

import pytest

from boltons.formatutils import (get_format_args,
                                 split_format_str,
                                 tokenize_format_str,
                                 infer_positional_format_args,
                                 DeferredValue as DV)


PFAT = namedtuple("PositionalFormatArgTest", "fstr arg_vals res")

_PFATS = [PFAT('{} {} {}', ('hi', 'hello', 'bye'), "hi hello bye"),
          PFAT('{:d} {}', (1, 2), "1 2"),
          PFAT('{!s} {!r}', ('str', 'repr'), "str 'repr'"),
          PFAT('{[hi]}, {.__name__!r}', ({'hi': 'hi'}, re), "hi, 're'"),
          PFAT('{{joek}} ({} {})', ('so', 'funny'), "{joek} (so funny)")]


def test_pos_infer():
    for i, (tmpl, args, res) in enumerate(_PFATS):
        converted = infer_positional_format_args(tmpl)
        assert converted.format(*args) == res


@pytest.mark.parametrize('template, expected, args, kwargs', [
    ('{[{}]} {}', '{0[{}]} {1}', ({'{}': 'value'}, 'tail'), {}),
    ('{data[{}]} {}', '{data[{}]} {0}', ('tail',),
     {'data': {'{}': 'value'}}),
    ('{0[{}]} {1}', '{0[{}]} {1}', ({'{}': 'value'}, 'tail'), {}),
    ('[{[{:}]}] {:>{}}', '[{0[{:}]}] {1:>{2}}',
     ({'{:}': 'value'}, 'end', 5), {}),
    ('{[first][{!r}]} {!s}', '{0[first][{!r}]} {1!s}',
     ({'first': {'{!r}': 'value'}}, 'tail'), {}),
    ('{{{[{}]}}}', '{{{0[{}]}}}', ({'{}': 'value'},), {}),
    ('[{}] {{[{}]}} {:>{}}', '[{0}] {{[{1}]}} {2:>{3}}',
     ('first', 'second', 'end', 5), {}),
])
def test_pos_infer_item_braces(template, expected, args, kwargs):
    converted = infer_positional_format_args(template)
    assert converted == expected
    assert converted.format(*args, **kwargs) == template.format(*args, **kwargs)


def test_tokenize_item_braces():
    field, literal, following = tokenize_format_str('{[{}]} {}')
    assert field.fname == '0[{}]'
    assert field.fstr == '{0[{}]}'
    assert literal == ' '
    assert following.fname == '1'


_TEST_TMPLS = ["example 1: {hello}",
               "example 2: {hello:*10}",
               "example 3: {hello:*{width}}",
               "example 4: {hello!r:{fchar}{width}}, {width}, yes",
               "example 5: {0}, {1:d}, {2:f}, {1}",
               "example 6: {}, {}, {}, {1}"]


def test_get_fstr_args():
    results = []
    for t in _TEST_TMPLS:
        inferred_t = infer_positional_format_args(t)
        res = get_format_args(inferred_t)
        assert res


def test_split_fstr():
    results = []
    for t in _TEST_TMPLS:
        res = split_format_str(t)
        results.append(res)
        assert res


def test_tokenize_format_str():
    results = []
    for t in _TEST_TMPLS:
        res = tokenize_format_str(t)
        results.append(res)
        assert res


def test_deferredvalue():
    def myfunc():
        myfunc.called += 1
        return 123

    myfunc.called = 0

    dv = DV(myfunc)
    assert str(dv) == '123'
    assert myfunc.called == 1
    assert str(dv) == '123'
    assert myfunc.called == 1
    dv.cache_value = False
    assert str(dv) == '123'
    assert myfunc.called == 2
    assert str(dv) == '123'
    assert myfunc.called == 3
