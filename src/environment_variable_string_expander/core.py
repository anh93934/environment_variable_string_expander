"""Expand $VAR and ${VAR} references in strings.

Supported syntax:
  $NAME       NAME is one or more ASCII uppercase letters or underscores.
  ${NAME}    Same character class, no spaces or modifiers allowed inside braces.
  ${NAME:-DEFAULT}
  ${NAME-DEFAULT}

Defaults may contain characters that are not valid variable names (dashes, dots),
so the default is read verbatim until the matching closing brace — no further
variable expansion is performed inside a default value.

"""

import os


class ExpansionError(ValueError):
    """Raised on malformed reference syntax (e.g. unclosed ${VAR)."""


_NAME_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ_")


def expand(text, environ=None):
    """Expand $VAR / ${VAR} references in *text* using *environ* (defaults to os.environ).

    Unset variables expand to an empty string.
    """
    return _expand(text, environ if environ is not None else os.environ)


def expand_with_mapping(text, mapping):
    """Expand *text* using *mapping* as the variable source.

    *mapping* is converted with str() so dicts mapping names to ints/floats work.
    """
    if not isinstance(mapping, dict):
        raise TypeError("mapping must be a dict, got %r" % type(mapping).__name__)
    return _expand(text, mapping)


def _expand(text, mapping):
    if not isinstance(text, str):
        raise TypeError("text must be str, got %r" % type(text).__name__)
    result = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c != "$":
            result.append(c)
            i += 1
            continue
        # A literal $ is produced by $ followed by a non-name character,
        # or by $$ at end of string.
        if i + 1 >= n:
            result.append("$")
            i += 1
            continue
        nxt = text[i + 1]
        if nxt == "{":
            value, consumed = _parse_brace(text, i, mapping)
            result.append(value)
            i += consumed
            continue
        if nxt in _NAME_CHARS:
            j = i + 1
            while j < n and text[j] in _NAME_CHARS:
                j += 1
            name = text[i + 1:j]
            result.append(_lookup(name, mapping))
            i = j
            continue
        result.append("$")
        i += 1
    return "".join(result)


def _parse_brace(text, i, mapping):
    """Parse a ${...} reference starting at index i (where text[i] == '$').

    Returns (expanded_value, consumed_chars).
    """
    assert text[i] == "$" and text[i + 1] == "{"
    start = i + 2
    n = len(text)
    j = start
    while j < n and text[j] in _NAME_CHARS:
        j += 1
    if j == start:
        raise ExpansionError("empty variable name in ${...} at position %d" % i)
    if j >= n:
        raise ExpansionError("unterminated ${...} starting at position %d" % i)
    name = text[start:j]
    ch = text[j]
    if ch == "}":
        return _lookup(name, mapping), j - i + 1
    if ch != "-" and ch != ":":
        raise ExpansionError(
            "invalid character %r in ${...} at position %d" % (ch, j)
        )
    if ch == ":":
        if j + 1 >= n or text[j + 1] != "-":
            raise ExpansionError(
                "expected '-' after ':' in ${...} at position %d" % j
            )
        default_start = j + 2
    else:
        default_start = j + 1
    end = text.find("}", default_start)
    if end == -1:
        raise ExpansionError(
            "unterminated ${NAME:-default} starting at position %d" % i
        )
    default = text[default_start:end]
    if name in mapping:
        return str(mapping[name]), end - i + 1
    return default, end - i + 1


def _lookup(name, mapping):
    if name in mapping:
        return str(mapping[name])
    return ""
