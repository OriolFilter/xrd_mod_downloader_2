import json
import os

from github import Github

from modClasses import AppStruct, WakeUpTool


class GlobalConfig:
    mod_list: list[AppStruct]
    mod_dict: {
        'str': AppStruct
    } = {}
    github_client: Github

    def __init__(self):
        mod_list = [
            # AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots", description="Hitbox/framedata viewer "
            #                                                                                  "mod"),
            WakeUpTool(repo_name="rev2-wakeup-tool", repo_owner="kkots", _config=self),
            # ReplayTakeover(repo_name="GGXrdReplayTakeover", repo_owner="ibrow19", _config=self),
            # WakeUpTool(repo_name="rev2-wakeup-tool", repo_owner="Iquis", _config=self),
            # #Iquis would need to verify download differenlty

            # AppStruct(repo_name="GGXrdFasterLoadingTimes", repo_owner="kkots", _config=self),
            # AppStruct(repo_name="GGXrdMirrorColorSelect", repo_owner="kkots", _config=self),
            # AppStruct(repo_name="GGXrdBackgroundGamepad", repo_owner="kkots", _config=self),
        ]

        for mod in mod_list:
            mod: AppStruct
            # print(mod.app_name)
            if mod.app_name not in self.mod_dict:
                self.mod_dict[mod.app_name] = mod
                # print(self.mod_dict.get(mod.app_name).enabled)

        self.github_client = Github()

    @property
    def mod_list(self) -> list[AppStruct]:
        for mod in self.mod_dict.values():
            mod: AppStruct
            yield mod

    def get_app(self, app_name: str) -> AppStruct:
        return self.mod_dict.get(app_name, None)

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

    def load_config(self) -> bool:
        # Load default -> Merge differences
        # If exists -> load
        if os.path.exists(self.config_file_path) and os.path.isfile(self.config_file_path):
            # For app -> check if config says something and import fields
            user_config: {str: {str}} = None
            with open(self.config_file_path, 'r', encoding="utf-8") as user_file:
                user_config = json.loads(user_file.read())

            for app_name, app_values in user_config.items():
                app_name: str
                app_values: {str: str}
                app = self.get_app(app_name)
                app: AppStruct
                if app:
                    # with self.get_app(app_name) as app:
                    for key, value in app_values.items():
                        if hasattr(app, key):
                            app.__setattr__(key, value)
                        else:
                            print(f"> Field '{key}' for app {app_name} couldn't load due to not matching a variable. Skipping.")
                else:
                    print(f"> Config for app {app_name} couldn't load due to not matching any app by name. Skipping.")

            del app_name, app_values
            return True

        # If doesn't -> Load default
        return False
        # raise NotImplementedError

    def save_config(self) -> bool:
        config_dict: {str: {str: str}} = {}

        # fields_to_export: [str] = ["tag_name","url_source_release"]
        for key, app in self.mod_dict.items():
            app: AppStruct
            config_dict[key] = app.export_config_dict()
        with open(self.config_file_path, 'w+', encoding="utf-8") as file:
            file.write(json.dumps(config_dict))
        return True

    @property
    def app_download_path(self) -> str:
        return f"{self.workdir}/downloads"
