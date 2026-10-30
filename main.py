"""CLI entry point for a UNIX-like shell emulator."""

import argparse
import sys

from src.shell import Shell
from src.vfs import VirtualFileSystem


def main(argv=None):
    parser = argparse.ArgumentParser(description="In-memory UNIX-like shell emulator")
    parser.add_argument("--vfs", help="path to a CSV virtual file system")
    parser.add_argument("--prompt", help="custom shell prompt string")
    parser.add_argument("--script", help="startup command script")
    args = parser.parse_args(argv)

    print("Configuration:")
    print(f"  VFS: {args.vfs if args.vfs is not None else '(empty in-memory VFS)'}")
    print(f"  Prompt: {args.prompt if args.prompt is not None else '(system default)'}")
    print(f"  Startup script: {args.script if args.script is not None else '(none)'}")
    try:
        vfs = VirtualFileSystem(args.vfs)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"VFS load error: {exc}", file=sys.stderr)
        return 1
    shell = Shell(vfs, prompt=args.prompt)
    if args.script and not shell.run_script(args.script):
        return 1
    if shell.running:
        shell.repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
