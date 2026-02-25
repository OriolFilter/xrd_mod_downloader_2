from Config import GlobalConfig
from modManagerApp import ModManagerApp

if __name__ == "__main__":
    globalConfig = GlobalConfig()
    # print("Xrd folder {}".format(globalConfig.xrd_path))
    print(f"Found existing config? {globalConfig.load_config()}")
    app = ModManagerApp(config=globalConfig)
    # print(app.debug)
    app.run(inline=True)
