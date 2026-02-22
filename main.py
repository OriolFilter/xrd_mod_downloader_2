from textual.app import App, ComposeResult, Binding
from textual.widgets import Footer, Label, Markdown, TabbedContent, TabPane
from Config import GlobalConfig
from modManagerApp import ModManagerApp
import textual

if __name__ == "__main__":
    globalConfig = GlobalConfig()
    print(f"Found existing config? {globalConfig.load_config()}")
    app = ModManagerApp(config=globalConfig)
    print(app.debug)
    app.run(inline=True)
