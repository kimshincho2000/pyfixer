import os
import tempfile
import unittest
import json
import shutil
from pyfixer.core import (
    find_py_files,
    check_syntax,
    fix_syntax_content,
    try_fix,
    scan,
    _balance_brackets_in_line,
    _fix_condition_assignment,
    _fix_py2_print,
    _fix_colon_in_header,
)


class TestPyFixerCore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_find_py_files(self):
        f1 = os.path.join(self.test_dir, "test1.py")
        f2 = os.path.join(self.test_dir, "test2.txt")
        git_dir = os.path.join(self.test_dir, ".git")
        os.makedirs(git_dir)
        f3 = os.path.join(git_dir, "ignore.py")

        with open(f1, "w") as f: f.write("print('ok')")
        with open(f2, "w") as f: f.write("text")
        with open(f3, "w") as f: f.write("print('ignored')")

        py_files = find_py_files(self.test_dir)
        self.assertIn(f1, py_files)
        self.assertNotIn(f2, py_files)
        self.assertNotIn(f3, py_files)

    def test_check_syntax_valid(self):
        file_path = os.path.join(self.test_dir, "valid.py")
        with open(file_path, "w") as f:
            f.write("def foo():\n    return 42\n")
        self.assertIsNone(check_syntax(file_path))

    def test_check_syntax_invalid(self):
        file_path = os.path.join(self.test_dir, "invalid.py")
        with open(file_path, "w") as f:
            f.write("def foo(\n    return 42\n")
        err = check_syntax(file_path)
        self.assertIsNotNone(err)
        self.assertEqual(err["file"], file_path)
        self.assertTrue(">>>" in err["snippet"])

    def test_bracket_balancer(self):
        self.assertEqual(_balance_brackets_in_line("print('salom'"), "print('salom')")
        self.assertEqual(_balance_brackets_in_line("data = [1, 2, 3"), "data = [1, 2, 3]")
        self.assertEqual(_balance_brackets_in_line("d = {'a': 1"), "d = {'a': 1}")

    def test_condition_assignment(self):
        self.assertEqual(_fix_condition_assignment("if x = 10:"), "if x == 10:")
        self.assertEqual(_fix_condition_assignment("elif y = 'test':"), "elif y == 'test':")
        self.assertEqual(_fix_condition_assignment("if x == 10:"), "if x == 10:")

    def test_py2_print(self):
        self.assertEqual(_fix_py2_print("print 'salom'"), "print('salom')")
        self.assertEqual(_fix_py2_print("    print x, y"), "    print(x, y)")
        self.assertEqual(_fix_py2_print("print('salom')"), "print('salom')")

    def test_colon_in_header(self):
        self.assertEqual(_fix_colon_in_header("def add(a, b)"), "def add(a, b):")
        self.assertEqual(_fix_colon_in_header("if condition"), "if condition:")
        self.assertEqual(_fix_colon_in_header("else"), "else:")
        self.assertEqual(_fix_colon_in_header("def add(a, b):"), "def add(a, b):")

    def test_fix_syntax_content_full(self):
        broken = (
            "def hisobla(a, b)\n"
            "    if a = 5\n"
            "        print('a teng 5'\n"
            "    return a + b\n"
        )
        fixed = fix_syntax_content(broken)
        self.assertIsNotNone(fixed)
        import ast
        tree = ast.parse(fixed)
        self.assertIsNotNone(tree)

    def test_try_fix_with_backup(self):
        file_path = os.path.join(self.test_dir, "broken.py")
        broken_code = "def salom()\n    print('salom'\n"
        with open(file_path, "w") as f:
            f.write(broken_code)

        success = try_fix(file_path, backup=True)
        self.assertTrue(success)

        # Check .bak file exists
        bak_file = f"{file_path}.bak"
        self.assertTrue(os.path.exists(bak_file))
        with open(bak_file, "r") as f:
            self.assertEqual(f.read(), broken_code)

        # Check fixed file syntax
        self.assertIsNone(check_syntax(file_path))

    def test_scan_creates_json_report(self):
        file_path = os.path.join(self.test_dir, "err.py")
        with open(file_path, "w") as f:
            f.write("def x(\n")
        report_file = os.path.join(self.test_dir, "report.json")
        errors = scan(self.test_dir, output_json=report_file)
        self.assertEqual(len(errors), 1)
        self.assertTrue(os.path.exists(report_file))

        with open(report_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data["error_count"], 1)
        self.assertEqual(data["errors"][0]["file"], os.path.abspath(file_path))


if __name__ == "__main__":
    unittest.main()
