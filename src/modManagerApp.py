import asyncio

from github.GitRelease import GitRelease
from rich.text import Text
from textual import work
from textual.app import App, ComposeResult, Binding
from textual.widgets import DataTable, Footer

from Config import GlobalConfig
from exceptions import XrdNotRunning
from modClasses import AppStruct

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
        Binding("u", "update_app_to_latest", "update_to_latest", show=True),
        # Binding("p", "patch_app", "patch", show=True, priority=True),
        # Binding("i", "search_updates", "search_updates", show=True, priority=True), # Checks on boot
        Binding("s", "save_config", "save", show=True),
        Binding("l", "launch_mod", "launch", show=True),
        Binding("p", "patch_mod", "patch", show=True),
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
            "installed": "Installed",
            "patched": "Auto Start",
            "tag_name": " Current ",
            "latest_version_available": " Latest ",  # Or Up to date
            "up_to_date": "Up To Date",
            "description": "Description",
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

    def action_launch_mod(self):
        app = self.selected_app
        app: AppStruct
        if not app.is_installed:
            self.notify(f"App {app.app_name} is not installed.\nInstall before launching.",
                        severity="warning")
        elif not app.can_be_launched():
            # TODO check if dotnet is required/is installed
            self.notify(f"Can't launch app {app.app_name}.\nEnsure the app is installed.",
                        severity="error")
        else:
            try:
                app.launch()
                self.notify(f"Launched {app.app_name}.", severity="information")
            except XrdNotRunning:
                self.notify(f"Can't launch app {app.app_name}.\nXrdApp is not running.",
                            severity="error")
            # except Exception as e:
            #     self.notify(f"Can't launch app {app.app_name}.\nError: {e}.",
            #                 severity="error")


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
        self.__update_app_to_release()

    @work(exclusive=True)
    async def __update_app_to_release(self, release: GitRelease = None):
        """
        Calls download and install methods from the app class.

        If no release is given, it will update to latest.

        Notify through the process.
        :return:
        """
        app = self.selected_app
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
            return 0

        # TODO Install step is useless. Remove
        self.notify("Download completed.\nStarting install step.", severity="information")
        async with asyncio.TaskGroup() as tg:
            install = tg.create_task(app.install_release(release=release))

        if not install.done():
            # No clue under which circumstances this would occur but whatever
            # TODO capture exceptions ?
            self.notify(f"Failed to download mod {app.app_name}", severity="error")
            return 0

        self.notify(f"Mod {app.app_name} installed.")

        self.__update_set_values(rows=app.app_name, columns=["tag_name", "up_to_date", "installed", "patched"])

    @work(exclusive=True)
    async def action_patch_mod(self):
        app = self.selected_app
        # if app.is_patched():

        if not app.is_installed:
            self.notify(f"Can't patch.\nApp not installed: {app.app_name}",
                        severity="warning")
        elif not app.is_patched:
            self.notify(f"Patching App: {app.app_name}",
                        severity="warning")

            async with asyncio.TaskGroup() as tg:
                patch = tg.create_task(app.patch())

            if not patch.done():
                # No clue under which circumstances this would occur but whatever
                # TODO capture exceptions ?
                self.notify(f"Failed to patch mod {app.app_name}!", severity="error")
                return 0
        else:
            self.notify(f"Unpatch App: {app.app_name}",
                        severity="warning")

            async with asyncio.TaskGroup() as tg:
                patch = tg.create_task(app.disable_patch())

            if not patch.done():
                # No clue under which circumstances this would occur but whatever
                # TODO capture exceptions ?
                self.notify(f"Failed to unpatch mod {app.app_name}!", severity="error")
                return 0

        self.notify(f"Mod {app.app_name} patched.")

        self.__update_set_values(rows=app.app_name, columns=["patched"])

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
            if app.tag_name and app.tag_name != app.latest_release_name:
                tag_name_message = Text(app.tag_name, style="#d8db23 bold")
            else:
                tag_name_message = Text(app.tag_name, style="#32a852")
            app_info = {
                "app_name": app.app_name,
                "tag_name": tag_name_message,
                "latest_version_available": app.latest_release_name,
                "installed": (NO, TRUE)[app.is_installed],
                "patched": (NO, TRUE)[app.is_patched],
                "description": app.description,
                "up_to_date": (NO, TRUE)[app.up_to_date]
            }

            for column in columns:
                # self.table.update_cell(value=Text(str("cell"), style="italic #03AC13", justify="right"), row_key=row, column_key=column)
                if app_info.get(column) is not Text:
                    self.table.update_cell(value=app_info.get(column), row_key=row, column_key=column)
                else:
                    self.table.update_cell(value=Text(app_info.get(column) or UNKNOWN), row_key=row, column_key=column)
