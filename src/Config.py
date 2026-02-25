import json
import os

import psutil
from github import Github

from modClasses import AppStruct, WakeUpTool, HitboxOverlay
from exceptions import XrdFolderNotValid, XrdFolderNotFound


class GlobalConfig:
    mod_list: list[AppStruct]
    mod_dict: {
        'str': AppStruct
    } = {}
    github_client: Github

    __xrd_path: str = ""

    def __init__(self):
        # TODO
        # C++ redistrib
        # DotNet
        mod_list = [
            HitboxOverlay(repo_name="ggxrd_hitbox_overlay_2211",
                          repo_owner="kkots",
                          description="Hitbox/framedata viewer mod",
                          _config=self),
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
    def config_file_path(self):
        return f"{self.workdir}/config.json"
        # return f"{self.workdir}/config.json"

    def load_config(self) -> bool:
        # Load default -> Merge differences
        # If exists -> load
        if os.path.exists(self.config_file_path) and os.path.isfile(self.config_file_path):
            # For app -> check if config says something and import fields
            user_config: {str: str | {str: str}} = {}
            mods_info: {str: {str: str}} = {}

            with open(self.config_file_path, 'r', encoding="utf-8") as user_file:
                user_config = json.loads(user_file.read())

            if xrd_path := user_config.get("xrd_path"):
                self.xrd_path = xrd_path

            mods_info = user_config.get("mods_info", {})
            for app_name, app_values in mods_info.items():
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
                            print(
                                f"> Field '{key}' for app {app_name} couldn't load due to not matching a variable. Skipping.")
                else:
                    print(f"> Config for app {app_name} couldn't load due to not matching any app by name. Skipping.")
            return True

    def save_config(self) -> bool:
        config_dict: {str: str | {str: str}} = {}
        mods_dict: {str: {str: str}} = {}

        # fields_to_export: [str] = ["tag_name","url_source_release"]

        # Export mods info
        for key, app in self.mod_dict.items():
            app: AppStruct
            mods_dict[key] = app.export_config_dict()

        config_dict["mods_info"] = mods_dict
        config_dict["xrd_path"] = self.xrd_path
        # raise Exception(config_dict)
        # Write / Save
        with open(self.config_file_path, 'w+', encoding="utf-8") as file:
            file.write(json.dumps(config_dict))
        return True

    @property
    def app_download_path(self) -> str:
        return f"{self.workdir}/downloads"

    @staticmethod
    def __find_xrd_location_if_open() -> str:
        # 1. Find Xrd Process (if open)
        xrd_process = None
        for pid in psutil.process_iter():
            if pid.name() == "GuiltyGearXrd.exe":
                xrd_process = pid
                break
        del pid

        return xrd_process.environ().get("PWD")

    @staticmethod
    def __find_xrd_process_by_folders() -> str:
        # 2. Find Xrd by checking folders (only one path known right now on linux)
        steam_path = "{home_path}/.steam/root/config/libraryfolders.vdf"
        return ""

    @property
    def xrd_path(self) -> str:
        if self.__xrd_path:
            pass
        elif path := self.__find_xrd_location_if_open():
            self.xrd_path = path
        elif path := self.__find_xrd_process_by_folders():
            self.__xrd_path = path
        else:
            raise XrdFolderNotFound
        return self.__xrd_path

    @xrd_path.setter
    def xrd_path(self, path: str):
        if self.__check_xrd_path_is_valid(path):
            self.__xrd_path = path
        else:
            raise XrdFolderNotValid()

    @staticmethod
    def __check_xrd_path_is_valid(path: str) -> bool:
        """
        TODO idk check various things from the given path.
        :param path:
        :return:
        """
        return True
