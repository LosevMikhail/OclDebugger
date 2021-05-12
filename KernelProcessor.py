from clang.cindex import Cursor, Index, CursorKind
from SourceProcessor import SourceProcessor
from filters import filter_node_list_by_node_kind, filter_node_list_by_start_line
from primitives import VarInfo


def get_node_extent(node: Cursor) -> (int, int):
    beg = node.extent.start.offset
    end = node.extent.end.offset
    return beg, end


def get_vars_info(node: Cursor, by_line: int):
    result = []
    if node.extent.start.line >= by_line:
        return []
    if node.kind == CursorKind.VAR_DECL:
        result.append(VarInfo(node))
    for child in node.get_children():
        result.extend(get_vars_info(child, by_line))
    return result


def get_scope_vars(scope: Cursor):
    assert scope.kind == CursorKind.COMPOUND_STMT
    declarations = filter_node_list_by_node_kind(scope.get_children(), [CursorKind.DECL_STMT])
    var_declarations = []
    for d in declarations:
        var_declarations.extend(
            filter_node_list_by_node_kind(d.get_children(), [CursorKind.VAR_DECL])
        )
    return var_declarations


def print_node(node: Cursor, indent: int):
    print('%s %-35s %-20s %-10s [%-6s:%s - %-6s:%s] %s %s ' % (' ' * indent,
                                                               node.kind, node.spelling, node.type.spelling,
                                                               node.extent.start.line, node.extent.start.column,
                                                               node.extent.end.line, node.extent.end.column,
                                                               node.location.file, node.mangled_name))


