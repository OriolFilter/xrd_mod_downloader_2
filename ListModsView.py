from textual.app import App, ComposeResult
from textual.widgets import DataTable
from modClasses import AppStruct


class AppDataTable(DataTable):
    BINDINGS = [
        ("z", "z", "Z!")
    ]

    def on_mount(self) -> None:
        # Lists mods/current settings
        rows = [
            ("enabled", "mod_name")
        ]
        mod_list = [
            AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots"),
            AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
            AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots"),
            AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
            AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots"),
            AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
            AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots"),
            AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
            AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots"),
            AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
        ]

        for mod in mod_list:
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
