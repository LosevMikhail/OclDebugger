import argparse
import asyncio
import os
import sys
from logging import fatal, warning
from shutil import copyfile  # TODO: find out whether it works with Windows

from typing import List

from PrintfInserter import PrintfInserter
from primitives import VarDeclaration, Variable, ClTypes


class OclDebugger(object):
    _break_line: int = None
    _threads: [int] = None

    def __init__(self, kernel_file: str, binary: str, build_cmd: str):
        self._kernel_file = kernel_file
        self._binary = os.path.basename(binary)
        self._binary_dir = os.path.dirname(binary)
        # TODO: find out whether it works with Windows
        self._cmd = f'cd {self._binary_dir} && ./{self._binary}'
        self._build_cmd = build_cmd

    def safe_debug(self, break_line: int, threads: [int]):
        self._break_line = break_line
        self._threads = threads

        copyfile(self._kernel_file, 'kernel_backup')
        try:
            variables = self._debug()
        finally:
            copyfile('kernel_backup', self._kernel_file)
        return variables

    def _debug(self):
        kernel_processor = PrintfInserter(self._break_line, self._threads)
        with open(self._kernel_file, 'r') as source_kernel_file:
            kernel = kernel_processor.process_source(str(source_kernel_file.read()), 'cl')

        ClTypes.struct_declarations = kernel_processor.get_structs()

        with open(self._kernel_file, 'w') as kernel_file:
            kernel_file.write(kernel)
            kernel_file.close()

        with open('kernel.cl', 'w') as kernel_file:
            kernel_file.write(kernel)
            kernel_file.close()

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self._build())
        finally:
            # loop.run_until_complete(loop.shutdown_asyncgens())
            pass

        try:
            variables = loop.run_until_complete(self.process_values(kernel_processor.get_variables(),
                                                                    self.value_generator()))
            return variables
        finally:
            # see: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.shutdown_asyncgens
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            pass

    def _build_env(self) -> dict:
        env = os.environ.copy()

        dirs = env['PATH'].split(':')
        dirs[0] = self._binary_dir
        path = ':'.join(dirs)

        env['PATH'] = path
        env['PWD'] = self._binary_dir
        return env

    async def process_values(self, info: List[VarDeclaration], values):
        while True:
            try:
                if await values.__anext__() == PrintfInserter.get_magic_string():
                    break
            except StopAsyncIteration as e:
                fatal('No debugging data received')
                exit(-1)
        variables = []
        for t in self._threads:
            for i in info:
                v = await values.__anext__()
                variables.append(Variable(i, v, t))
        return variables

    async def _build(self):
        if self._build_cmd is not None:
            env = self._build_env()
            create = asyncio.create_subprocess_exec(self._build_cmd, env=env,
                                                     stdin=asyncio.subprocess.PIPE,
                                                     stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.STDOUT)
            try:
                proc = await create
            except Exception as e:
                fatal(f'Could not execute {self._binary}')

    async def value_generator(self):
        env = self._build_env()
        create = asyncio.create_subprocess_shell(self._cmd, env=env,
                                                 stdin=asyncio.subprocess.PIPE,
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.STDOUT)
        try:
            proc = await create
        except FileNotFoundError as e:
            warning(f'Could not find {self._binary};')
            exit(-1)
        except Exception as e:
            fatal(f'Could not execute {self._binary}')

        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            line = line.decode('ascii').rstrip()
            yield line


def main():
    parser = argparse.ArgumentParser(prog='OclDebugger.py')
    parser.add_argument('-k', '--kernel', help='<Required> Kernel file location', required=True)
    parser.add_argument('-a', '--application', help='<Required> Target application location', required=True)
    parser.add_argument('--build', help='<Optional> build command if needed', type=str, required=False)
    parser.add_argument('-b', '--breakpoint', help='<Required> Breakpoint', type=int, required=True)
    parser.add_argument('-t', '--threads', nargs='+', help='<Required> Target threads (global ids)', type=int, required=True)
    args = parser.parse_args()

    debugger = OclDebugger(
        kernel_file=args.kernel,
        binary=args.application,
        build_cmd=args.build
    )

    variables = debugger.safe_debug(break_line=args.breakpoint, threads=args.threads)
    for v in variables:
        print(v)


if __name__ == '__main__':
    exit(main())