class KernelProcessor(SourceProcessor):
    _function: Cursor
    _is_kernel: bool = False
    _line_insertions = []

    # TODO: get to find kernel_name
    def __init__(self, kernel_name: str, line: int):
        SourceProcessor.__init__(self)
        self.kernel_name = kernel_name
        self.break_line = line - 1

    def insert_after(self, node: Cursor, src: str):
        (_, beg) = get_node_extent(node)
        self._edit.append((beg, beg, src))

    def _find_scope(self, node: Cursor) -> [Cursor]:
        scopes = []
        if node.kind == CursorKind.FUNCTION_DECL:
            compounds = filter_node_list_by_node_kind(node.get_children(), [CursorKind.COMPOUND_STMT])
            assert 1 == len(compounds)
            self._function = node

        if node.kind == CursorKind.COMPOUND_STMT:
            if node.extent.start.line <= self.break_line <= node.extent.end.line:
                scopes.append(node)
        for child in node.get_children():
            scopes.extend(self._find_scope(child))
        return scopes

    def _process(self, node):
        self._code_lines = self._code.split('\n')

        # 1. Find the scope containing the break line.
        scopes = self._find_scope(node)  # also finds the target function. TODO: separate
        print([s.kind for s in scopes])

        # Get the indent
        parent_scope = scopes[-1]
        self._indent = self._code_lines[parent_scope.extent.start.line][:parent_scope.extent.start.column] + '\t'

        # 2. Find out if the breakpoint belongs to some kernel body
        function_attributes = filter_node_list_by_node_kind(self._function.get_children(), [CursorKind.UNEXPOSED_ATTR])
        for attr in function_attributes:
            beg, end = attr.extent.start.offset, attr.extent.end.offset
            attr_spelling = self._code[beg:end]
            if attr_spelling == '__kernel':
                self._is_kernel = True

        # 2. Generate the code
        # TODO: make sure that 3 dimensions are enough for OpenCL
        # TODO: make sure that the counter names are unique
        counter_names = ['_losev_' + e for e in ['i', 'j', 'k']]
        self._line_insertions.append(
            f'int {counter_names[0]} = 0; int {counter_names[1]} = 0; int {counter_names[2]} = 0;')
        pointer_type = 'uint'
        if self._is_kernel:
            for scope in scopes:
                vars = get_scope_vars(scope)
                vars = filter_node_list_by_start_line(vars, by_line=self.break_line + 1)  # TODO: get rid of that 1
                vars = [VarInfo(c) for c in vars]
                for v in vars:
                    var_type = pointer_type if bool(v.pointer_rank) else v.var_type
                    if not v.is_array:
                        self._line_insertions.append(
                            f'*(__global {var_type}*)debuggingBuffer = {v.var_name};\n'
                            f' debuggingBuffer += sizeof ({v.var_type});\n'
                        )
                    else:
                        n_dims = len(v.var_shape)
                        if 1 == n_dims:
                            self._line_insertions.append(
                                f'*(__global {pointer_type}*)debuggingBuffer = {v.var_name};\n'
                                f'debuggingBuffer += sizeof ({pointer_type});'
                                f'{counter_names[0]} = 0;\n'
                                f'while ({counter_names[0]} < {v.var_shape[0]})'
                                ' {\n'
                                f'\t*(__global {var_type}*)debuggingBuffer = {v.var_name}[{counter_names[0]}++];\n'
                                f'\tdebuggingBuffer += sizeof ({var_type});\n'
                                '}\n'
                            )
                        elif 2 == n_dims:
                            self._line_insertions.append(
                                f'*(__global {pointer_type}*)debuggingBuffer = {v.var_name};\n'
                                f'debuggingBuffer += sizeof ({pointer_type});'
                                f'{counter_names[0]} = 0;\n'
                                f'while ({counter_names[0]} < {v.var_shape[0]})'
                                ' {\n'
                                f'\t*(__global {pointer_type}*)debuggingBuffer = {v.var_name}[{counter_names[0]}];\n'
                                f'\tdebuggingBuffer += sizeof ({pointer_type});\n'
                                f'\t{counter_names[1]} = 0;\n'
                                f'\twhile ({counter_names[1]} < {v.var_shape[1]})'
                                ' { \n'
                                f'\t\t*(__global {var_type}*)debuggingBuffer = {v.var_name}[{counter_names[0]}][{counter_names[1]}++];\n'
                                f'\t\tdebuggingBuffer += sizeof ({var_type});\n'
                                '\t}\n'
                                f'\t{counter_names[0]}++;\n'
                                '}'
                            )
                        elif 3 == n_dims:
                            pass  # TODO: implement
                        else:
                            raise Exception('Too much array dimensions...')
        else:
            pass  # TODO: implement

        # print(get_vars_info(node, self.break_line))
        self._visit_any(node)
        for child in node.get_children():
            child.parent = node
            self._visit_any(child)

    def _visit_any(self, node: Cursor):
        # TODO: get the following stuff somewhere else
        if node.kind is CursorKind.FUNCTION_DECL and node.spelling == self.kernel_name:
            params = [c for c in node.get_children() if c.kind == CursorKind.PARM_DECL]
            self.insert_after(params[-1], ', __global char* debuggingBuffer')

    def _apply_patches(self):
        print(self._line_insertions)
        self._edit.sort(key=lambda itm: itm[0])

        encd = 'UTF-8'
        code = bytearray(self._code, encd)

        # TODO: simplify
        pos = 0
        for edit in self._edit:
            src = edit[2].encode(encd)
            beg = pos + edit[0]
            end = pos + edit[1]
            code[beg:end] = src
            pos += beg - end + len(src)
        self._code = code.decode(encd)

        # Add some indents
        line_insertions = []
        for l in self._line_insertions:
            line_insertions.extend([self._indent + '\t' + l for l in l.split('\n')])
        # Pack the insertions inside a special block
        line_insertions.insert(0, self._indent + '{ // Save debugging data')
        line_insertions.append(self._indent + '} // Save debugging data')
        # Insert
        lines = self._code.split('\n')
        lines = lines[:self.break_line] + line_insertions + lines[self.break_line:]
        self._code = '\n'.join(lines)
        # print(lines)
