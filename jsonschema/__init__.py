import datetime
import decimal
import re


TRACE_SEP = ' --> '


class ValidationError(ValueError):
    def __init__(self, value, message, trace):
        self.value = value
        self.message = message
        self.trace = trace

    def __str__(self):
        return f'{self.value} {self.message}'

    def __repr__(self):
        return f'jsonschema.ValidationError: {str(self)} ; Trace: {self.trace}'


class Type:
    def invalid(self, value, message):
        return ValidationError(value, message, type(self).__name__)

    def __init__(self, condition=None):
        self.condition = condition if condition is not None else (lambda x: True)

    def validate(self, value):
        pass

    def parse(self, value):
        return value

    def get_parsed_value(self, value):
        parsed = self.parse(value)
        if getattr(self, 'condition', None) is not None:
            try:
                passes = self.condition(parsed)
            except Exception as e:
                raise self.invalid(
                    value,
                    e.args[0] if e.args else 'doesn\'t meet the validation criterion'
                )
            if not passes:
                raise self.invalid(value, 'doesn\'t meet the validation criterion')
        return parsed


# Alias for public use
Variant = Type


class String(Type):
    def __init__(self, strict=True, condition=None):
        super().__init__(condition=condition)
        self.strict = strict

    def validate(self, value):
        if self.strict and not isinstance(value, str):
            raise self.invalid(value, 'is not a string')

    def parse(self, value):
        return str(value)


class RegexString(Type):
    def __init__(self, regex=None, condition=None):
        super().__init__(condition=condition)
        self.regex = regex
        self.match = re.compile(regex).match

    def validate(self, value):
        try:
            matchobj = self.match(value)
        except Exception:
            raise self.invalid(value, f'doesn\'t match pattern {self.regex}')
        if matchobj is None:
            raise self.invalid(value, f'doesn\'t match pattern {self.regex}')


class Number(Type):
    match = re.compile('^\d+(\.\d+)?$').match

    def __init__(self, min=None, max=None, strict=False, condition=None):
        super().__init__(condition=condition)
        self.min = min
        self.max = max
        self.strict = strict

    def validate(self, value):
        if isinstance(value, (int, float, decimal.Decimal)):
            return None
        if self.strict:
            raise self.invalid(value, 'is not a number')
        if not isinstance(value, str):
            raise self.invalid(value, 'is not a number')
        if self.match(value) is None:
            raise self.invalid(value, 'is not a validly formatted number')

    def parse(self, value):
        if isinstance(value, decimal.Decimal):
            return value
        parsed = float(value)
        return parsed if not parsed.is_integer() else int(parsed)

    def get_parsed_value(self, value):
        parsed = super().get_parsed_value(value)
        if self.min is not None and parsed < self.min:
            raise self.invalid(value, f'is less than the minimum: {self.min}')
        if self.max is not None and parsed > self.max:
            raise self.invalid(value, f'is greater than the maximum: {self.max}')
        return parsed


class Null(Type):
    def __init__(self):
        pass

    def validate(self, value):
        if value is not None:
            raise self.invalid(value, 'is not null')


class Date(RegexString):
    pattern = '^\d{4}-\d{2}-\d{2}$'

    def __init__(self, condition=None):
        super().__init__(regex=self.pattern, condition=condition)

    def parse(self, value):
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise self.invalid(value, 'is an invalid date')


class Datetime(RegexString):
    pattern = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d*)?Z?$'

    def __init__(self, condition=None):
        super().__init__(regex=self.pattern, condition=condition)

    def _attempt_parse(self, value, p):
        try:
            return datetime.datetime.strptime(value, p)
        except ValueError:
            return None

    def parse(self, value):
        patterns = (
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ',
        )
        try:
            return next(
                parsed
                for parsed in (self._attempt_parse(value, p) for p in patterns)
                if parsed is not None
            )
        except StopIteration:
            raise self.invalid(value, 'is an invalid datetime')


class Boolean(Type):
    admissible_true = (
        'yes',
        'True',
        'true',
        't',
        '1',
        1,
    )

    admissible_false = (
        'no',
        'False',
        'false',
        'f',
        '0',
        0,
        None
    )

    def __init__(self, strict=True):
        self.strict = strict

    def validate(self, value):
        if value is True or value is False:
            return None
        if self.strict:
            raise self.invalid(value, 'is not boolean')
        if value not in self.admissible_true and value not in self.admissible_false:
            raise self.invalid(value, 'can\'t be interpreted as boolean')

    def parse(self, value):
        if value is True or value is False:
            return value
        if value in self.admissible_false:
            return False
        return True


