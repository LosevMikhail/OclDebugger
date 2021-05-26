import abc
import json
import re
from abc import ABC
from typing import List, Tuple

import numpy as np
from clang.cindex import Cursor, CursorKind

from filters import filter_node_list_by_node_kind


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

    struct_declarations: [] = None

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

    @staticmethod
    def get_struct_decl(struct_name: str):
        struct_names = [s.name for s in ClTypes.struct_declarations]
        if struct_name not in struct_names:
            raise Exception("Undefined struct name")
        struct = [s for s in ClTypes.struct_declarations if s.name == struct_name]
        assert len(struct) == 1
        struct = struct[0]
        return struct

    @staticmethod
    def get_struct_types():
        return [e.name for e in ClTypes.struct_declarations]


class Declaration(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.var_type = None
        self.var_shape = None
        self.is_array = None

    def is_struct(self):
        return self.var_type not in ClTypes.scalar_types and \
               self.var_type not in ClTypes.vector_types

    def words_num(self):
        val_words = 0
        if self.is_array:
            t = 1
            shape_rev = reversed(self.var_shape)
            for d in shape_rev:
                t *= d
                t += 1
            val_words = t
        elif self.is_struct():
            struct_decl = ClTypes.get_struct_decl(self.var_type)
            val_words = struct_decl.words_num()
        else:
            val_words = 1

        return 1 + val_words  # 1 for variable name signing

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __repr__(self):
        return str(self)


class VarDeclaration(Declaration, ABC):
    _address_space_modifiers: [str] = ['__private', '__local', '__global']

    def __init__(self, var_name: str, full_type: str):
        super().__init__()
        self.var_name = var_name
        # Make ASM come first
        words = full_type.split(' ')
        assert words is not None
        assert len(words) > 1
        if words[0] not in self._address_space_modifiers:
            words[0], words[1] = words[1], words[0]
        assert words[0] in self._address_space_modifiers
        self.full_type = ' '.join(words)
        self.address_space = words[0]
        is_struct = words[1] == 'struct'
        if is_struct:
            self.var_type = words[2]
        else:
            self.var_type = words[1]

        # Check if it's an array
        if len(words) > 2 + int(is_struct):
            match = re.findall('\[[0-9]+\]', self.full_type)
            self.is_array = bool(len(match))
            self.var_shape = [int(re.search('[0-9]+', m).group(0)) for m in match]
        else:
            self.is_array = False

        # Check if it's a pointer
        match = re.findall('\*', self.full_type)
        self.pointer_rank = len(match)


class FieldDeclaration(Declaration, ABC):
    def __init__(self, node: Cursor):
        super().__init__()
        assert node.kind == CursorKind.FIELD_DECL

        self.var_name = node.spelling

        # Make ASM come first
        words = node.type.spelling.split(' ')
        assert words is not None
        assert len(words) > 0
        self.full_type = ' '.join(words)

        is_struct = words[0] == 'struct'
        if is_struct:
            self.var_type = words[1]
        else:
            self.var_type = words[0]

        # Check if it's an array
        if len(words) > 1 + int(is_struct):
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

        values = value.split(' ')
        assert values[0] == decl.var_name
        value = ' '.join(values[1:])
        self.value = self.__parse_var(value, decl)

    @staticmethod
    def __parse_var(value, decl):
        if decl.is_array:
            return Variable.__parse_array(value.split(' '), decl.var_shape, decl.var_type)
        else:
            return Variable.__parse_value(value, decl.var_type)

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
            return Variable.__parse_struct(value=value, var_type=var_type)

    @staticmethod
    def __parse_struct(value, var_type):
        struct_type = var_type
        struct_names = [s.name for s in ClTypes.struct_declarations]
        if struct_type not in struct_names:
            raise Exception("Undefined struct name")
        struct = [s for s in ClTypes.struct_declarations if s.name == struct_type]
        assert len(struct) == 1
        struct = struct[0]

        retval = {}
        elements = value.split(' ')
        i = 0
        for f in struct.fields.keys():
            field_decl = struct.fields[f]
            field_type = field_decl.var_type
            assert elements[i] == field_decl.var_name
            i += 1
            if field_decl.is_array:
                values = elements[i:i+field_decl.words_num() - 1]
                i += field_decl.words_num() - 1
                retval[f] = Variable.__parse_array(values, field_decl.var_shape, field_decl.var_type)
            else:
                if field_type in ClTypes.scalar_types:
                    retval[f] = Variable.__parse_scalar_value(elements[i], field_type)
                    i += 1
                elif field_type in ClTypes.vector_types:
                    retval[f] = Variable.__parse_vector_value(elements[i], field_type)
                    i += 1
                elif field_type in ClTypes.get_struct_types():
                    l = field_decl.words_num()
                    retval[f] = Variable.__parse_struct(' '.join(elements[i: i + l - 1]), field_type)
                    i += l - 1

        return retval

    @staticmethod
    def __parse_array(arr: [str], var_shape: [int], var_type: str):
        n_dims = len(var_shape)
        if n_dims == 1:
            return Variable.__parse_1d_array(arr, var_shape, var_type)
        elif n_dims == 2:
            return Variable.__parse_2d_array(arr, var_shape, var_type)
        elif n_dims == 3:
            return Variable.__parse_3d_array(arr, var_shape, var_type)

    @staticmethod
    def __parse_1d_array(arr: [str], var_shape: [int], var_type: str) -> Tuple:
        assert len(arr) == 1 + var_shape[0]
        return (Variable.__parse_value(arr[0], ClTypes.pointer_type),
                [Variable.__parse_value(v, var_type) for v in arr[1:]])

    @staticmethod
    def __parse_2d_array(arr: [str], var_shape: [int], var_type: str)  -> Tuple:
        assert len(arr) == 1 + var_shape[0] * (1 + var_shape[1])
        values = []
        for i in range(var_shape[0]):
            array_1d = arr[1 + (i + 0) * (1 + var_shape[1]): 1 + (i + 1) * (1 + var_shape[1])]
            values.append(Variable.__parse_1d_array(array_1d, (var_shape[1],), var_type))
        return Variable.__parse_value(arr[0], ClTypes.pointer_type), values

    @staticmethod
    def __parse_3d_array(arr: [str], var_shape: [int], var_type: str) -> Tuple:
        assert len(arr) == 1 + var_shape[0] * (1 + var_shape[1] * (1 + var_shape[2]))
        retval = []
        for i in range(var_shape[0]):
            array_2d = arr[1 + (i + 0) * (1 + var_shape[1] * (1 + var_shape[2])):
                           1 + (i + 1) * (1 + var_shape[1] * (1 + var_shape[2]))]
            retval.append(Variable.__parse_2d_array(array_2d, (var_shape[1], var_shape[2]), var_type))
        return Variable.__parse_value(arr[0], ClTypes.pointer_type), retval

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __repr__(self):
        return str(self)


class StructDeclaration(object):
    def __init__(self, node: Cursor):
        assert node.kind == CursorKind.STRUCT_DECL
        self.name = node.spelling
        fields = filter_node_list_by_node_kind(node.get_children(), [CursorKind.FIELD_DECL])
        self.fields = {}
        for f in fields:
            self.fields[f.spelling] = FieldDeclaration(f)

    def words_num(self):
        retval = 0
        for f in self.fields.keys():
            field_decl = self.fields[f]
            retval += field_decl.words_num()
        return retval

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def __repr__(self):
        return str(self)


if __name__ == '__main__':
    print(Variable.__parse_value(value='0.100000,0.200000', var_type='double2'))
