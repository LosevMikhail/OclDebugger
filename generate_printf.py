import re
import numpy as np
from primitives import VarInfo, ClTypes


def get_flag(var_type: str):
    if var_type in ClTypes.scalar_types:
        return f'%{ClTypes.flags[var_type]}'
    if var_type in ClTypes.vector_types:
        n = re.search('[0-9]+', var_type).group(0)
        base = re.search('[a-z]+', var_type).group(0)
        return f'%v{n}{ClTypes.flags[base]}'
    assert False  # Fail if it's not a primitive type


def generate_printf(v: VarInfo) -> str:
    retval = ''
    if v.is_array:
        n_dims = len(v.var_shape)
        # TODO: make them only be defined once
        counter_names = ['_losev_' + e for e in ['i', 'j', 'k']]
        if 1 == n_dims:
            retval += f'printf("{get_flag(ClTypes.pointer_type)}", {v.var_name});\n'
            retval += f'{counter_names[0]} = 0;\n'
            retval += f'while ({counter_names[0]} < {v.var_shape[0]}) {{\n'
            retval += f'\tprintf(" ");'
            retval += f'\tprintf("{get_flag(v.var_type)}", {v.var_name}[{counter_names[0]}++]);\n'
            retval += '}\n'
            retval += 'printf("\\n");\n'
        elif 2 == n_dims:
            retval += f'printf("{get_flag(ClTypes.pointer_type)}", {v.var_name});\n'
            retval += f'{counter_names[0]} = 0;\n'
            retval += f'while ({counter_names[0]} < {v.var_shape[0]}) {{\n'
            retval += f'\tprintf(" {get_flag(ClTypes.pointer_type)}", {v.var_name}[{counter_names[0]}]);\n'
            retval += f'\t{counter_names[1]} = 0;\n'
            retval += f'\twhile ({counter_names[1]} < {v.var_shape[1]}) {{\n'
            retval += f'\tprintf(" ");'
            retval += f'\t\tprintf("{get_flag(v.var_type)}", {v.var_name}[{counter_names[0]}][{counter_names[1]}++]);\n'
            retval += '\t}\n'
            retval += f'\t{counter_names[0]}++;\n'
            retval += '}\n'
            retval += 'printf("\\n");'
        elif 3 == n_dims:
            pass  # TODO: implement
        else:
            raise Exception('Too much array dimensions...')
    else:
        if v.pointer_rank:
            retval = f'printf("{get_flag(ClTypes.pointer_type)}\\n", {v.var_name});\n'
        else:
            # Both scalar and vector
            retval = f'printf("{get_flag(v.var_type)}\\n", {v.var_name});\n'
    return retval


if __name__ == '__main__':
    x = '000000003dcdd2f2'
    print(len(x))
    f64 = np.fromstring(x, dtype=np.float64)
    print(f64)
    exit(0)
