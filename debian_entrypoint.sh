#!/usr/bin/env bash
#pacman -Ssy
#pacman -S
python -m venv /tmp/venv
source /tmp/venv/bin/activate
pip3 install -r /requirements.txt
#OS="$(cat /etc/os-release | grep ^ID= | awk -F= '{print $2}')"
pyinstaller /src/main.py --distpath /tmp/ --clean -F --hidden-import "textual.widgets._tab_pane" --hidden-import "rich._unicode_data.unicode17-0-0" -n main
cp /tmp/main /binary_dump/main_linux -v
chown 1000:1000 -R /binary_dump
