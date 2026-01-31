from textual.app import App, ComposeResult
from textual.widgets import DataTable
from modClasses import AppStruct

# Lists mods/current settings
ROWS = [
    ("enabled", "mod_name")
]
MOD_LIST = [
    AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots"),
    AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
]

print(MOD_LIST)
print(ROWS)

for mod in MOD_LIST:
    mod: AppStruct
    ROWS.append(
            (("[]", "[x]")[mod.enabled],
            mod.repo_name)
    )

print(ROWS)

class AppListMenu(App):
    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])


app = AppListMenu()
if __name__ == '__main__':
    app.run()
