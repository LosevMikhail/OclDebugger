from clang.cindex import Cursor, CursorKind

from LineInsertor import LineInserter
from OclSourceProcessor import OclSourceProcessor
from filters import filter_node_list_by_node_kind, filter_node_list_by_start_line
from generate_printf import generate_printf
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


def get_var_declarations(block: Cursor):
    assert block.kind == CursorKind.COMPOUND_STMT
    declarations = filter_node_list_by_node_kind(block.get_children(), [CursorKind.DECL_STMT])
    var_declarations = []
    for d in declarations:
        var_declarations.extend(
            filter_node_list_by_node_kind(d.get_children(), [CursorKind.VAR_DECL])
        )
    return var_declarations


class PrintfInserter(OclSourceProcessor, LineInserter):
    counter_names = ['_losev_' + e for e in ['i', 'j', 'k']]
    _is_kernel: bool = False
    _variables: [VarInfo] = None

    def __init__(self, line: int):
        OclSourceProcessor.__init__(self)
        LineInserter.__init__(self)
        self._break_line = line - 1

    def get_variables(self):
        return self._variables.copy()

    def _find_blocks(self, node: Cursor) -> [Cursor]:
        blocks = []
        if node.kind == CursorKind.COMPOUND_STMT:
            if node.extent.start.line <= self._break_line <= node.extent.end.line:
                blocks.append(node)
        for child in node.get_children():
            blocks.extend(self._find_blocks(child))
        return blocks

    def _process(self, node):
        self._code_lines = self._code.split('\n')

        # 1. Find the code block containing the break line.
        blocks = self._find_blocks(node)

        # 2. Get the indent
        parent_blocks = blocks[-1]
        self._indent = self._code_lines[parent_blocks.extent.start.line][:parent_blocks.extent.start.column] + '\t'

        # 3. Generate the code
        counter_names = self.counter_names
        self._line_insertions.append(
            f'int {counter_names[0]} = 0; int {counter_names[1]} = 0; int {counter_names[2]} = 0;')
        self._variables = []
        for block in blocks:
            var_declarations = get_var_declarations(block)
            var_declarations = filter_node_list_by_start_line(var_declarations, by_line=self._break_line + 1)
            # TODO: get rid of that 1
            var_declarations = [VarInfo(c) for c in var_declarations]
            self._variables.extend(var_declarations)

        for v in self._variables:
            line = generate_printf(v)
            self._line_insertions.append(line)

        # 4. Pack the code inside a block
        global_id = 0  # TODO: get the ID from outside
        self._line_insertions.insert(0,
                                     self._indent + f'if (get_global_id(0) == {global_id}) {{ // Save debugging data')
        self._line_insertions.append(self._indent + '} // Save debugging data')

        self._insert_line = self._break_line
