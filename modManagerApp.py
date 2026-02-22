import asyncio
import time
from asyncio import Task
from os import system

from github.GitRelease import GitRelease
from rich.text import TextType, Text
from textual.app import App, ComposeResult, Binding
from textual.widgets import DataTable, Footer

from Config import GlobalConfig
from modClasses import AppStruct
from textual import log, work
from textual.widgets import LoadingIndicator

NO = Text("No", style="#a83a32 bold")
FALSE = NO
YES = Text("True", style="#32a852 bold")
TRUE = YES
UNKNOWN = Text("?", style="#d8db23 bold")


class ModManagerApp(App):
    config: GlobalConfig
    table: DataTable
    # table_struct: {str: {str: str}} = None

    __column_fields: {str: str} = None

    BINDINGS = [
        Binding("u", "update_app_to_latest", "update_to_latest", show=True, priority=True),
        # Binding("p", "patch_app", "patch", show=True, priority=True),
        # Binding("i", "search_updates", "search_updates", show=True, priority=True), # Checks on boot
        Binding("s", "save_config", "save", show=True, priority=True),
        # Binding("f", "download_latest", "download_latest", show=True, priority=True),
        # Binding("c", "change_version", "change_version", show=True, priority=True),
    ]

    # { field/key: display_name }
    @property
    def selected_app(self) -> AppStruct:
        row_pos = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)[0]
        # {'value': 'kkots/GGXrdBackgroundGamepad'}
        row_key = row_pos.value
        return self.config.get_app(row_key)

    def __init__(self, config: GlobalConfig, *args, **kwargs):
        self.config = config
        self.__column_fields = {
            # "app_name": "AppName",
            "description": "Description",
            "installed": "Installed",
            "patched": "Patched",
            "tag_name": " Current ",
            "latest_version_available": " Latest ",  # Or Up to date
            "up_to_date": "Up To Date",
        }

        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:

        # self.table.zebra_stripes = True
        # self.cursor_type = "row"
        # self.cursor_foreground_priority = "renderable"

        # Add columns
        for key, column in self.__column_fields.items():
            print(f"key {key}")
            print(f"column {column}")
            self.table.add_column(Text(str(column)), key=key, default='----')

        # Add rows
        for mod in self.config.mod_list:
            mod: AppStruct
            self.table.add_row(
                *(),
                key=mod.app_name,
                label=mod.app_name,
            )

        self.__update_set_values()
        # self.table.show_cursor = False

    # def action_search_updates_app(self):
    #     pass

    def compose(self) -> ComposeResult:
        # Footer to show keys
        self.table = DataTable(zebra_stripes=True, cursor_type="row",
                               cursor_foreground_priority="renderable",
                               # cursor_background_priority="renderable"
                               )
        self.table.styles.min_height = 10
        yield Footer()

        yield self.table

    def action_save_config(self) -> bool:
        # self.table.show_cursor = False
        return self.config.save_config()

    # def action_search_updates(self):
    #     app = self.selected_app
    #     try:
    #         _ = app.latest_release
    #         self.__update_set_values(rows=app.app_name, columns=["latest_version_available"])
    #     except Exception as e:
    #         raise e

    async def action_update_app_to_latest(self):
        # self.get_loading_widget()
        self.table.loading = True
        # with self.suspend():
        #     system("vim")
        # with self.suspend():
        # TODO try except: show error window
        # TODO set rate limit
        # self.run_worker(self.__update_app(self.selected_app), exclusive=True)
        self.__update_app_to_release(app=self.selected_app)

    @work(exclusive=True)
    async def __update_app_to_release(self, app: AppStruct, release: GitRelease = None):
        """
        Calls download and install methods from the app class.

        If no release is given, it will update to latest.

        Notify through the process.
        :return:
        """

        if release is None:
            release = app.latest_release
        # TODO check if its already download, skipp download if exists
        self.notify(f"Starting download.\nApp: {app.app_name}\nRelease: {release.name}",
                    severity="warning")
        async with asyncio.TaskGroup() as tg:
            download = tg.create_task(app.download_release(release=release))

        if not download.done():
            # No clue under which circumstances this would occur but whatever
            self.notify("Failed to download the mod!", severity="error")
            self.table.loading = False
            return 0
        self.notify("Download completed.\nStarting install step.", severity="information")

        async with asyncio.TaskGroup() as tg:
            install = tg.create_task(app.install_release(release=release))
        #
        # if not install.done():
        #     # No clue under which circumstances this would occur but whatever
        #     self.notify("Failed to download the mod!", severity="error")
        #     self.table.loading = False
        #     return 0

        self.notify(f"Mod {app.app_name} installed.")

        self.__update_set_values(rows=app.app_name, columns=["tag_name", "up_to_date", "installed", "patched"])
        self.table.loading = False

    # def action_patch_app(self):
    #     app = self.selected_app
    #     # TODO try except: show error window
    #     # TODO maybe skipp if already patched?
    #     if app.is_installed:
    #         try:
    #             app.patch()
    #             self.__update_set_values(rows=app.app_name, columns=["patched"])
    #
    #         except Exception as e:
    #             raise e

    # def action_download_latest(self):
    #     app = self.selected_app
    #     app.download_release(app.latest_release)

    def __update_set_values(self, columns: str | [str] = None, rows: str | [str] = None) -> None:
        if columns is str:
            columns = [columns]
        else:
            # get all keys
            columns = [colkey.value for colkey in self.table.columns.keys()]
        # raise Exception(columns)
        if rows is str:
            rows = [rows]
        else:
            # get all keys
            rows = [rowkey.value for rowkey in self.table.rows.keys()]
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
                "installed": (NO, TRUE)[app.is_installed],
                # "patched": (NO, TRUE)[app.is_patched],
                "description": app.description,
                "up_to_date": (NO, TRUE)[app.up_to_date]
            }

            for column in columns:
                # self.table.update_cell(value=Text(str("cell"), style="italic #03AC13", justify="right"), row_key=row, column_key=column)
                if app_info.get(column) is not Text:
                    self.table.update_cell(value=app_info.get(column), row_key=row, column_key=column)
                else:
                    self.table.update_cell(value=Text(app_info.get(column) or UNKNOWN), row_key=row, column_key=column)
