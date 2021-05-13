from clang.cindex import Cursor, CursorKind

from LineInsertor import LineInserter
from OclSourceProcessor import OclSourceProcessor
from filters import filter_node_list_by_node_kind, filter_node_list_by_start_line
from primitives import VarInfo, ClTypes


class PrintfInserter(OclSourceProcessor, LineInserter):
    _counter_names = ['_losev_' + e for e in ['i', 'j', 'k']]
    _variables: [VarInfo] = None

    def __init__(self, line: int):
        OclSourceProcessor.__init__(self)
        LineInserter.__init__(self)
        self._break_line = line - 1

    def get_variables(self):
        return self._variables.copy()

    @staticmethod
    def get_var_declarations(block: Cursor):
        assert block.kind == CursorKind.COMPOUND_STMT
        declarations = filter_node_list_by_node_kind(block.get_children(), [CursorKind.DECL_STMT])
        var_declarations = []
        for d in declarations:
            var_declarations.extend(filter_node_list_by_node_kind(d.get_children(), [CursorKind.VAR_DECL]))
        return var_declarations

    def _find_blocks(self, node: Cursor) -> [Cursor]:
        blocks = []
        if node.kind == CursorKind.COMPOUND_STMT:
            if node.extent.start.line <= self._break_line <= node.extent.end.line:
                blocks.append(node)
        for child in node.get_children():
            blocks.extend(self._find_blocks(child))
        return blocks

    @staticmethod
    def generate_printf(v: VarInfo) -> str:
        retval = ''
        if v.is_array:
            n_dims = len(v.var_shape)
            # TODO: make them only be defined once
            counter_names = ['_losev_' + e for e in ['i', 'j', 'k']]
            if 1 == n_dims:
                retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name});\n'
                retval += f'{counter_names[0]} = 0;\n'
                retval += f'while ({counter_names[0]} < {v.var_shape[0]}) {{\n'
                retval += f'\tprintf(" ");'
                retval += f'\tprintf("{ClTypes.get_printf_flag(v.var_type)}", {v.var_name}[{counter_names[0]}++]);\n'
                retval += '}\n'
                retval += 'printf("\\n");\n'
            elif 2 == n_dims:
                retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name});\n'
                retval += f'{counter_names[0]} = 0;\n'
                retval += f'while ({counter_names[0]} < {v.var_shape[0]}) {{\n'
                retval += f'\tprintf(" {ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name}[{counter_names[0]}]);\n'
                retval += f'\t{counter_names[1]} = 0;\n'
                retval += f'\twhile ({counter_names[1]} < {v.var_shape[1]}) {{\n'
                retval += f'\tprintf(" ");'
                retval += f'\t\tprintf("{ClTypes.get_printf_flag(v.var_type)}", {v.var_name}[{counter_names[0]}][{counter_names[1]}++]);\n'
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
                retval = f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}\\n", {v.var_name});\n'
            else:
                # Both scalar and vector
                retval = f'printf("{ClTypes.get_printf_flag(v.var_type)}\\n", {v.var_name});\n'
        return retval

    def _process(self, node):
        self._code_lines = self._code.split('\n')

        # 1. Find the code block containing the break line.
        blocks = self._find_blocks(node)

        # 2. Get the indent
        parent_blocks = blocks[-1]
        self._indent = self._code_lines[parent_blocks.extent.start.line][:parent_blocks.extent.start.column] + '\t'

        # 3. Generate the code
        counter_names = self._counter_names
        self._line_insertions.append(
            f'int {counter_names[0]} = 0; int {counter_names[1]} = 0; int {counter_names[2]} = 0;')
        self._variables = []
        for block in blocks:
            var_declarations = self.get_var_declarations(block)
            var_declarations = filter_node_list_by_start_line(var_declarations, by_line=self._break_line + 1)
            # TODO: get rid of that 1
            var_declarations = [VarInfo(c) for c in var_declarations]
            self._variables.extend(var_declarations)

        for v in self._variables:
            line = self.generate_printf(v)
            self._line_insertions.append(line)

        # 4. Pack the code inside a block
        global_id = 0  # TODO: get the ID from outside
        self._line_insertions.insert(0,
                                     self._indent + f'if (get_global_id(0) == {global_id}) {{ // Save debugging data')
        self._line_insertions.append(self._indent + '} // Save debugging data')

        self._insert_line = self._break_line
