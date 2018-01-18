import datetime

import jsonschema


def fail(msg):
    raise ValueError(msg)


clean = jsonschema.clean({
    "foo": jsonschema.String(),
    "bar": jsonschema.Number(),
    "hoho": jsonschema.Optional(jsonschema.Number()),
    "nest": {
        "somedate": jsonschema.Date(),
        "constrained_date": jsonschema.Datetime(
            condition=lambda d: fail('date must be later than 2017-01-01')
            if d > datetime.datetime(2017, 1, 1)
            else True
        ),
        "nest": [jsonschema.Number(min=0)],
    },
    "mixed": jsonschema.Optional([jsonschema.Any(
        jsonschema.String(),
        jsonschema.Number(),
        jsonschema.Boolean(),
        [jsonschema.Null()],
    )]),
    "pairlist": [(jsonschema.String(), jsonschema.Number())],
    "strict_bool": jsonschema.Boolean(),
    "permissive_bool": jsonschema.Boolean(strict=False),
    "enum": jsonschema.Any(
        jsonschema.Constant("FOO"),
        jsonschema.Constant("BAR"),
        jsonschema.Constant("BAZ"),
    )
})


if __name__ == '__main__':
    test_passing = {
        "foo": "hello",
        "bar": "1234",
        "nest": {
            "somedate": "2000-01-01",
            "constrained_date": "2000-01-02T10:10:10.123Z",
            "nest": [1, 2, 3, 4],
            "somethingextra": "not validated",
        },
        "mixed": [1, "hello", True, 123.1234, [None], "OH MY GOD"],
        "pairlist": [
            ["hello", 1],
            ["goodbye", 120],
        ],
        "strict_bool": True,
        "permissive_bool": 'false',
        "enum": "BAZ",
    }
    print("RAW", test_passing)
    print("CLEAN", clean(test_passing))
    print()

    test_failing_condition = {
        "foo": "hello",
        "bar": "1234",
        "nest": {
            "somedate": "2000-01-01",
            "constrained_date": "2018-01-02T10:10:10",
            "nest": [1, 2, 3, 4]
        },
        "pairlist": [
            ["hello", 1],
            ["goodbye", 120],
        ],
        "strict_bool": True,
        "permissive_bool": 'false',
        "enum": "BAZ",
    }
    print("RAW", test_failing_condition)
    try:
        clean(test_failing_condition)
    except jsonschema.ValidationError as e:
        print("ERROR", e)
        print("TRACE", e.trace)
        print()

    test_failing_schema = {
        "foo": "hello",
        "bar": "1234",
        "hoho": "1234a",
        "nest": {
            "somedate": "2000-01-01",
            "constrained_date": "2000-01-02T10:10:10",
            "nest": [1, 2, 3, 4]
        },
        "pairlist": [
            ["hello", 1],
            ["goodbye", 120],
        ],
        "strict_bool": True,
        "permissive_bool": 'false',
        "enum": "BAZ",
    }
    print("RAW", test_failing_schema)
    try:
        clean(test_failing_schema)
    except jsonschema.ValidationError as e:
        print("ERROR", e)
        print("TRACE", e.trace)
        print()

    test_failing_composite = {
        "foo": "hello",
        "bar": "1234",
        "hoho": "1234.1234",
        "nest": {
            "somedate": "2000-01-01",
            "constrained_date": "2000-01-02T10:10:10",
            "nest": [1, 2, 3, 4]
        },
        "mixed": [1, 2, [3, 4, None]],
        "pairlist": [
            ["hello", 1],
            ["goodbye", 120],
        ],
        "strict_bool": True,
        "permissive_bool": 'false',
        "enum": "BAZ",
    }
    print("RAW", test_failing_composite)
    try:
        clean(test_failing_composite)
    except jsonschema.ValidationError as e:
        print("ERROR", e)
        print("TRACE", e.trace)
        print()

    test_failing_tuple = {
        "foo": "hello",
        "bar": "1234",
        "hoho": "1234.1234",
        "nest": {
            "somedate": "2000-01-01",
            "constrained_date": "2000-01-02T10:10:10",
            "nest": [1, 2, 3, 4]
        },
        "mixed": [1, 2],
        "pairlist": [
            ["hello", 1],
            ["goodbye", 120],
            ["butwait", 1000, 1000],
        ],
        "strict_bool": True,
        "permissive_bool": 'false',
        "enum": "BAZ",
    }
    print("RAW", test_failing_tuple)
    try:
        clean(test_failing_tuple)
    except jsonschema.ValidationError as e:
        print("ERROR", e)
        print("TRACE", e.trace)
        print()

    test_failing_enum = {
        "foo": "hello",
        "bar": "1234",
        "hoho": "1234.1234",
        "nest": {
            "somedate": "2000-01-01",
            "constrained_date": "2000-01-02T10:10:10",
            "nest": [1, 2, 3, 4]
        },
        "mixed": [1, 2],
        "pairlist": [
            ["hello", 1],
            ["goodbye", 120],
            ["butwait", 1000],
        ],
        "strict_bool": True,
        "permissive_bool": 'false',
        "enum": "BARZ",
    }
    print("RAW", test_failing_enum)
    try:
        clean(test_failing_enum)
    except jsonschema.ValidationError as e:
        print("ERROR", e)
        print("TRACE", e.trace)
