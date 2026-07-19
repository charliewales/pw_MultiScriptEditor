import os

def read_file_text(path):
    """
    Safely read text from a file, trying multiple encodings and falling back gracefully.
    """
    if not os.path.exists(path):
        return ""

    # 1. Try utf-8-sig to automatically handle UTF-8 with BOM and normal UTF-8
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return f.read()
    except UnicodeDecodeError:
        pass

    # 2. Try utf-16 (covers UTF-16 LE and UTF-16 BE with BOM)
    try:
        with open(path, 'r', encoding='utf-16') as f:
            return f.read()
    except UnicodeDecodeError:
        pass

    # 3. Fallback to utf-8 with errors='replace' to avoid UnicodeDecodeError entirely
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception:
        pass

    # 4. Final fallback with default encoding and errors='replace'
    try:
        with open(path, 'r', errors='replace') as f:
            return f.read()
    except Exception:
        return ""
