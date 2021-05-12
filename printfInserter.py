from clang.cindex import Cursor, CursorKind

from SourceProcessor import SourceProcessor
from filters import filter_node_list_by_node_kind, filter_node_list_by_start_line
from generate_printf import generate_printf
from primitives import VarInfo, ClTypes


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


class PrintfDebugger(SourceProcessor):
    counter_names = ['_losev_' + e for e in ['i', 'j', 'k']]
    _function: Cursor
    _is_kernel: bool = False
    _line_insertions = []
    _variables: [VarInfo] = None

    # TODO: get to find kernel_name
    def __init__(self, kernel_name: str, line: int):
        SourceProcessor.__init__(self)
        self.kernel_name = kernel_name
        self.break_line = line - 1

    def get_variables(self):
        return self._variables.copy()

    # TODO: rename
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
        # print([s.kind for s in scopes])

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

        # 3. Generate the code
        counter_names = self.counter_names
        self._line_insertions.append(
            f'int {counter_names[0]} = 0; int {counter_names[1]} = 0; int {counter_names[2]} = 0;')
        self._variables = []
        for scope in scopes:
            vars = get_scope_vars(scope)
            vars = filter_node_list_by_start_line(vars, by_line=self.break_line + 1)  # TODO: get rid of that 1
            vars = [VarInfo(c) for c in vars]
            self._variables.extend(vars)

        for v in self._variables:
            line = generate_printf(v)
            self._line_insertions.append(line)

    # For some reason clang doesn't parse u* and vector types so it needs a little help
    def _prepare(self):
        line_insertions = []
        # 1. u* types
        line_insertions.extend([f'typedef unsigned {t} u{t};' for t in ClTypes.signed_integer_types])
        # print(line_insertions)
        # 2. vector types.
        for t in ClTypes.vector_base:
            for n in ClTypes.vector_len:
                line_insertions.append(f'typedef {t} {t}{n} __attribute__((ext_vector_type({n})));')
        # Insert
        lines = self._code.split('\n')
        lines = line_insertions + lines[:]
        self._code = '\n'.join(lines)
        # Shift
        self.shift = len(line_insertions)
        self.break_line += self.shift

    def _apply_patches(self):
        # Add some indents
        line_insertions = []
        for l in self._line_insertions:
            line_insertions.extend([self._indent + '\t' + l for l in l.split('\n')])
        # Pack the insertions inside a special block
        id = 0
        line_insertions.insert(0, self._indent + f'if (get_global_id(0) == {id}) {{ // Save debugging data')
        line_insertions.append(self._indent + '} // Save debugging data')
        # Insert
        lines = self._code.split('\n')
        lines = lines[:self.break_line] + line_insertions + lines[self.break_line:]

        # Shift back
        self._code = '\n'.join(lines[self.shift:])
