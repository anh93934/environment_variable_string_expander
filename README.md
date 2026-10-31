# environment_variable_string_expander

Expands `$VAR` and `${VAR}` references in strings using the process environment or a custom mapping. Supports default values via `${VAR:-default}` and `${VAR-default}`; silently treats unset variables as empty.

```python
from environment_variable_string_expander import expand, expand_with_mapping, ExpansionError

expand("$HOME/bin")                       # uses os.environ
expand_with_mapping("${PATH:-/usr/bin}", {"PATH": "/opt/bin"})  # -> "/opt/bin"
expand_with_mapping("[${MISSING:-fallback}]", {})              # -> "[fallback]"
```

## Why

Configuration files and small templates frequently need to splice environment values into strings without pulling in a full template engine. This library covers exactly that: `$VAR`, `${VAR}`, and a default-value syntax. It does not implement `~`, `$(...)`, arithmetic, or nested expansion — anything beyond simple reference substitution is out of scope and intentionally left to a heavier tool.

## Names exported

- `expand(text, environ=None)` — expand against `os.environ` (or an override `dict`).
- `expand_with_mapping(text, mapping)` — expand against an explicit `dict`; values are coerced with `str()`.
- `ExpansionError` — raised on malformed references (unclosed `${VAR`, invalid characters inside braces, `${}`).

## Edge cases

A `$` followed by a non-name character (lowercase letter, digit, punctuation) is emitted literally — it is not a reference. So `$5` stays `$5`. The only way to produce a literal `$` that would otherwise start a reference is `$$` at end of string, which yields `$`.

Variable names are restricted to ASCII uppercase letters and underscores (`A-Z`, `_`). Lowercase letters terminate a `$`-reference, so `$FOO_bar` expands `$FOO` and appends `_bar`.

Default values are read verbatim up to the closing `}` — no further variable expansion happens inside a default. This is a deliberate simplification: recursive expansion inside defaults is a source of quoting ambiguity this library chooses not to open.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

