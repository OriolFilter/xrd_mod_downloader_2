from modClasses import *


class GlobalConfig:
    mod_list: list[AppStruct]

    def __init__(self):
        self.mod_list = [
            AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots"),
            AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
            AppStruct(repo_name="GGXrdFasterLoadingTimes", repo_owner="kkots"),
            AppStruct(repo_name="GGXrdMirrorColorSelect", repo_owner="kkots"),
            AppStruct(repo_name="GGXrdBackgroundGamepad", repo_owner="kkots"),
            AppStruct(repo_name="GGXrdReplayTakeover", repo_owner="ibrow19"),
        ]
