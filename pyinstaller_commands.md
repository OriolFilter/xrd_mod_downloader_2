# Compile pyinstaller (its bundling but w/e)

## Linux

pyinstaller main.py  --clean -F --paths venv/lib/python3.14/site-packages --hidden-import "textual.widgets._tab_pane" --hidden-import "rich._unicode_data.unicode17-0-0"

## Windows (?)

> Replace the path from --paths venv etc into the respective venv **after installing the requirements.txt**

pyinstaller main.py  --clean -F --paths venv/lib/python3.14/site-packages --hidden-import "textual.widgets._tab_pane" --hidden-import "rich._unicode_data.unicode17-0-0"  --nowindow





