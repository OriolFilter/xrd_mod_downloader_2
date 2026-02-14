from textual.app import App, ComposeResult, Binding
from textual.widgets import Footer, Label, Markdown, TabbedContent, TabPane
from ListModsView import AppDataTable
from Config import GlobalConfig
from modManagerView import ModManagerView

LETO = """
# Duke Leto I Atreides

Head of House Atreides.
"""

JESSICA = """
# Lady Jessica

Bene Gesserit and concubine of Leto, and mother of Paul and Alia.
"""

PAUL = """
# Paul Atreides

Son of Leto and Jessica.
"""

# TABNAMES = [
#     "Toggle Mod Display",
#     "Display Mods Info",
#     "Download/Update mods",
#     "Patch mods",  # Install etc
#     # "Launch mods", # Execute/launch # IDK
# ]

globalConfig = GlobalConfig()


class TabbedApp(App):
    tabs_menu: TabbedContent
    """An example of tabbed content."""

    BINDINGS = [
        Binding("a", "previous_tab", "Previous tab", show=True,
                # priority=True
                ),
        Binding("right", "next_tab", "Next tab", show=True,
                # priority=True
                ),
    ]

    def compose(self) -> ComposeResult:
        """Compose app with tabbed content."""
        # Footer to show keys
        yield Footer()

        # Add the TabbedContent widget
        self.tabs_menu = TabbedContent(initial="mods_info")
        with self.tabs_menu:
            with TabPane("Display Mods Info", id="mods_info"):  # First tab
                # yield AppDataTable(zebra_stripes=True, cursor_type="row", config=globalConfig)
                yield ModManagerView(zebra_stripes=True, config=globalConfig, cursor_type="row")
                # yield ModManagerView(zebra_stripes=True, cursor_type="row", config=globalConfig)
                # yield Markdown(LETO)  # Tab content
            # with TabPane("Toggle Mod Display", id="toggle_mods_display"):
            #     yield Markdown(JESSICA)

            with TabPane("Download/Update mods", id="download_mods"):
                yield Markdown(PAUL)
                with TabbedContent("Paul", "Alia"):
                    yield TabPane("Paul", Label("First child"))
                    yield TabPane("Alia", Label("Second child"))
            with TabPane("Patch mods", id="patch_mods"):
                yield Markdown(PAUL)

    # def action_next_tab(self):
    #     TabbedContent.prev

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab
        # self.get_child_by_type(TabbedContent).focus(false)


if __name__ == "__main__":
    app = TabbedApp()
    app.run(inline=True)
