from modClasses import *


class GlobalConfig:
    mod_list: list[AppStruct]
    mod_dict: {
        'str': AppStruct
    } = {}

    def __init__(self):
        mod_list = [
            AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots", description="Hitbox/framedata viewer "
                                                                                             "mod"),
            # AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
            # AppStruct(repo_name="GGXrdFasterLoadingTimes", repo_owner="kkots", enabled=True),
            # AppStruct(repo_name="GGXrdMirrorColorSelect", repo_owner="kkots"),
            # AppStruct(repo_name="GGXrdBackgroundGamepad", repo_owner="kkots"),
            # AppStruct(repo_name="GGXrdReplayTakeover", repo_owner="ibrow19"),
        ]

        for mod in mod_list:
            mod: AppStruct
            # print(mod.app_name)
            if not mod.app_name in self.mod_dict:
                self.mod_dict[mod.app_name] = mod
                # print(self.mod_dict.get(mod.app_name).enabled)

    @property
    def mod_list(self) -> list[AppStruct]:
        for mod in self.mod_dict.values():
            mod: AppStruct
            yield mod

    def get_app(self, app_name: str) -> AppStruct:
        return self.mod_dict.get(app_name)
