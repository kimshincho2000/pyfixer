# pyfixer 🔍

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/pyfixer/)
[![Python versions](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**pyfixer** is a fast, safe, and automated Python syntax error detection and fixing CLI tool. Unlike traditional linters (`black`, `ruff`, `autopep8`) that fail and crash when encountering broken syntax, `pyfixer` detects the `SyntaxError`, inspects the surrounding context, and safely fixes common syntax mistakes while creating backup copies.

---

## ✨ Features / Imkoniyatlar

- 🛡️ **Safe AST Verification**: Every proposed fix is verified with `ast.parse` before touching your file.
- ⚡ **Auto-Fix Common Syntax Mistakes**:
  - Automatically appends missing colons (`:`) to `def`, `class`, `if`, `elif`, `else`, `for`, `while`, `try`, `except`, `with`.
  - Closes unclosed brackets (`()`, `[]`, `{}`) and unclosed string quotes (`'`, `"`).
  - Fixes assignment typos in condition headers (`if a = 5:` ➔ `if a == 5:`).
  - Migrates Python 2 print statements (`print "hello"` ➔ `print("hello")`).
  - Normalizes indentation and applies PEP 8 formatting via `autopep8`.
- 💾 **Automatic Backups**: Always saves `.bak` copies before altering files (can be bypassed with `--no-backup`).
- 🤖 **CI/CD Ready**: Supports `-y` / `--yes` non-interactive execution and standard exit codes (0 for success, 1 for remaining errors).
- 📊 **JSON Reports**: Generates detailed error logs in `pyfix_report.json`.

---

## 📦 Installation / O'rnatish

```bash
pip install pyfixer
```

Or install from source:

```bash
git clone https://github.com/kimshincho2000/pyfixer.git
cd pyfixer
pip install -e .
```

---

## 🚀 Usage / Ishlatish

### English

```bash
# Scan and fix a single file
pyfixer main.py

# Scan an entire directory
pyfixer ./myproject

# Non-interactive automatic fix (great for CI/CD)
pyfixer ./myproject -y

# Fix without creating .bak backup files
pyfixer ./myproject -y --no-backup

# Only report errors without fixing
pyfixer ./myproject --no-fix

# Custom report output path
pyfixer ./myproject -o custom_report.json
```

### O'zbekcha

```bash
# Bitta faylni tekshirish va tuzatish
pyfixer main.py

# Butun papkani skanerlash
pyfixer ./loyiham

# So'roqsiz avtomatik tuzatish
pyfixer ./loyiham -y

# .bak nusxasiz tuzatish
pyfixer ./loyiham -y --no-backup

# Faqat tekshirish (tuzatmasdan)
pyfixer ./loyiham --no-fix
```

---

## 🖥️ Terminal Preview

```
🔍 Skanerlanmoqda: /home/user/project
   Jami .py fayllar: 1

❌ 1 ta sintaksis xato topildi:

============================================================

[1] 📄 demo.py  (satr: 1, ustun: 15)
     💬 Xato: expected ':'
     📝 Kod:
        >>>    1 | def test(a, b)
               2 |     if a = 10
               3 |         print("Natija"

============================================================

📋 To'liq hisobot saqlandi: pyfix_report.json

  ✅ Tuzatildi (.bak saqlandi): demo.py
```

---

## 🧪 Testing

Run the test suite using `unittest`:

```bash
python3 -m unittest discover tests
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
