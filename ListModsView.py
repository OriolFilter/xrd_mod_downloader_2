from rich.text import TextType, Text
from textual.app import App, ComposeResult, Binding
from textual.widgets import DataTable

from Config import GlobalConfig
from modClasses import AppStruct
from textual import log


class AppDataTable(DataTable):
    cursor_type = "row"
    config: GlobalConfig
    BINDINGS = [
        ("z", "z", "Z!"),
        Binding("space", "toggle_display", "Toggle Display", show=True, priority=True),
        # Binding("right", "next_tab", "Next tab", show=True, priority=True),
        Binding("right", "next_tab", "Next tab", show=True, priority=False),
    ]

    def __init__(self, config: GlobalConfig, *args, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        # Lists mods/current settings
        columns = (
            "enabled",
            # "mod_name"
        )
        for column in columns:
            print(column)
            self.add_column(Text(str(column)))
            pass
        rows = []
        for mod in self.config.mod_list:
            mod: AppStruct
            self.add_row(
                *((Text("True", style="#32a852"), Text("False", style="#a83a32"))[mod.enabled],
                  # mod.repo_name
                  )
                ,
                key=mod.app_name,
                label=mod.app_name,
            )
            rows.append(
                (("[]", "[x]")[mod.enabled],
                 mod.repo_name)
            )

        # # table = self.query_one(DataTable)
        # self.add_columns(*rows[0])
        # self.add_rows(rows[1:])
        self.focus()

    def action_z(self) -> None:
        # self.add_row("[]", "z")
        self.add_row("[]")
        # self.parent

    def action_toggle_display(self) -> None:
        row_pos = self.coordinate_to_cell_key(self.cursor_coordinate)[0]
        # {'value': 'kkots/GGXrdBackgroundGamepad'}
        row_key = row_pos.value
        self.config.get_app(row_key).enabled = not self.config.get_app(row_key).enabled
        mod = self.config.get_app(row_key)
        # TODO update rows
        # self.add_row(
        #     *((Text("True", style="#32a852"), Text("False", style="#a83a32"))[mod.enabled],
        #       # mod.repo_name
        #       )
        #     ,
        #     key=f"{mod.app_name}2",
        #     label=f"{mod.app_name}2",
        # )
        # self.remove_row(row_key=row_key)
