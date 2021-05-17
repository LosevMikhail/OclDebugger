from SourceProcessor import SourceProcessor


class LineInserter(SourceProcessor):
    _line_insertions: [str] = []
    _indent: str = ''
    _insert_line: int = 0

    def __init__(self):
        SourceProcessor.__init__(self)

    def _apply_patches(self):
        line_insertions = []
        for line in self._line_insertions:
            line_insertions.extend([self._indent + e for e in line.split('\n')])
        lines = self._code.split('\n')
        lines = lines[:self._insert_line] + line_insertions + lines[self._insert_line:]
        self._code = '\n'.join(lines[:])
