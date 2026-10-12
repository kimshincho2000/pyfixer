import ast
import os
import re
import json
import shutil
from datetime import datetime


def find_py_files(root_dir: str) -> list[str]:
    """Papkadagi barcha .py fayllarni topadi."""
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # .git, __pycache__, .venv papkalarini o'tkazib yuborish
        dirnames[:] = [d for d in dirnames if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.tox', '.pytest_cache'}]
        for filename in filenames:
            if filename.endswith('.py'):
                py_files.append(os.path.join(dirpath, filename))
    return py_files


def check_syntax(filepath: str) -> dict | None:
    """Bir fayldagi sintaksis xatoni aniqlaydi. Xato bo'lsa dict qaytaradi."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        ast.parse(source)
        return None  # Xato yo'q
    except SyntaxError as e:
        # Xato atrofidagi kodni ko'rsatish uchun
        lines = source.splitlines()
        lineno = e.lineno or 1
        start = max(0, lineno - 3)
        end = min(len(lines), lineno + 2)
        snippet = []
        for i, line in enumerate(lines[start:end], start=start + 1):
            marker = ">>>" if i == lineno else "   "
            snippet.append(f"{marker} {i:4d} | {line}")

        return {
            "file": filepath,
            "line": lineno,
            "col": e.offset,
            "message": str(e.msg),
            "text": e.text.rstrip() if e.text else "",
            "snippet": "\n".join(snippet),
        }


def _balance_brackets_in_line(line: str) -> str:
    """Qatorda ochilib yopilmay qolgan qavslar va tirnoqlarni yopadi."""
    code_part = line.split('#')[0].rstrip()
    comment_part = (' #' + line.split('#', 1)[1]) if '#' in line else ''

    stack = []
    in_single = in_double = False
    escaped = False

    for ch in code_part:
        if escaped:
            escaped = False
            continue
        if ch == '\\':
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if ch in '([{':
                stack.append(ch)
            elif ch in ')]}':
                if stack:
                    stack.pop()

    quote_closer = "'" if in_single else ('"' if in_double else '')
    mapping = {'(': ')', '[': ']', '{': '}'}
    bracket_closer = ''.join(mapping[c] for c in reversed(stack))
    return code_part + quote_closer + bracket_closer + comment_part


def _fix_condition_assignment(line: str) -> str:
    """if / elif shartlarida '=' o'rniga '==' qo'yadi."""
    pattern = r'^((\s*(?:if|elif)\s+.*?)(?<![!<>=])=(?!=)(.*))$'
    if re.match(pattern, line):
        eq_idx = line.find('=')
        return line[:eq_idx] + '==' + line[eq_idx + 1:]
    return line


def _fix_py2_print(line: str) -> str:
    """Python 2 uslubidagi 'print \"text\"' ni 'print(\"text\")' ga o'zgartiradi."""
    m = re.match(r'^(\s*)print\s+([^\(].*)$', line)
    if m:
        indent = m.group(1)
        content = m.group(2).rstrip()
        return f"{indent}print({content})"
    return line


def _fix_colon_in_header(line: str) -> str:
    """def, class, if, for va h.k. oxirida ':' tushib qolgan bo'lsa qo'yadi."""
    keywords = (
        'def ', 'class ', 'if ', 'elif ', 'else',
        'for ', 'while ', 'try', 'except', 'finally',
        'with ', 'async def ', 'async for ', 'async with '
    )
    code_part = line.split('#')[0].rstrip()
    comment_part = (' #' + line.split('#', 1)[1]) if '#' in line else ''
    stripped = code_part.strip()

    if any(stripped.startswith(k) or stripped == k for k in keywords) and not stripped.endswith(':'):
        return code_part + ':' + comment_part
    return line


def fix_syntax_content(source: str) -> str | None:
    """
    Python manba kodidagi keng tarqalgan sintaksis xatolarni tuzatishga urinadi.
    Agar tuzatish muvaffaqiyatli bo'lsa va ast.parse dan o'tsa yangi kodni qaytaradi.
    """
    # 0. Agar dastlabki kodning o'zi to'g'ri bo'lsa
    try:
        ast.parse(source)
        return source
    except SyntaxError:
        pass

    # 1. Tablarni 4 bo'shliqqa almashtirish
    code = source.replace('\t', '    ')
    try:
        ast.parse(code)
        return code
    except SyntaxError:
        pass

    # 2. Qatorlar bo'yicha tuzatishlar (qavslar, ikki nuqta, shart tengligi, print)
    lines = code.splitlines()
    new_lines = []
    for line in lines:
        l = _balance_brackets_in_line(line)
        l = _fix_colon_in_header(l)
        l = _fix_condition_assignment(l)
        l = _fix_py2_print(l)
        new_lines.append(l)

    candidate = '\n'.join(new_lines)
    if source.endswith('\n'):
        candidate += '\n'

    try:
        ast.parse(candidate)
        return candidate
    except SyntaxError:
        pass

    # 3. autopep8 orqali urinib ko'rish
    try:
        import autopep8
        formatted = autopep8.fix_code(candidate, options={'aggressive': 2})
        ast.parse(formatted)
        return formatted
    except Exception:
        pass

    try:
        import autopep8
        formatted = autopep8.fix_code(source, options={'aggressive': 2})
        ast.parse(formatted)
        return formatted
    except Exception:
        pass

    return None


def try_fix(filepath: str, backup: bool = True) -> bool:
    """Fayldagi sintaksis xatoni tuzatishga urinadi. Backup saqlash imkoni bor."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            original = f.read()

        fixed = fix_syntax_content(original)
        if fixed is None or fixed == original:
            return False

        # Zaxira nusxa yaratish
        if backup:
            shutil.copyfile(filepath, f"{filepath}.bak")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed)
        return True
    except Exception:
        return False


def scan(root_dir: str, output_json: str = "pyfix_report.json") -> list[dict]:
    """Barcha fayllarni skanerlab, xatolarni qaytaradi va JSON ga saqlaydi."""
    root_dir = os.path.abspath(root_dir)
    files = find_py_files(root_dir)
    errors = []

    print(f"\n🔍 Skanerlanmoqda: {root_dir}")
    print(f"   Jami .py fayllar: {len(files)}\n")

    for filepath in files:
        result = check_syntax(filepath)
        if result:
            errors.append(result)

    # JSON hisobot
    report = {
        "scanned_at": datetime.now().isoformat(),
        "root": root_dir,
        "total_files": len(files),
        "error_count": len(errors),
        "errors": errors,
    }
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return errors


def run(
    root_dir: str = ".",
    output_json: str = "pyfix_report.json",
    auto_confirm: bool = False,
    backup: bool = True
) -> bool:
    """
    Asosiy funksiya: skanerlash + ko'rsatish + tuzatish.
    Barcha xatolar bartaraf etilsa yoki xato bo'lmasa True, aks holda False qaytaradi.
    """
    errors = scan(root_dir, output_json)

    if not errors:
        print("✅ Hech qanday sintaksis xato topilmadi!\n")
        return True

    # Terminalda xatolarni chiqarish
    print(f"❌ {len(errors)} ta sintaksis xato topildi:\n")
    print("=" * 60)
    for i, err in enumerate(errors, 1):
        rel_path = os.path.relpath(err['file'])
        print(f"\n[{i}] 📄 {rel_path}  (satr: {err['line']}, ustun: {err['col']})")
        print(f"     💬 Xato: {err['message']}")
        print(f"     📝 Kod:")
        for line in err['snippet'].split('\n'):
            print(f"        {line}")
    print("\n" + "=" * 60)
    print(f"\n📋 To'liq hisobot saqlandi: {output_json}\n")

    if not auto_confirm:
        try:
            answer = input("🔧 Xatolarni avtomatik tuzatilsinmi? [yes/no]: ").strip().lower()
            proceed = answer in ('yes', 'y', 'ha', 'h')
        except (EOFError, KeyboardInterrupt):
            print("\nℹ️  Tuzatish bekor qilindi.")
            return False
    else:
        proceed = True

    if proceed:
        fixed_count = 0
        failed = []
        for err in errors:
            if try_fix(err['file'], backup=backup):
                fixed_count += 1
                bak_msg = " (.bak saqlandi)" if backup else ""
                print(f"  ✅ Tuzatildi{bak_msg}: {os.path.relpath(err['file'])}")
            else:
                failed.append(err['file'])
                print(f"  ❌ Tuzatib bo'lmadi: {os.path.relpath(err['file'])}")

        print(f"\n🎉 {fixed_count}/{len(errors)} ta fayl tuzatildi.")
        if failed:
            print(f"⚠️  {len(failed)} ta fayl qo'lda tuzatishni talab qiladi.")
            return False
        return True
    else:
        print("ℹ️  Tuzatish bekor qilindi. JSON hisobotdan foydalaning.")
        return False


def run_single(
    filepath: str,
    output_json: str = "pyfix_report.json",
    fix: bool = True,
    auto_confirm: bool = False,
    backup: bool = True
) -> bool:
    """Bitta .py faylni skanerlash + ko'rsatish + tuzatish."""
    filepath = os.path.abspath(filepath)
    err = check_syntax(filepath)

    report = {
        "scanned_at": datetime.now().isoformat(),
        "root": filepath,
        "total_files": 1,
        "error_count": 1 if err else 0,
        "errors": [err] if err else [],
    }
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    if not err:
        print(f"✅ {os.path.relpath(filepath)} — xato yo'q!\n")
        return True

    print(f"\n❌ Sintaksis xato topildi:\n")
    print("=" * 60)
    print(f"\n[1] 📄 {os.path.relpath(filepath)}  (satr: {err['line']}, ustun: {err['col']})")
    print(f"     💬 Xato: {err['message']}")
    print(f"     📝 Kod:")
    for line in err['snippet'].split('\n'):
        print(f"        {line}")
    print("\n" + "=" * 60)
    print(f"\n📋 To'liq hisobot saqlandi: {output_json}\n")

    if not fix:
        return False

    if not auto_confirm:
        try:
            answer = input("🔧 Xato avtomatik tuzatilsinmi? [yes/no]: ").strip().lower()
            proceed = answer in ('yes', 'y', 'ha', 'h')
        except (EOFError, KeyboardInterrupt):
            print("\nℹ️  Tuzatish bekor qilindi.")
            return False
    else:
        proceed = True

    if proceed:
        if try_fix(filepath, backup=backup):
            bak_msg = " (.bak saqlandi)" if backup else ""
            print(f"  ✅ Tuzatildi{bak_msg}: {os.path.relpath(filepath)}")
            return True
        else:
            print(f"  ❌ Tuzatib bo'lmadi — qo'lda tuzating.")
            return False
    else:
        print("ℹ️  Tuzatish bekor qilindi.")
        return False
