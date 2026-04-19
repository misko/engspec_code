import pytest
from json_pointer import (
    resolve,
    PointerError,
    PointerSyntaxError,
    KeyNotFound,
    IndexOutOfBounds,
    TypeMismatch,
)


@pytest.fixture
def rfc_doc():
    return {
        "foo": ["bar", "baz"],
        "": 0,
        "a/b": 1,
        "c%d": 2,
        "e^f": 3,
        "g|h": 4,
        "i\\j": 5,
        "k\"l": 6,
        " ": 7,
        "m~n": 8,
    }


def test_empty_pointer_returns_document(rfc_doc):
    assert resolve(rfc_doc, "") is rfc_doc


def test_foo_returns_list(rfc_doc):
    assert resolve(rfc_doc, "/foo") == ["bar", "baz"]


def test_foo_0_returns_bar(rfc_doc):
    assert resolve(rfc_doc, "/foo/0") == "bar"


def test_slash_returns_value_at_empty_key(rfc_doc):
    assert resolve(rfc_doc, "/") == 0


def test_escape_tilde_one_to_slash(rfc_doc):
    assert resolve(rfc_doc, "/a~1b") == 1


def test_percent_in_key(rfc_doc):
    assert resolve(rfc_doc, "/c%d") == 2


def test_caret_in_key(rfc_doc):
    assert resolve(rfc_doc, "/e^f") == 3


def test_pipe_in_key(rfc_doc):
    assert resolve(rfc_doc, "/g|h") == 4


def test_backslash_in_key(rfc_doc):
    assert resolve(rfc_doc, "/i\\j") == 5


def test_doublequote_in_key(rfc_doc):
    assert resolve(rfc_doc, "/k\"l") == 6


def test_space_key(rfc_doc):
    assert resolve(rfc_doc, "/ ") == 7


def test_escape_tilde_zero_to_tilde(rfc_doc):
    assert resolve(rfc_doc, "/m~0n") == 8


def test_escape_order_tilde_one_first():
    assert resolve({"~1": "kept-as-tilde-one"}, "/~01") == "kept-as-tilde-one"


def test_escape_order_slash_key():
    assert resolve({"/": "slash-key"}, "/~1") == "slash-key"


def test_syntax_error_no_leading_slash():
    with pytest.raises(PointerSyntaxError):
        resolve({"foo": 1}, "foo")


def test_syntax_error_trailing_tilde():
    with pytest.raises(PointerSyntaxError):
        resolve({"a~": 1}, "/a~")


def test_syntax_error_bad_escape():
    with pytest.raises(PointerSyntaxError):
        resolve({"a~b": 1}, "/a~b")


def test_syntax_error_leading_zero_index():
    with pytest.raises(PointerSyntaxError):
        resolve({"a": [1, 2]}, "/a/01")


def test_syntax_error_negative_index():
    with pytest.raises(PointerSyntaxError):
        resolve({"a": [1, 2]}, "/a/-1")


def test_key_not_found():
    with pytest.raises(KeyNotFound):
        resolve({"a": 1}, "/b")


def test_index_out_of_bounds():
    with pytest.raises(IndexOutOfBounds):
        resolve({"a": [1, 2]}, "/a/2")


def test_dash_index_rejected():
    with pytest.raises(IndexOutOfBounds):
        resolve({"a": [1, 2]}, "/a/-")


def test_type_mismatch_scalar():
    with pytest.raises(TypeMismatch):
        resolve({"a": 1}, "/a/x")


def test_resolve_none_with_empty_pointer():
    assert resolve(None, "") is None


def test_pointer_error_is_base_class():
    with pytest.raises(PointerError):
        resolve({"a": 1}, "/b")

    with pytest.raises(PointerError):
        resolve({"a": 1}, "foo")

    with pytest.raises(PointerError):
        resolve({"a": [1, 2]}, "/a/5")

    with pytest.raises(PointerError):
        resolve({"a": 1}, "/a/x")
