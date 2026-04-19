# RFC 6901 §5 Test Vectors (verbatim)

Source: [RFC 6901 §5](https://www.rfc-editor.org/rfc/rfc6901#section-5). Transcribed verbatim for use as assertion code blocks in test engspecs.

## The document

```json
{
  "foo": ["bar", "baz"],
  "": 0,
  "a/b": 1,
  "c%d": 2,
  "e^f": 3,
  "g|h": 4,
  "i\\j": 5,
  "k\"l": 6,
  " ": 7,
  "m~n": 8
}
```

As a Python literal:

```python
doc = {
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
```

## Pointer → referenced value (RFC 6901 §5 table)

| Pointer (literal string)   | Expected value |
|----------------------------|----------------|
| `""`                       | `doc` (the whole document) |
| `"/foo"`                   | `["bar", "baz"]` |
| `"/foo/0"`                 | `"bar"` |
| `"/"`                      | `0` (value at key `""`) |
| `"/a~1b"`                  | `1` (key is `"a/b"`; `~1` unescapes to `/`) |
| `"/c%d"`                   | `2` |
| `"/e^f"`                   | `3` |
| `"/g|h"`                   | `4` |
| `"/i\\j"`                  | `5` (key is `"i\\j"`) |
| `"/k\"l"`                  | `6` (key is `"k\"l"`) |
| `"/ "`                     | `7` (key is a single space) |
| `"/m~0n"`                  | `8` (key is `"m~n"`; `~0` unescapes to `~`) |

## Ready-to-paste assertion blocks

Each of these becomes an assertion code block in the test engspec's `### Postconditions`:

```python
assert resolve(doc, "") is doc
assert resolve(doc, "/foo") == ["bar", "baz"]
assert resolve(doc, "/foo/0") == "bar"
assert resolve(doc, "/") == 0
assert resolve(doc, "/a~1b") == 1
assert resolve(doc, "/c%d") == 2
assert resolve(doc, "/e^f") == 3
assert resolve(doc, "/g|h") == 4
assert resolve(doc, "/i\\j") == 5
assert resolve(doc, "/k\"l") == 6
assert resolve(doc, "/ ") == 7
assert resolve(doc, "/m~0n") == 8
```

## Additional assertions (not in RFC but implied by the idea)

Error cases — each inherits from `PointerError`:

```python
# PointerSyntaxError — pointer must start with '/' or be empty
with pytest.raises(PointerSyntaxError):
    resolve({}, "foo")

# PointerSyntaxError — bad escape
with pytest.raises(PointerSyntaxError):
    resolve({"a~": 1}, "/a~")       # trailing ~
with pytest.raises(PointerSyntaxError):
    resolve({"a~b": 1}, "/a~b")     # ~ not followed by 0 or 1

# KeyNotFound — key missing
with pytest.raises(KeyNotFound):
    resolve({"a": 1}, "/b")

# IndexOutOfBounds — list index past end
with pytest.raises(IndexOutOfBounds):
    resolve({"a": [1, 2]}, "/a/2")

# IndexOutOfBounds — dash index on read
with pytest.raises(IndexOutOfBounds):
    resolve({"a": [1, 2]}, "/a/-")

# PointerSyntaxError — bad index (leading zero)
with pytest.raises(PointerSyntaxError):
    resolve({"a": [1, 2]}, "/a/01")

# TypeMismatch — indexing into a scalar
with pytest.raises(TypeMismatch):
    resolve({"a": 1}, "/a/x")
```

## Out-of-scope — explicitly NOT tested

- URI fragment form (`#/foo/0`) — RFC 6901 §6.
- Encoded `~` or `/` within a fragment form.
- Negative array indices (`/a/-1`) — per RFC §4 only unsigned decimal ints.
- Mutation of the referenced element.
