from Config import GlobalConfig
from modManagerApp import ModManagerApp

if __name__ == "__main__":
    globalConfig = GlobalConfig()
    print(f"Found existing config? {globalConfig.load_config()}")
    if any(globalConfig.xrd_path):
        # print(f"Xrd Path? {globalConfig.xrd_path}")
        app = ModManagerApp(config=globalConfig)
        app.run(inline=True)
    else:
        print("Xrd Path couldn't be located.\n"
              "Easiest method to locate it is to have Xrd running when you execute this.")
