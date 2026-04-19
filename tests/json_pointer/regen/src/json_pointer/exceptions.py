class PointerError(Exception):
    """Base class for all errors raised by json_pointer.resolve."""


class PointerSyntaxError(PointerError, ValueError):
    """Raised when a pointer string is not well-formed per RFC 6901."""


class KeyNotFound(PointerError, KeyError):
    """Raised when a reference token names a key not present in a dict."""


class IndexOutOfBounds(PointerError, IndexError):
    """Raised when a list index is >= len(list), or when the '-' token is
    encountered (which refers to a nonexistent one-past-end element per
    RFC 6901 §4)."""


class TypeMismatch(PointerError, TypeError):
    """Raised when a reference token is applied to a non-container value."""