class Optional(Type):
    def __init__(self, othertype):
        assert isinstance(othertype, (Type, dict, list, tuple)), \
            'Optional can only be applied to other types or aggregates'
        self.othertype = othertype

    def invalid(self, value, message, error):
        return ValidationError(value, message, f'Optional({error})')

    def validate(self, value):
        if value is None:
            return None
        try:
            return _validate(value, self.othertype)
        except ValidationError as e:
            raise self.invalid(e.value, e.message, e.trace)

    def parse(self, value):
        if value is None:
            return None
        try:
            return _parse(value, self.othertype)
        except ValidationError as e:
            raise self.invalid(e.value, e.message, e.trace)


class Any(Type):
    def __init__(self, first, *others):
        assert all(isinstance(t, (Type, dict, list, tuple)) for t in ((first,) + others)), \
            'Any can only be applied to other types or aggregates'
        self.types = (first,) + others

    def invalid(self, value, message, errors=None):
        errors = errors or []
        traces = ', '.join(e.trace for e in errors)
        return ValidationError(value, message, f'Any({traces})')

    def parse(self, value):
        errors = []
        for t in self.types:
            try:
                _validate(value, t)
                return _parse(value, t)
            except ValidationError as e:
                errors.append(e)
        raise self.invalid(value, f'doesn\'t meet any allowed criterion', errors=errors)


class Constant(Type):
    def __init__(self, constant):
        self.constant = constant

    def invalid(self, value, message):
        return ValidationError(value, message, f'Constant({repr(self.constant)})')

    def validate(self, value):
        if value != self.constant:
            raise self.invalid(value, f'is not equals to {repr(self.constant)}')


def _validate(variant, schema, current_trace=''):
    if isinstance(schema, Type):
        try:
            return schema.validate(variant)
        except ValidationError as e:
            e.trace = f'{current_trace}{e.trace}'
            raise e
    if isinstance(schema, dict):
        if not isinstance(variant, dict):
            raise ValidationError(variant, 'is not an object', f'{current_trace}Object')
        for k in schema:
            if k not in variant and not isinstance(schema[k], Optional):
                raise ValidationError(variant, f'doesn\'t have key "{k}"', f'{current_trace}Object')
        for k, v in variant.items():
            if k in schema:
                _validate(
                    v,
                    schema[k],
                    current_trace=f'{current_trace}Object(key:{repr(k)}){TRACE_SEP}'
                )
        return None
    if isinstance(schema, list):
        if len(schema) > 1:
            raise TypeError(
                'schema is a list of more than one element; '
                'can be empty or have just one'
            )
        if not isinstance(variant, (list, tuple)):
            raise ValidationError(variant, 'is not a list or tuple', f'{current_trace}List')
        if not schema:
            return None
        for i, e in enumerate(variant):
            _validate(e, schema[0], current_trace=f'{current_trace}List(index:{i}){TRACE_SEP}')
        return None
    if isinstance(schema, tuple):
        if not isinstance(variant, (list, tuple)):
            raise ValidationError(variant, 'is not a list or tuple', f'{current_trace}Tuple')
        if len(schema) != len(variant):
            which = 'few' if len(variant) < len(schema) else 'many'
            raise ValidationError(
                variant,
                f'has too {which} elements (it requires {len(schema)})',
                f'{current_trace}Tuple'
            )
        for i, subschema in enumerate(schema):
            _validate(
                variant[i],
                subschema,
                current_trace=f'{current_trace}Tuple(index:{i}){TRACE_SEP}'
            )
        return None
    raise TypeError(f'schema of type {type(schema)} is not valid')


def _parse(variant, schema, current_trace=''):
    if isinstance(schema, Type):
        try:
            return schema.get_parsed_value(variant)
        except ValidationError as e:
            e.trace = f'{current_trace}{e.trace}'
            raise e
    if isinstance(schema, dict):
        return {
            k: _parse(
                variant.get(k),
                subschema,
                current_trace=f'{current_trace}Object(key:{repr(k)}){TRACE_SEP}'
            )
            for k, subschema in schema.items()
        }
    if isinstance(schema, list):
        if not schema:
            return []
        return [
            _parse(e, schema[0], current_trace=f'{current_trace}List(index:{i}){TRACE_SEP}')
            for i, e in enumerate(variant)
        ]
    if isinstance(schema, tuple):
        return tuple(
            _parse(e, schema[i], current_trace=f'{current_trace}Tuple(index:{i}){TRACE_SEP}')
            for i, e in enumerate(variant)
        )
    raise TypeError(f'schema of type {type(schema)} is not valid')


def clean(schema):
    def cleaner(variant):
        _validate(variant, schema)
        return _parse(variant, schema)

    return cleaner
