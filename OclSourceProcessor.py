from SourceProcessor import SourceProcessor
from primitives import ClTypes


class OclSourceProcessor(SourceProcessor):
    _shift: int = 0
    _break_line: int = 0

    def __init__(self):
        SourceProcessor.__init__(self)

    # For some reason clang doesn't parse u* and vector types so it needs a little help
    def _prepare(self):
        line_insertions = []
        # a) u* types
        line_insertions.extend([f'typedef unsigned {t} u{t};' for t in ClTypes.signed_integer_types])
        # b) vector types.
        for t in ClTypes.vector_base:
            for n in ClTypes.vector_len:
                line_insertions.append(f'typedef {t} {t}{n} __attribute__((ext_vector_type({n})));')
        # 1. Insert
        lines = self._code.split('\n')
        lines = line_insertions + lines[:]
        self._code = '\n'.join(lines)
        # 2. Shift
        self._shift = len(line_insertions)
        self._break_line += self._shift

    def _defuse(self):
        # Shift back
        lines = self._code.split('\n')
        self._code = '\n'.join(lines[self._shift:])
