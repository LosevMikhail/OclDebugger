import json
import re

import numpy as np
from clang.cindex import Cursor, CursorKind


class ClTypes:
    pointer_type = 'uint'
    signed_integer_types = ['char', 'short', 'int', 'long']
    unsigned_integer_types = ['uchar', 'ushort', 'uint', 'ulong']
    integer_types = signed_integer_types + unsigned_integer_types
    float_types = ['float', 'double']
    vector_len = [2, 4, 8, 16]
    vector_base = float_types + integer_types
    vector_types = [f'{t}{n}' for t in vector_base for n in [2, 4, 8, 16]]
    scalar_types = ['char', 'uchar', 'short', 'ushort', 'int', 'uint', 'long', 'ulong', 'float', 'double']

    parser = {
        'char': np.int8,
        'uchar': np.uint8,
        'short': np.int16,
        'ushort': np.uint16,
        'int': np.int32,
        'uint': np.uint32,
        'long': np.int64,
        'ulong': np.uint64,
        'float': np.float32,
        'double': np.float64
    }
    flags = {
        'char': 'x',
        'uchar': 'x',
        'short': 'hx',
        'ushort': 'hx',
        'int': 'x',
        'uint': 'x',
        'long': 'lx',
        'ulong': 'lx',
        'float': 'f',
        'double': 'lf'
    }


def parse_scalar_value(value, var_type):
    if var_type not in ClTypes.float_types:
        value = int(value, base=16)
        return int(ClTypes.parser[var_type](value))
    return float(ClTypes.parser[var_type](value))


def parse_vector_value(value, var_type):
    elements = value.split(',')
    assert len(elements) in [2, 4, 8, 16]
    base = re.search('[a-z]+', var_type).group(0)
    return [parse_scalar_value(value=e, var_type=base) for e in elements]


def parse_value(value, var_type):
    if var_type in ClTypes.scalar_types:
        return parse_scalar_value(value=value, var_type=var_type)
    elif var_type in ClTypes.vector_types:
        return parse_vector_value(value=value, var_type=var_type)
    else:
        pass  # TODO: implement structs parsing


class VarInfo(object):
    _address_space_modifiers: [str] = ['__private', '__local', '__global']
    address_space: str
    full_type: str
    var_name: str
    var_type: str
    is_array: bool
    var_shape: []
    pointer_rank: int

    def __init__(self, node: Cursor):
        # TODO: handle arrays
        assert node.kind == CursorKind.VAR_DECL

        self.var_name = node.spelling

        # Make ASM come first
        words = node.type.spelling.split(' ')
        assert words is not None
        assert len(words) > 1
        if words[0] not in self._address_space_modifiers:
            words[0], words[1] = words[1], words[0]
        assert words[0] in self._address_space_modifiers
        self.full_type = ' '.join(words)
        self.address_space = words[0]
        self.var_type = words[1]

        # Check if it's an array
        if len(words) > 2:
            match = re.findall('\[[0-9]+\]', self.full_type)
            self.is_array = bool(len(match))
            self.var_shape = [int(re.search('[0-9]+', m).group(0)) for m in match]
        else:
            self.is_array = False

        # Check if it's a pointer TODO: test the way of check
        match = re.findall('\*', self.full_type)
        self.pointer_rank = len(match)

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __repr__(self):
        return str(self)


class Variable(object):
    def __init__(self, info: VarInfo, value: str):
        self.info = info

        if info.is_array:
            n_dims = len(info.var_shape)
            if n_dims == 1:
                values = value.split(' ')
                assert len(values) == 1 + info.var_shape[0]
                self.value = [parse_value(values[0], ClTypes.pointer_type),
                              [parse_value(v, info.var_type) for v in values[1:]]]
            elif n_dims == 2:
                values = value.split(' ')
                assert len(values) == 1 + info.var_shape[0] * (1 + info.var_shape[1])
                self.value = [parse_value(values[0], ClTypes.pointer_type)]
                for i in range(info.var_shape[0]):
                    line = values[1 + i * (1 + info.var_shape[1]): 1 + (i + 1) * (1 + info.var_shape[1])]
                    self.value.append([parse_value(line[0], ClTypes.pointer_type),
                                       [parse_value(v, info.var_type) for v in line[1:]]])
            elif n_dims == 3:
                pass  # TODO: implement
        else:
            self.value = parse_value(value, info.var_type)

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __repr__(self):
        return str(self)


if __name__ == '__main__':
    print(parse_value(value='0.100000,0.200000', var_type='double2'))
