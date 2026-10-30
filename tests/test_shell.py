"""Unit tests for command interpretation and script execution."""

import io
import tempfile
import unittest
from pathlib import Path

from src.shell import Shell
from src.vfs import VirtualFileSystem


CSV = """path,type,content_base64
/docs,dir,
/docs/a.txt,file,SGVsbG8=
/docs/deep,dir,
/docs/deep/b.txt,file,AAEC
"""


class VFSTests(unittest.TestCase):
    def setUp(self):
        self.vfs = VirtualFileSystem()
        self.vfs.load(io.StringIO(CSV))

    def test_files_and_nested_levels(self):
        self.assertEqual(self.vfs.list_dir("/"), ["docs"])
        self.assertEqual(self.vfs.list_dir("/docs"), ["a.txt", "deep"])
        self.assertEqual(self.vfs.get("/docs/a.txt").content, b"Hello")
        self.assertEqual(self.vfs.get("/docs/deep/b.txt").content, b"\x00\x01\x02")

    def test_normalization(self):
        self.assertEqual(self.vfs.normalize("../deep/./b.txt", "/docs"), "/deep/b.txt")
        self.assertEqual(self.vfs.normalize("../../../", "/docs"), "/")

    def test_invalid_parent(self):
        with self.assertRaises(ValueError):
            VirtualFileSystem().load(io.StringIO("path,type,content_base64\n/a/b,file,\n"))

    def test_invalid_base64(self):
        with self.assertRaises(ValueError):
            VirtualFileSystem().load(io.StringIO("path,type,content_base64\n/a,file,%%%\n"))


class ShellTests(unittest.TestCase):
    def setUp(self):
        vfs = VirtualFileSystem()
        vfs.load(io.StringIO(CSV))
        self.out = io.StringIO()
        self.err = io.StringIO()
        self.shell = Shell(vfs, prompt="test$ ", output=self.out, error=self.err)

    def test_cd_and_ls(self):
        self.assertTrue(self.shell.execute("ls"))
        self.assertTrue(self.shell.execute("cd docs"))
        self.assertTrue(self.shell.execute("ls deep"))
        self.assertEqual(self.shell.cwd, "/docs")
        self.assertIn("b.txt", self.out.getvalue())

    def test_errors(self):
        self.assertFalse(self.shell.execute("unknown"))
        self.assertFalse(self.shell.execute("cd /missing"))
        self.assertFalse(self.shell.execute("cd /docs/a.txt"))
        self.assertFalse(self.shell.execute("ls /missing"))
        self.assertFalse(self.shell.execute("ls 'unclosed"))
        self.assertFalse(self.shell.execute("cd one two"))
        self.assertIn("parse error", self.err.getvalue())

    def test_exit(self):
        self.assertFalse(self.shell.execute("exit 1"))
        self.assertTrue(self.shell.running)
        self.assertTrue(self.shell.execute("exit"))
        self.assertFalse(self.shell.running)

    def test_script_stops_on_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "script.sh"
            path.write_text("ls\ncd docs\nnot_a_command\ncd deep\n", encoding="utf-8")
            self.assertFalse(self.shell.run_script(path))
        self.assertEqual(self.shell.cwd, "/docs")
        self.assertIn("test$ not_a_command", self.out.getvalue())
        self.assertNotIn("test$ cd deep", self.out.getvalue())

    def test_script_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "script.sh"
            path.write_text("exit\nunknown\n", encoding="utf-8")
            self.assertTrue(self.shell.run_script(path))
        self.assertFalse(self.shell.running)
        self.assertNotIn("unknown", self.err.getvalue())


if __name__ == "__main__":
    unittest.main()
