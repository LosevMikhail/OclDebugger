import abc
import json
import re
from abc import abstractmethod, ABC

import numpy as np
from clang.cindex import Cursor, CursorKind


class ClTypes:
    # TODO: add half types
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

    @staticmethod
    def get_printf_flag(var_type: str):
        if var_type in ClTypes.scalar_types:
            return f'%{ClTypes.flags[var_type]}'
        if var_type in ClTypes.vector_types:
            n = re.search('[0-9]+', var_type).group(0)
            base = re.search('[a-z]+', var_type).group(0)
            return f'%v{n}{ClTypes.flags[base]}'
        assert False  # Fail if it's not a primitive type


class Declaration(object):
    __metaclass__ = abc.ABCMeta

    @abstractmethod
    def is_struct(self):
        pass

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __repr__(self):
        return str(self)


class VarDeclaration(Declaration, ABC):
    _address_space_modifiers: [str] = ['__private', '__local', '__global']

    def __init__(self, node: Cursor):
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

        # Check if it's a pointer
        match = re.findall('\*', self.full_type)
        self.pointer_rank = len(match)


class Variable(object):
    def __init__(self, decl: VarDeclaration, value: str, gid: int = None):
        self.decl = decl
        self.gid = gid

        if decl.is_array:
            n_dims = len(decl.var_shape)
            values = value.split(' ')
            if n_dims == 1:
                self.value = self.__parse_1d_array(values, decl.var_shape, decl.var_type)
            elif n_dims == 2:
                self.value = self.__parse_2d_array(values, decl.var_shape, decl.var_type)
            elif n_dims == 3:
                self.value = self.__parse_3d_array(values, decl.var_shape, decl.var_type)
        else:
            self.value = self.__parse_value(value, decl.var_type)

    @staticmethod
    def __parse_scalar_value(value, var_type):
        if var_type not in ClTypes.float_types:
            value = int(value, base=16)
            return int(ClTypes.parser[var_type](value))
        return float(ClTypes.parser[var_type](value))

    @staticmethod
    def __parse_vector_value(value, var_type):
        elements = value.split(',')
        assert len(elements) in [2, 4, 8, 16]
        base = re.search('[a-z]+', var_type).group(0)
        return [Variable.__parse_scalar_value(value=e, var_type=base) for e in elements]

    @staticmethod
    def __parse_value(value, var_type):
        if var_type in ClTypes.scalar_types:
            return Variable.__parse_scalar_value(value=value, var_type=var_type)
        elif var_type in ClTypes.vector_types:
            return Variable.__parse_vector_value(value=value, var_type=var_type)
        else:
            pass  # TODO: implement structs parsing

    @staticmethod
    def __parse_1d_array(arr: [str], var_shape: [int], var_type: str):
        assert len(arr) == 1 + var_shape[0]
        return [Variable.__parse_value(arr[0], ClTypes.pointer_type),
                [Variable.__parse_value(v, var_type) for v in arr[1:]]]

    @staticmethod
    def __parse_2d_array(arr: [str], var_shape: [int], var_type: str):
        assert len(arr) == 1 + var_shape[0] * (1 + var_shape[1])
        retval = [Variable.__parse_value(arr[0], ClTypes.pointer_type)]
        for i in range(var_shape[0]):
            array_1d = arr[1 + (i + 0) * (1 + var_shape[1]): 1 + (i + 1) * (1 + var_shape[1])]
            retval.append(Variable.__parse_1d_array(array_1d, (var_shape[1],), var_type))
        return retval

    @staticmethod
    def __parse_3d_array(arr: [str], var_shape: [int], var_type: str):
        assert len(arr) == 1 + var_shape[0] * (1 + var_shape[1] * (1 + var_shape[2]))
        retval = [Variable.__parse_value(arr[0], ClTypes.pointer_type)]
        for i in range(var_shape[0]):
            array_2d = arr[1 + (i + 0) * (1 + var_shape[1] * (1 + var_shape[2])):
                           1 + (i + 1) * (1 + var_shape[1] * (1 + var_shape[2]))]
            retval.append(Variable.__parse_2d_array(array_2d, (var_shape[1], var_shape[2]), var_type))
        return retval

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __repr__(self):
        return str(self)


if __name__ == '__main__':
    a = Declaration()
    print('a')
    # print(Variable.parse_value(value='0.100000,0.200000', var_type='double2'))
