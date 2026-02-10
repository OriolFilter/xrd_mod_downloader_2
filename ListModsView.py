from textual.app import App, ComposeResult, Binding
from textual.widgets import DataTable

from Config import GlobalConfig
from modClasses import AppStruct


class AppDataTable(DataTable):
    config: GlobalConfig
    BINDINGS = [
        ("z", "z", "Z!"),
        # Binding("left", "previous_tab", "Previous tab", show=True, priority=True),
        # Binding("right", "next_tab", "Next tab", show=True, priority=True),
    ]

    def __init__(self, config: GlobalConfig, *args, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        # Lists mods/current settings
        rows = [
            ("enabled", "mod_name")
        ]

        for mod in self.config.mod_list:
            mod: AppStruct
            rows.append(
                (("[]", "[x]")[mod.enabled],
                 mod.repo_name)
            )

        # table = self.query_one(DataTable)
        self.add_columns(*rows[0])
        self.add_rows(rows[1:])
        self.focus()

    def action_z(self) -> None:
        self.add_row("[]", "z")
