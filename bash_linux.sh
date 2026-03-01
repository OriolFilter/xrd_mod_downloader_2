#!/usr/bin/env ash
pip3 install -r /requirements.txt
apk add binutils
pyinstaller /src/main.py --distpath /dataout/ --clean -F --hidden-import "textual.widgets._tab_pane" --hidden-import "rich._unicode_data.unicode17-0-0"
chown 1000:1000 -R /dataout/main