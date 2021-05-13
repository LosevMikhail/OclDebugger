from clang.cindex import Cursor, Index


class SourceProcessor:
    def __init__(self):
        self._edit = []
        self._code = ""
        self._filename = None
        self._ast_root = None

    def process_source(self, src: str, ext='cl') -> str:
        self._code = src
        self._prepare()

        self._parse(ext)
        root = self._ast_root
        self._process(root)
        self._apply_patches()

        self._defuse()
        return self._code

    @staticmethod
    def _print_node(node: Cursor, indent: int):
        print('%s %-35s %-20s %-10s [%-6s:%s - %-6s:%s] %s %s ' % (' ' * indent,
                                                                   node.kind, node.spelling, node.type.spelling,
                                                                   node.extent.start.line, node.extent.start.column,
                                                                   node.extent.end.line, node.extent.end.column,
                                                                   node.location.file, node.mangled_name))

    def print_ast(self, node: Cursor, level: int = 0):
        self._print_node(node, level)
        for child in node.get_children():  # filter_node_list_by_file(node.get_children(), self._filename):
            self.print_ast(child, level + 1)

    def _parse(self, ext='cl'):
        index = Index.create()
        translation_unit = index.parse(unsaved_files=[(f'__file__.{ext}', self._code)],
                                       path=f'__file__.{ext}',
                                       args=['-cc1'])
        self._ast_root = translation_unit.cursor

    def _prepare(self):
        pass

    def _defuse(self):
        pass

    def _process(self, node: Cursor):
        pass

    def _apply_patches(self):
        pass
