#!/usr/bin/env python3
"""pyfixer CLI - Automatic Python syntax error detector and fixer."""
import argparse
import sys
import os
from pyfixer.core import run, scan, run_single


def main():
    parser = argparse.ArgumentParser(
        prog="pyfixer",
        description="🔍 Automatic Python syntax error detector and fixer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / Misollar:
  pyfixer .                          # scan current directory
  pyfixer ./myproject                # scan specific project folder
  pyfixer main.py                    # scan single file
  pyfixer ./myproject -y             # auto-fix without prompt
  pyfixer ./myproject --no-backup    # do not create .bak backup files
  pyfixer ./myproject -o report.json # custom JSON report output
  pyfixer ./myproject --no-fix       # inspect only without fixing
        """
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Target folder or .py file (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        default="pyfix_report.json",
        metavar="FILE",
        help="Path to JSON report output (default: pyfix_report.json)"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Automatically fix errors without interactive confirmation"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not save .bak backup copies before modifying files"
    )
    parser.add_argument(
        "--no-fix",
        action="store_true",
        help="Only report syntax errors without attempting fixes"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="pyfixer 0.1.0"
    )

    args = parser.parse_args()
    path = args.path
    backup = not args.no_backup

    try:
        # Single file
        if os.path.isfile(path):
            if not path.endswith('.py'):
                print(f"❌ Xato: '{path}' Python fayli emas (.py kerak)!")
                sys.exit(1)
            ok = run_single(
                path,
                output_json=args.output,
                fix=not args.no_fix,
                auto_confirm=args.yes,
                backup=backup
            )
            sys.exit(0 if ok else 1)

        # Directory
        elif os.path.isdir(path):
            if args.no_fix:
                errors = scan(path, args.output)
                if errors:
                    print(f"\n❌ {len(errors)} ta xato topildi. To'liq hisobot: {args.output}")
                    for err in errors:
                        rel = os.path.relpath(err['file'])
                        print(f"  • {rel}:{err['line']} — {err['message']}")
                    sys.exit(1)
                else:
                    print("✅ Hech qanday xato topilmadi!")
                    sys.exit(0)
            else:
                ok = run(
                    path,
                    output_json=args.output,
                    auto_confirm=args.yes,
                    backup=backup
                )
                sys.exit(0 if ok else 1)

        else:
            print(f"❌ Xato: '{path}' fayl yoki papka topilmadi!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Jarayon to'xtatildi.")
        sys.exit(130)


if __name__ == "__main__":
    main()
