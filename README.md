jsonschema
==========

Validate and clean heterogeneous data structures based on custom specifications:

```python

import jsonschema

clean_foo = jsonschema.clean({
    "foo_attr": jsonschema.Number(),
    "optional_foo_attr": jsonschema.Optional(jsonschema.String()),
    "nested": {
       "nested_foo_attr": jsonschema.Date()
    },
    "multiple": [jsonschema.String()],
    "tuple": (jsonschema.Number(), jsonschema.Boolean()),
    "enum": jsonschema.Any(
        jsonschema.Constant("FOO"),
        jsonschema.Constant("BAR"),
        jsonschema.Constant("BAZ")
    )
})

# returns a 'cleaned' data structure
clean_foo({
    "foo_attr": 123,
    "nested": {
       "nested_foo_attr": "2017-08-10",
    },
    "multiple": ["foo", "bar"],
    "tuple": [1, False],
    "enum": "BAR"
})

clean_foo({}) # raises jsonschema.ValidationError
```

## Ground types

**jsonschema.Type(condition=None)** base type used for arbitrary validation. An alias is `jsonschema.Variant`. `condition` can be a callable that gets invoked after parsing, and can trigger a failure if it returns a falsey value or if it raises an exception.

**jsonschema.String(strict=True, condition=None)** validates string types. `strict=False` makes it ignore the type altogether, making it call `str` on the value when parsing.

**jsonschema.RegexString(regex=None, condition=None)** validates a string against a regular expression. `regex` must be the pattern in string form.

**jsonschema.Number(min=None, max=None, strict=False, condition=None)** validates a number. `min` and `max` can be used to specify boundaries, and `strict=True` disables parsing of strings to numbers.

**jsonschema.Null()** only accepts the `None` value.

**jsonschema.Date(condition=None)** accepts strings representing dates in `'%Y-%m-%d'` format. A valid date object is returned after parsing.

**jsonschema.Datetime(condition=None)** accepts strings represeting datetimes in any of these formats: `('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S.%fZ')`.

**jsonschema.Boolean(strict=True)** accepts boolean values. `strict=False` makes it accept variations for `False`: `('no', 'False', 'false', 'f', '0', 0, None)`; and variations for `True`: `('yes', 'True', 'true', 't', '1', 1)`.

**jsonschema.Constant(value)** accepts only `value`, checking it with the inequality operator `!=`.

## Composite types

**jsonschema.Optional(othertype)** accepts whatever `othertype` accepts, or `None` (or abscence).

__jsonschema.Any(*ts)__ accepts any value validated by some type in *ts, and parses it with the first one that passes validation.

**()** (python tuples) accepts tuples or lists of elements of exactly the number of elements in the schema's tuple, and wich pass the validations defined whithin (positionally).

**[type]** accepts tuples or lists of any number of values passing the validation of `type`.

**{"key": type}** accepts dictionaries with keys specified in the schema's dictionary, and with values passing the corresponding `type`'s validation.
