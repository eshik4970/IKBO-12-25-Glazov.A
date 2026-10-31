"""Interactive command interpreter and startup-script runner."""

import getpass
import shlex
import socket
import sys
from pathlib import Path

from .vfs import VirtualFileSystem


class Shell:
    """A small subset of a UNIX shell that only accesses an in-memory VFS."""

    def __init__(self, vfs, prompt=None, output=None, error=None):
        self.vfs = vfs
        self.cwd = "/"
        self.prompt_override = prompt
        self.output = output if output is not None else sys.stdout
        self.error = error if error is not None else sys.stderr
        self.running = True

    def prompt(self):
        if self.prompt_override is not None:
            return self.prompt_override
        return f"{getpass.getuser()}@{socket.gethostname()}:{self.cwd}$ "

    def execute(self, line):
        """Execute one command; report errors without terminating REPL."""
        try:
            args = shlex.split(line, posix=True)
        except ValueError as exc:
            print(f"shell: parse error: {exc}", file=self.error)
            return False
        if not args:
            return True
        name, *parameters = args
        if name == "exit":
            return self._exit(parameters)
        if name == "cd":
            return self._cd(parameters)
        if name == "ls":
            return self._ls(parameters)
        print(f"{name}: command not found", file=self.error)
        return False

    def _exit(self, parameters):
        """Exit the emulator when no unexpected arguments were given."""
        if parameters:
            print("exit: too many arguments", file=self.error)
            return False
        self.running = False
        return True

    def _cd(self, parameters):
        """Change the in-memory current directory."""
        if len(parameters) > 1:
            print("cd: too many arguments", file=self.error)
            return False
        destination = parameters[0] if parameters else "/"
        absolute = self.vfs.normalize(destination, self.cwd)
        entry = self.vfs.get(absolute)
        if entry is None:
            message = f"cd: {destination}: no such directory"
            print(message, file=self.error)
            return False
        if entry.kind != "dir":
            print(f"cd: {destination}: not a directory", file=self.error)
            return False
        self.cwd = absolute
        return True

    def _ls(self, parameters):
        """List immediate children of a virtual directory."""
        if len(parameters) > 1:
            print("ls: too many arguments", file=self.error)
            return False
        target = parameters[0] if parameters else "."
        try:
            entries = self.vfs.list_dir(target, self.cwd)
        except FileNotFoundError:
            message = f"ls: {target}: no such file or directory"
            print(message, file=self.error)
            return False
        print("  ".join(entries), file=self.output)
        return True

    def run_script(self, path):
        """Echo each command, stop on first error, and return its status."""
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    if not self.running:
                        break
                    line = line.rstrip("\r\n")
                    if not line.strip() or line.lstrip().startswith("#"):
                        continue
                    print(f"{self.prompt()}{line}", file=self.output)
                    self.output.flush()
                    if not self.execute(line):
                        return False
        except (OSError, UnicodeError) as exc:
            print(f"script: {exc}", file=self.error)
            return False
        return True

    def repl(self):
        while self.running:
            try:
                line = input(self.prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                break
            self.execute(line)
