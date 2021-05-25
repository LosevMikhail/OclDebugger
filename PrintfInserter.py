from typing import List

from clang.cindex import Cursor, CursorKind

from LineInsertor import LineInserter
from OclSourceProcessor import OclSourceProcessor
from filters import filter_node_list_by_node_kind, filter_node_list_by_start_line
from primitives import VarInfo, ClTypes


class PrintfInserter(OclSourceProcessor, LineInserter):
    _magic_string: str = '[ debugging output begins ]'
    _counter_names = ['_losev_' + e for e in ['i', 'j', 'k']]
    _variables: [VarInfo] = None

    def __init__(self, line: int, threads: [int]):
        OclSourceProcessor.__init__(self)
        LineInserter.__init__(self)
        self._break_line = line
        self._threads = threads

    def get_variables(self):
        return self._variables.copy()

    @staticmethod
    def get_magic_string():
        return PrintfInserter._magic_string

    @staticmethod
    def get_var_declarations(block: Cursor):
        assert block.kind == CursorKind.COMPOUND_STMT
        declarations = filter_node_list_by_node_kind(block.get_children(), [CursorKind.DECL_STMT])
        var_declarations = []
        for d in declarations:
            var_declarations.extend(filter_node_list_by_node_kind(d.get_children(), [CursorKind.VAR_DECL]))
        return var_declarations

    @staticmethod
    def get_decl_statements(block: Cursor):
        assert block.kind == CursorKind.COMPOUND_STMT
        # Note: declaration statement may contain a few variable declarations
        declarations = filter_node_list_by_node_kind(block.get_children(), [CursorKind.DECL_STMT])
        return declarations

    @staticmethod
    def _get_var_declarations(declarations: List[Cursor]):
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
    def __gen_print_arr(counter_name, count, contents: [str]):
        lines = [f'{counter_name} = 0;', f'while ({counter_name} < {count}) {{'] \
                + ['\t' + i for i in contents] + [f'\t{counter_name}++;', f'}}']
        return lines

    def generate_printf(self, v: VarInfo) -> str:
        retval = ''
        if v.is_array:
            n_dims = len(v.var_shape)
            counter_names = self._counter_names
            if 1 == n_dims:
                retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name});\n'
                res = self.__gen_print_arr(counter_names[0], str(v.var_shape[0]),
                                           contents=['printf(" ");',
                                                     f'printf("{ClTypes.get_printf_flag(v.var_type)}", {v.var_name}[{counter_names[0]}]);'])
                for e in res:
                    retval += e + '\n'
                retval += 'printf("\\n");\n'
            elif 2 == n_dims:
                retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name});\n'
                inner_lines = self.__gen_print_arr(counter_name=counter_names[1], count=str(v.var_shape[1]),
                                                   contents=['printf(" ");',
                                                             f'printf("{ClTypes.get_printf_flag(v.var_type)}", {v.var_name}[{counter_names[0]}][{counter_names[1]}]);'])
                res = self.__gen_print_arr(counter_name=counter_names[0], count=str(v.var_shape[0]),
                                           contents=[f'printf(" {ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name}[{counter_names[0]}]);'] + inner_lines)
                for e in res:
                    retval += e + '\n'
                retval += 'printf("\\n");'
            elif 3 == n_dims:
                retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name});\n'
                inner_lines = self.__gen_print_arr(counter_name=counter_names[2], count=str(v.var_shape[2]),
                                                   contents=['printf(" ");',
                                                             f'printf("{ClTypes.get_printf_flag(v.var_type)}", {v.var_name}[{counter_names[0]}][{counter_names[1]}][{counter_names[2]}]);'])
                inner_lines = self.__gen_print_arr(counter_name=counter_names[1], count=str(v.var_shape[1]),
                                                   contents=[f'printf(" {ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name}[{counter_names[0]}][{counter_names[1]}]);'] + inner_lines)
                res = self.__gen_print_arr(counter_name=counter_names[0], count=str(v.var_shape[0]),
                                           contents=[f'printf(" {ClTypes.get_printf_flag(ClTypes.pointer_type)}", {v.var_name}[{counter_names[0]}]);'] + inner_lines)
                for e in res:
                    retval += e + '\n'
                retval += 'printf("\\n");'
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
        self._indent = self._code_lines[parent_blocks.extent.start.line][:parent_blocks.extent.start.column]

        # 3. Generate the code
        counter_names = self._counter_names
        self._line_insertions.append(
            f'int {counter_names[0]} = 0; int {counter_names[1]} = 0; int {counter_names[2]} = 0;')
        self._variables = []
        for block in blocks:
            declarations = self.get_decl_statements(block)
            declarations = filter_node_list_by_start_line(declarations, by_line=self._break_line)
            var_declarations = self._get_var_declarations(declarations)
            var_declarations = [VarInfo(c) for c in var_declarations]
            self._variables.extend(var_declarations)

        for v in self._variables:
            line = self.generate_printf(v)
            self._line_insertions.append(line)

        # 4. Pack the code inside a block
        lines = []
        for e in self._line_insertions:
            lines.extend(e.split('\n'))
        self._line_insertions = ['\t' * 2 + e for e in lines]
        threads_array = '_losev_target_threads'
        thread_counter = '_losev_thread_counter'
        initializer_list = ', '.join([str(i) for i in self._threads])
        # TODO: something about the indents
        self._line_insertions.insert(0, f'int {threads_array}[] = {{{initializer_list}}};')
        self._line_insertions.insert(1,
                                     f'if (get_global_id(0) == *{threads_array}) {{ printf("{self._magic_string}\\n"); }} \n')
        self._line_insertions.insert(2,
                                     f'for (int {thread_counter} = 0; {thread_counter} < {len(self._threads)}; {thread_counter}++) {{')
        self._line_insertions.insert(3,
                                     f'\tif (get_global_id(0) == {threads_array}[{thread_counter}]) {{ // Save '
                                     f'debugging data')
        self._line_insertions.append('\t} // Save debugging data')
        self._line_insertions.append('} // ?')
        # self._indent = self._indent[:-1]
        # self._line_insertions.append(self._indent + '}')

        self._insert_line = self._break_line


if __name__ == '__main__':
    res = PrintfInserter.gen_print_arr('i', str(10),
                                       PrintfInserter.gen_print_arr('j', str(11), ['printf("%d", i);']))
    for e in res:
        print(e)
