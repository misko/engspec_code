import re

from .exceptions import (
    PointerSyntaxError,
    KeyNotFound,
    IndexOutOfBounds,
    TypeMismatch,
)

_INDEX_RE = re.compile(r"^(0|[1-9][0-9]*)$")


def _validate_escapes(token: str) -> str:
    i = 0
    while i < len(token):
        if token[i] == "~":
            if i + 1 >= len(token) or token[i + 1] not in ("0", "1"):
                raise PointerSyntaxError(
                    f"bad escape in token {token!r}: '~' must be followed by '0' or '1'"
                )
            i += 2
        else:
            i += 1
    return token


def _unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _parse(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise PointerSyntaxError(
            f"pointer must start with '/' or be empty, got {pointer!r}"
        )
    raw_tokens = pointer[1:].split("/")
    return [_unescape(_validate_escapes(t)) for t in raw_tokens]


def _resolve_token(value, token: str):
    if isinstance(value, dict):
        if token in value:
            return value[token]
        raise KeyNotFound(f"key {token!r} not in dict")
    if isinstance(value, list):
        if token == "-":
            raise IndexOutOfBounds(
                "token '-' refers to the one-past-end element; not valid for read"
            )
        if not _INDEX_RE.fullmatch(token):
            raise PointerSyntaxError(
                f"invalid array index {token!r}: must be '0' or [1-9][0-9]*"
            )
        index = int(token)
        if index >= len(value):
            raise IndexOutOfBounds(
                f"index {index} out of bounds for list of length {len(value)}"
            )
        return value[index]
    raise TypeMismatch(
        f"cannot descend into {type(value).__name__} value with token {token!r}"
    )


def resolve(document, pointer: str):
    if pointer == "":
        return document
    current = document
    for token in _parse(pointer):
        current = _resolve_token(current, token)
    return current
