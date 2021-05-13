import typing
import clang


def filter_node_list_by_file(nodes: typing.Iterable[clang.cindex.Cursor], file_name: str) \
        -> typing.Iterable[clang.cindex.Cursor]:
    result = [n for n in nodes if n.location.file and n.location.file.name == file_name]
    return result


def filter_node_list_by_node_kind(nodes: typing.Iterable[clang.cindex.Cursor], kinds: list) \
        -> typing.Iterable[clang.cindex.Cursor]:
    result = [n for n in nodes if n.kind in kinds]
    return result


def filter_node_list_by_start_line(nodes: typing.Iterable[clang.cindex.Cursor], by_line: int) \
        -> typing.Iterable[clang.cindex.Cursor]:
    result = [n for n in nodes if n.extent.start.line <= by_line]
    return result
