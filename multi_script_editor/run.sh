#!/bin/bash
CURRENT=`dirname $(readlink -f $0)`
PYTHON_BIN="${PYTHON:-}"

if [ -z "$PYTHON_BIN" ]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN=python3
    else
        PYTHON_BIN=python
    fi
fi

exec "$PYTHON_BIN" "$CURRENT/scriptEditor.py"
