from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Tabs, Label
from modClasses import AppStruct

TABNAMES = [
    "Toggle Mod Display",
    "Display Mods Info",
    "Download/Update mods",
    "Patch mods",  # Install etc
    # "Launch mods", # Execute/launch # IDK
]


class TabsApp(App):
    CSS = """
        Tabs {
            dock: top;
        }
        Screen {
            align: center middle;
        }
        Label {
            margin:1 1;
            width: 100%;
            height: 100%;
            background: $panel;
            border: tall $primary;
            content-align: center middle;
        }
        """

    def compose(self) -> ComposeResult:
        yield Tabs(*TABNAMES)
        yield Label()
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Tabs).focus()

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        label = self.query_one(Label)
        if event is None:
            # When the tabs are cleared, event.tab will be None
            label.visible = False
        else:
            label.visible = True
            label.update(event.tab.label)

    BINDINGS = [

        ("z", "zzz", "zzzz")

    ]

    def action_zzz(self) -> None:
        """zzz!"""
        tabs = self.query_one(Tabs)
        tabs.add_tab("ZZZ!")

if __name__ == "__main__":
    app = TabsApp()
    app.run()