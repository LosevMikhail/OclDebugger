from typing import List

from clang.cindex import Cursor, CursorKind

from LineInsertor import LineInserter
from OclSourceProcessor import OclSourceProcessor
from filters import filter_node_list_by_node_kind, filter_node_list_by_start_line
from primitives import ClTypes, VarDeclaration, StructDeclaration, Declaration


class PrintfInserter(OclSourceProcessor, LineInserter):
    _magic_string: str = '[ debugging output begins ]'
    _counter_names = ['_losev_' + e for e in ['i', 'j', 'k']]
    _variables: [VarDeclaration] = None

    def __init__(self, line: int, threads: [int]):
        OclSourceProcessor.__init__(self)
        LineInserter.__init__(self)
        self._break_line = line
        self._threads = threads
        self._structs = None

    def get_variables(self):
        return self._variables.copy()

    def get_structs(self):
        return self._structs

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

    def _find_struct_declarations(self, node: Cursor):
        structs = []
        if node.kind == CursorKind.STRUCT_DECL:
            structs.append(node)
        for child in node.get_children():
            structs.extend(self._find_struct_declarations(child))
        return structs

    @staticmethod
    def __gen_printf_arr(v: Declaration, parent=None, delim=''):
        var_name = v.var_name
        if parent is not None:
            var_name = '.'.join([parent, var_name])
        retval = f'printf("{v.var_name} ");'
        n_dims = len(v.var_shape)
        counter_names = PrintfInserter._counter_names
        if 1 == n_dims:
            retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}", {var_name});\n'
            res = PrintfInserter.__gen_cycle(counter_names[0], str(v.var_shape[0]),
                                   contents=['printf(" ");',
                                             f'printf("{ClTypes.get_printf_flag(v.var_type)}", {var_name}[{counter_names[0]}]);'])
            for e in res:
                retval += e + '\n'
        elif 2 == n_dims:
            retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}", {var_name});\n'
            inner_lines = PrintfInserter.__gen_cycle(counter_name=counter_names[1], count=str(v.var_shape[1]),
                                           contents=['printf(" ");',
                                                     f'printf("{ClTypes.get_printf_flag(v.var_type)}", {var_name}[{counter_names[0]}][{counter_names[1]}]);'])
            res = PrintfInserter.__gen_cycle(counter_name=counter_names[0], count=str(v.var_shape[0]),
                                   contents=[
                                                f'printf(" {ClTypes.get_printf_flag(ClTypes.pointer_type)}", {var_name}[{counter_names[0]}]);'] + inner_lines)
            for e in res:
                retval += e + '\n'
        elif 3 == n_dims:
            retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)}", {var_name});\n'
            inner_lines = PrintfInserter.__gen_cycle(counter_name=counter_names[2], count=str(v.var_shape[2]),
                                           contents=['printf(" ");',
                                                     f'printf("{ClTypes.get_printf_flag(v.var_type)}", {var_name}[{counter_names[0]}][{counter_names[1]}][{counter_names[2]}]);'])
            inner_lines = PrintfInserter.__gen_cycle(counter_name=counter_names[1], count=str(v.var_shape[1]),
                                           contents=[
                                                        f'printf(" {ClTypes.get_printf_flag(ClTypes.pointer_type)}", {var_name}[{counter_names[0]}][{counter_names[1]}]);'] + inner_lines)
            res = PrintfInserter.__gen_cycle(counter_name=counter_names[0], count=str(v.var_shape[0]),
                                   contents=[
                                                f'printf(" {ClTypes.get_printf_flag(ClTypes.pointer_type)}", {var_name}[{counter_names[0]}]);'] + inner_lines)
            for e in res:
                retval += e + '\n'

        retval += f'printf("{delim}");'
        return retval

    @staticmethod
    def __gen_printf_var(v: Declaration, parent=None, delim=''):
        var_name = v.var_name
        if parent is not None:
            var_name = '.'.join([parent, var_name])

        retval = ''
        retval += f'printf("{v.var_name} ");'
        if v.pointer_rank:
            retval += f'printf("{ClTypes.get_printf_flag(ClTypes.pointer_type)} {delim}", {var_name});\n'
        else:
            if v.is_struct():
                struct_type = v.var_type
                struct_names = [s.name for s in ClTypes.struct_declarations]
                if struct_type not in struct_names:
                    raise Exception("Undefined struct name")
                struct = [s for s in ClTypes.struct_declarations if s.name == struct_type]
                assert len(struct) == 1
                struct = struct[0]

                for f in struct.fields.keys():
                    if struct.fields[f].is_array:
                        t = PrintfInserter.__gen_printf_arr(struct.fields[f], parent=var_name, delim=' ')
                    else:
                        t = PrintfInserter.__gen_printf_var(struct.fields[f], parent=var_name)
                    retval += t
                retval += f'printf("{delim}");'
            else:
                retval += f'printf("{ClTypes.get_printf_flag(v.var_type)} {delim}", {var_name});\n'
        return retval

    @staticmethod
    def __gen_cycle(counter_name, count, contents: [str]):
        lines = [f'{counter_name} = 0;', f'while ({counter_name} < {count}) {{'] \
                + ['\t' + i for i in contents] + [f'\t{counter_name}++;', f'}}']
        return lines

    @staticmethod
    def generate_printf(v: Declaration) -> str:
        retval = ''
        if v.is_array:
            retval += PrintfInserter.__gen_printf_arr(v, delim='\\n')
        else:
            retval = PrintfInserter.__gen_printf_var(v, delim='\\n')
        return retval

    def _process(self, node):
        self._code_lines = self._code.split('\n')

        # 1. Find the code block containing the break line.
        blocks = self._find_blocks(node)

        # 2. Get the indent
        if len(blocks) == 0:
            raise Exception('Breakpoint is out of any function')
        parent_blocks = blocks[-1]
        self._indent = self._code_lines[parent_blocks.extent.start.line][:parent_blocks.extent.start.column]

        # 2.5. Get struct declarations
        self._structs = [StructDeclaration(c) for c in self._find_struct_declarations(self._ast_root)]
        ClTypes.struct_declarations = self._structs

        # 3. Generate the code
        counter_names = self._counter_names
        self._line_insertions.append(
            f'int {counter_names[0]} = 0; int {counter_names[1]} = 0; int {counter_names[2]} = 0;')
        self._variables = []
        for block in blocks:
            declarations = self.get_decl_statements(block)
            declarations = filter_node_list_by_start_line(declarations, by_line=self._break_line)
            var_declarations = self._get_var_declarations(declarations)
            var_declarations = [VarDeclaration(c.spelling, c.type.spelling) for c in var_declarations]
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
