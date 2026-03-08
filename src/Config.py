import json
import os
import sys
from pathlib import Path

import psutil
from github import Github

from appBase import AppStruct
from appExpanded import *
from exceptions import XrdFolderNotValid, XrdFolderNotFound


class GlobalConfig:
    mod_list: list[AppStruct]
    mod_dict: {
        'str': AppStruct
    } = {}
    github_client: Github

    __xrd_path: str = ""

    def __init__(self):
        mod_list = [
            DotNet(repo_owner="Microsoft", repo_name=".Net 6", _config=self,
                        description="Required to launch the Reversal Tool"),
            HitboxOverlay(repo_name="ggxrd_hitbox_overlay_2211",
                           repo_owner="kkots",
                           description="Hitbox/framedata viewer mod",
                           _config=self),
            # WakeUpTool(repo_name="rev2-wakeup-tool", repo_owner="kkots", _config=self),
            # ReplayTakeover(repo_name="GGXrdReplayTakeover", repo_owner="ibrow19", _config=self),
            # WakeUpTool(repo_name="rev2-wakeup-tool", repo_owner="Iquis", _config=self),
            # #Iquis would need to verify download differenlty

            # AppStruct(repo_name="GGXrdFasterLoadingTimes", repo_owner="kkots", _config=self),
            # AppStruct(repo_name="GGXrdMirrorColorSelect", repo_owner="kkots", _config=self),
            # AppStruct(repo_name="GGXrdBackgroundGamepad", repo_owner="kkots", _config=self),
            # GGXrdChangeBorderlessWindowPos idk about this one
            # https://github.com/kkots/GGXrdAutomaticallyChangeAudioDevice
            # https://github.com/kkots/GGXrdDisplayPing
            # https://github.com/kkots/GGXrdAdjustConnectionTiers  idk about this one
        ]

        match sys.platform:
            case 'linux':
                pass
            case "win32":
                from sys import maxsize
                if maxsize > 2 ** 32:
                    # VsRedistribute only works for x64 devices
                    mod_list.append(
                        VsRedistributable64(repo_owner="Microsoft", repo_name="VsCppRedist_x64", _config=self,
                                            description="Required to launch most mods."))
                # TODO Probably unused if x64 exists.
                mod_list.append(
                    VsRedistributable86(repo_owner="Microsoft", repo_name="VsCppRedist_x86", _config=self,
                                        description="Required to launch most mods."))
            case _:
                pass

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

        # fields_to_export: [str] = ["_tag_name"]

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
        if xrd_process:
            match sys.platform:
                case 'linux':
                    return xrd_process.environ().get("PWD")
                case "win32":
                    return xrd_process.exe().removesuffix("\\Binaries\\Win32\\GuiltyGearXrd.exe")
                case _:
                    raise NotImplementedError(f"OS {sys.platform} is currently not implemented.")

    @staticmethod
    def __find_xrd_process_by_vdf_files() -> str:
        # 2. Find Xrd by checking folders (only one path known right now on linux)
        possible_paths = []
        match sys.platform:
            case 'linux':
                possible_paths = ["{HOME}/.steam/root/config/libraryfolders.vdf"]
            case "win32":
                possible_paths = []
                import winreg
                hkey = winreg.HKEY_CURRENT_USER
                try:
                    with winreg.OpenKeyEx(key=hkey,
                                          sub_key=r"SOFTWARE\Valve\Steam") as reg:
                        n_index = winreg.QueryInfoKey(reg)[1]
                        for i in range(0, n_index):
                            query = winreg.EnumValue(reg, i)
                            if query[0] == "SteamPath":
                                possible_paths = [f"{query[1]}/steamapps/libraryfolders.vdf"]

                except FileNotFoundError as e:
                    # Key not found, thus shouldn't be installed.
                    return ""
            case _:
                raise NotImplementedError(f"OS {sys.platform} is currently not implemented.")

        for path_str in possible_paths:
            path_file = Path(path_str.format(
                HOME=os.getenv("HOME"),
            ))
            if path_file.exists():
                with open(path_file.__str__(), "r", encoding="utf-8") as file:
                    last_path = ""
                    for line in file:
                        text = line.lstrip()
                        # Find path line
                        if text.startswith('"path"'):
                            tmp_line = text.removeprefix('"path"')
                            tmp_path = tmp_line.lstrip().rstrip()

                            # Find steam library path
                            if tmp_path.startswith('"') and tmp_path.endswith('"') and len(tmp_path) > 2:
                                last_path = tmp_path.removeprefix('"').removesuffix('"')

                        # Find Xrd line
                        elif text.startswith('"520440"'):
                            return f"{last_path}/steamapps/common/GUILTY GEAR Xrd -REVELATOR-"

        return ""

    @property
    def xrd_path(self) -> str:
        # TODO
        # Should validate be called every time to check if xrd path is still valid?
        # ie: Changed proton version
        if self.__xrd_path:
            pass
        elif path := self.__find_xrd_location_if_open():
            self.xrd_path = path
        elif path := self.__find_xrd_process_by_vdf_files():
            self.__xrd_path = path
        else:
            raise XrdFolderNotFound
        return self.__xrd_path

    @xrd_path.setter
    def xrd_path(self, path: str):
        if self.__check_xrd_path_is_valid(path):
            self.__xrd_path = path
        else:
            raise XrdFolderNotValid(path)

    @staticmethod
    def __check_xrd_path_is_valid(path: str) -> bool:
        """
        Checks if the folder exists and finds a series of files to determine "it's correct"
        :param path:
        :return:
        """
        xrd_path = Path(path)
        if xrd_path.exists() and xrd_path.is_dir():
            files_to_find = [
                "BootGGXrd.bat",
                "Binaries/Win32/GuiltyGearXrd.exe",
            ]
            for file in files_to_find:
                file_path = xrd_path.joinpath(file)
                if not (file_path.exists() or file_path.is_file()):
                    return False
        return True
