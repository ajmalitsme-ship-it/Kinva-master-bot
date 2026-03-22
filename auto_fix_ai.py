import os
import re
import sys

PROJECT_ROOT = "src"

# ---------- CONFIG ----------
AUTO_CREATE_STUB = True   # create function if not found
UPDATE_INIT = True        # add to __init__.py
# ----------------------------


def scan_python_files():
    py_files = []
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files


def find_function(func_name):
    for file in scan_python_files():
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            if re.search(rf"def\s+{func_name}\s*\(", content):
                return file
    return None


def add_to_init(file_path, func_name):
    dir_path = os.path.dirname(file_path)
    init_file = os.path.join(dir_path, "__init__.py")

    module = os.path.basename(file_path).replace(".py", "")

    if not os.path.exists(init_file):
        open(init_file, "w").close()

    with open(init_file, "a", encoding="utf-8") as f:
        f.write(f"\nfrom .{module} import {func_name}\n")

    print(f"[✔] Added {func_name} to {init_file}")


def create_stub(file_path, func_name):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"\n\ndef {func_name}(*args, **kwargs):\n")
        f.write("    print('⚠️ Auto-created stub function')\n")
        f.write("    return None\n")

    print(f"[⚠] Created stub for {func_name} in {file_path}")


def extract_missing_imports(log_text):
    pattern = r"cannot import name '(\w+)' from '([\w\.]+)'"
    return re.findall(pattern, log_text)


def fix_missing_import(func_name, module_path):
    print(f"\n🔍 Fixing: {func_name} from {module_path}")

    found_file = find_function(func_name)

    if found_file:
        print(f"[✔] Found in {found_file}")

        if UPDATE_INIT:
            add_to_init(found_file, func_name)

    else:
        print(f"[✘] Not found: {func_name}")

        if AUTO_CREATE_STUB:
            # create in utils as fallback
            fallback = os.path.join(PROJECT_ROOT, "utils", "auto_generated.py")
            os.makedirs(os.path.dirname(fallback), exist_ok=True)

            if not os.path.exists(fallback):
                open(fallback, "w").close()

            create_stub(fallback, func_name)

            if UPDATE_INIT:
                add_to_init(fallback, func_name)


def auto_fix_from_log(log_text):
    errors = extract_missing_imports(log_text)

    if not errors:
        print("✅ No import errors found")
        return

    for func_name, module_path in errors:
        fix_missing_import(func_name, module_path)


# ---------- MAIN ----------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_fix_ai.py error.log")
        sys.exit(1)

    log_file = sys.argv[1]

    with open(log_file, "r", encoding="utf-8") as f:
        logs = f.read()

    auto_fix_from_log(logs)
