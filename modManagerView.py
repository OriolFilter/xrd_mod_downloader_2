from rich.text import TextType, Text
from textual.app import App, ComposeResult, Binding
from textual.widgets import DataTable

from Config import GlobalConfig
from modClasses import AppStruct
from textual import log


class ModManagerView(DataTable):
    config: GlobalConfig
    # table_struct: {str: {str: str}} = None

    __column_fields: {str: str} = None

    BINDINGS = [
        Binding("u", "update", "u", show=True, priority=True),
    ]

    # { field/key: display_name }

    def __init__(self, config: GlobalConfig, *args, **kwargs):
        self.config = config

        self.__column_fields = {
            "app_name": "AppName",
            "tag_name": "Current Version",
            "latest_version_available": "Latest Version Available",  # Or Up to date
            "patched": "Patched",
        }
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        # Add columns
        for key, column in self.__column_fields.items():
            print(f"key {key}")
            print(f"column {column}")
            self.add_column(Text(str(column)), key=key, default='----')

        # Add rows
        for mod in self.config.mod_list:
            mod: AppStruct
            self.add_row(
                *(),
                key=mod.app_name,
                label=mod.app_name,
            )

        self.__update_set_values()

    def __action_update(self):
        pass

    def __update_set_values(self, columns: str | [str] = None, rows: str | [str] = None) -> None:
        if columns is str:
            columns = [columns]
        else:
            # get all keys
            # columns = self.rows.items()
            columns = [colkey.value for colkey in self.columns.keys()]
        # raise Exception(columns)
        if rows is str:
            rows = [rows]
        else:
            # get all keys
            rows = [rowkey.value for rowkey in self.rows.keys()]
        for row in rows:
            app = self.config.get_app(row)
            app_info = {
                "app_name": app.app_name,
                "tag_name": app.tag_name,
                "latest_version_available": "hi",
                "patched": "Not Patched",
            }

            # raise Exception(columns)
            for column in columns:
                self.update_cell(value=Text(app_info.get(column)), row_key=row, column_key=column)
