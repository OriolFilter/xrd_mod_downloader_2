from modClasses import *
import os
import json


class GlobalConfig:
    mod_list: list[AppStruct]
    mod_dict: {
        'str': AppStruct
    } = {}

    def __init__(self):
        mod_list = [
            AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots", description="Hitbox/framedata viewer "
                                                                                             "mod"),
            AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots"),
            AppStruct(repo_name="GGXrdFasterLoadingTimes", repo_owner="kkots", enabled=True),
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

    @property
    def workdir(self) -> str:
        # return "/tmp/a"
        return os.getcwd()

    @property
    def xrd_folder(self) -> str:
        raise NotImplementedError

    @property
    def config_file_path(self):
        return f"{self.workdir}/config.json"
        # return f"{self.workdir}/config.json"

    def load_config(self):
        # Load default -> Merge differences
        # If exists -> load
        if os.path.exists(self.config_file_path) and os.path.isfile(self.config_file_path):
            # For app -> check if config says something and import fields
            pass

        # If doesn't -> Load default
        raise NotImplementedError

    def save_config(self) -> bool:
        config_dict: {str: {str: str}} = {}

        # fields_to_export: [str] = ["tag_name","url_source_release"]
        for key, app in self.mod_dict.items():
            app: AppStruct
            app_config = {
                "tag_name": app.tag_name,
                "url_source_release": app.url_source_release,
                # automatically_patch: bool = None
                # patched: False,
                # enabled: False  # IDK
                # hidden: False
            }
            config_dict[key] = app_config

        with open(self.config_file_path, 'w+', encoding="utf-8") as file:
            file.write(json.dumps(config_dict))
        return True
