import time

from rich.text import TextType, Text
from textual.app import App, ComposeResult, Binding
from textual.widgets import DataTable

from Config import GlobalConfig
from modClasses import AppStruct
from textual import log

NO = Text("No", style="#a83a32 bold")
FALSE = NO
YES = Text("True", style="#32a852 bold")
TRUE = YES
UNKNOWN = Text("?", style="#d8db23 bold")


class ModManagerView(DataTable):
    config: GlobalConfig
    # table_struct: {str: {str: str}} = None

    __column_fields: {str: str} = None

    BINDINGS = [
        Binding("u", "update_to_latest", "update_to_latest", show=True, priority=True),
        Binding("p", "patch_app", "patch", show=True, priority=True),
        Binding("i", "search_updates", "search_updates", show=True, priority=True),
        Binding("s", "save_config", "save", show=True, priority=True),
        Binding("f", "download", "download_files", show=True, priority=True),
        # Binding("s", "search_updates", "s", show=True, priority=True),
    ]

    # { field/key: display_name }

    def __init__(self, config: GlobalConfig, *args, **kwargs):
        self.config = config
        self.__column_fields = {
            # "app_name": "AppName",
            "description": "Description",
            "patched": "Patched",
            "tag_name": "Current Version                   ",
            "latest_version_available": "Latest Version Available",  # Or Up to date
            "up_to_date": "Up To Date",
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
        # self.show_cursor = False

    # def action_search_updates_app(self):
    #     pass

    def action_save_config(self) -> bool:
        # self.show_cursor = False
        return self.config.save_config()

    def action_search_updates(self):
        row_pos = self.coordinate_to_cell_key(self.cursor_coordinate)[0]
        row_key = row_pos.value
        app = self.config.get_app(row_key)
        try:
            app.get_latest_release()
            self.__update_set_values(rows=row_key, columns=["latest_version_available"])
        except Exception as e:
            raise e

    def action_update_to_latest(self):
        row_pos = self.coordinate_to_cell_key(self.cursor_coordinate)[0]
        # {'value': 'kkots/GGXrdBackgroundGamepad'}
        row_key = row_pos.value
        app = self.config.get_app(row_key)
        # self.show_cursor = not self.show_cursor
        # TODO try except: show error window
        # TODO set rate limit
        try:
            app.update_to(release=app.get_latest_release())
            self.__update_set_values(rows=row_key, columns=["tag_name", "up_to_date"])

        except Exception as e:
            raise e

    def __update_set_values(self, columns: str | [str] = None, rows: str | [str] = None) -> None:
        if columns is str:
            columns = [columns]
        else:
            # get all keys
            columns = [colkey.value for colkey in self.columns.keys()]
        # raise Exception(columns)
        if rows is str:
            rows = [rows]
        else:
            # get all keys
            rows = [rowkey.value for rowkey in self.rows.keys()]
        for row in rows:
            app = self.config.get_app(row)
            # time.sleep(0.50)
            # latest_release = app.get_latest_release_available()
            # latest_release = "paco"

            app_info = {
                "app_name": app.app_name,
                "tag_name": app.tag_name,
                "latest_version_available": app.latest_release_name,
                # "latest_version_available": latest_release.name,
                "patched": (NO, TRUE)[app.patched],
                "description": app.description,
                "up_to_date": (NO, TRUE)[app.up_to_date]
            }

            for column in columns:
                # self.update_cell(value=Text(str("cell"), style="italic #03AC13", justify="right"), row_key=row, column_key=column)
                if app_info.get(column) is not Text:
                    self.update_cell(value=app_info.get(column), row_key=row, column_key=column)
                else:
                    self.update_cell(value=Text(app_info.get(column) or UNKNOWN), row_key=row, column_key=column)
