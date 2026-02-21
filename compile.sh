#!/bin/bash
# Compile windows
pyinstaller main.py  --clean -F --paths venv/lib/python3.14/site-packages --hidden-import "textual.widgets._tab_pane" --hidden-import "rich._unicode_data.unicode17-0-0"

# Compile linux?
## Pass