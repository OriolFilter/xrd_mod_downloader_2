import dataclasses
import os.path
import shutil
import subprocess
import sys
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path
from subprocess import DEVNULL
from zipfile import ZipFile

import psutil
from github import GitRelease
from github.GitReleaseAsset import GitReleaseAsset

import functions
from exceptions import XrdNotRunning, WineLoaderNotFound, WinePrefixNotFound
from appBase import InjectorApp, StandAloneExeRequirement, GithubApp, XrdBinaryPatcher


# from Config import GlobalConfig


class GenericGithubApp(InjectorApp, GithubApp):
    """
    Used as placeholder, sometimes.
    """

    @property
    def _key_dll(self) -> str:
        return ""

    @property
    def _required_files(self) -> [str]:
        return []

    @property
    def _executable_name(self) -> str:
        return "placeholder.exe"

    def _get_assets_whitelist(self, tag: str) -> [str]:
        raise NotImplementedError("_download_app for app {}".format(self.__class__))


class WakeUpTool(InjectorApp, GithubApp):

    @property
    def _key_dll(self) -> str:
        """
        Wakeup tool is allowed to be launched multiple times.
        :return:
        """
        return ""

    @property
    def _required_files(self) -> [str]:
        return [
            "appsettings.json",
            "GGXrdReversalTool.deps.json",
            "GGXrdReversalTool.dll",
            "GGXrdReversalTool.exe",
            "GGXrdReversalTool.Library.dll",
            "GGXrdReversalTool.runtimeconfig.json",
            "Microsoft.Extensions.Configuration.Abstractions.dll",
            "Microsoft.Extensions.Configuration.Binder.dll",
            "Microsoft.Extensions.Configuration.dll",
            "Microsoft.Extensions.Configuration.FileExtensions.dll",
            "Microsoft.Extensions.Configuration.Json.dll",
            "Microsoft.Extensions.FileProviders.Abstractions.dll",
            "Microsoft.Extensions.FileProviders.Physical.dll",
            "Microsoft.Extensions.FileSystemGlobbing.dll",
            "Microsoft.Extensions.Primitives.dll",
            "System.Text.Encodings.Web.dll",
            "System.Text.Json.dll",
        ]

    @property
    def _executable_name(self) -> str:
        return "GGXrdReversalTool.exe"

    def _get_assets_whitelist(self, tag: str) -> [str]:
        assets_whitelist = ["GGXrdReversalTool.{}.zip".format(tag),
                            "GGXrdReversalTool-{}.zip".format(tag)]

        return assets_whitelist

    @property
    def _is_injected(self) -> bool:
        match sys.platform:
            case 'linux':
                for pid in psutil.process_iter():
                    try:
                        for command in pid.cmdline():
                            if command.endswith("GGXrdReversalTool.exe"):
                                # TODO bring app to foreground.
                                return True
                    except psutil.AccessDenied:
                        pass
                    except psutil.ZombieProcess:
                        pass
            case 'win32':
                for pid in psutil.process_iter():
                    if "GGXrdReversalTool" in pid.name():
                        # TODO bring app to foreground.
                        return True
        return False


class ReplayTakeover(InjectorApp, GithubApp):

    @property
    def _key_dll(self) -> str:
        return "GGXrdReplayTakeover.dll"

    @property
    def _required_files(self) -> [str]:
        return [
            self._key_dll,
            self._executable_name,
        ]

    @property
    def _executable_name(self) -> str:
        return "GGXrdReplayTakeoverInjector.exe"

    def _get_assets_whitelist(self, tag: str) -> [str]:
        assets_whitelist = ["GGXrdReplayTakeover.zip"]
        return assets_whitelist


class GGXrdDisplayPing(InjectorApp, GithubApp):

    @property
    def _key_dll(self) -> str:
        return "GGXrdDisplayPing.dll"

    @property
    def _required_files(self) -> [str]:
        return [
            self._key_dll,
            self._executable_name,
        ]

    @property
    def _executable_name(self) -> str:
        """
        If syswow64 is found, use the 64bit injector, else the 32.

        If not linux or windows raise error.
        :return: str
        """

        match sys.platform:
            case 'linux':
                # Get to the steam "root" folder
                # /home/$HOME/.local/share/Steam/steamapps
                steam_apps_path = Path(self._config.xrd_path).parent.parent

                drivec_windows_path = steam_apps_path.joinpath("compatdata/520440/pfx/drive_c/windows")
                if drivec_windows_path.exists() and drivec_windows_path.is_dir():
                    if drivec_windows_path.joinpath('syswow64').exists() and drivec_windows_path.joinpath('syswow64'):
                        return "GGXrdDisplayPingInjector64bit.exe"
                return "GGXrdDisplayPingInjector.exe"

            case 'win32':
                from sys import maxsize
                if maxsize > 2 ** 32:
                    return "GGXrdDisplayPingInjector64bit.exe"
                return "GGXrdDisplayPingInjector.exe"

            case _:
                raise NotImplementedError(f"System \"{sys.platform}\" is not supported for {self.__class__.__name__}")

    def _get_assets_whitelist(self, tag: str) -> [str]:
        assets_whitelist = ["GGXrdDisplayPing.zip"]
        return assets_whitelist

    @property
    def _launch_extra_args(self) -> [str]:
        """
        "Force" the injection to avoid the window popup
        :return:
        """
        return ["-force"]


class HitboxOverlay(InjectorApp, GithubApp):
    @property
    def _key_dll(self) -> str:
        return "ggxrd_hitbox_overlay.dll"

    @property
    def _is_binary_patched(self) -> bool:
        """
        Code from kkots.
        """

        hardcoded_patch_place_raw = 0x970126
        xrd_exe_path = Path(self._config.xrd_path).joinpath("Binaries/Win32/GuiltyGearXrd.exe")

        with open(xrd_exe_path, "rb") as file:
            file.seek(hardcoded_patch_place_raw)
            if file.read(1) != b'\xe9':
                return False
        return True

    def _unpatch_binary(self):
        # TODO
        # Prevent unpatch if version is less than 15
        # Windows doesn't allow to write a file if it's already open.
        # So... on Windows raise an error if Xrd is open.
        if sys.platform == 'win32':
            for pid in psutil.process_iter():
                if pid.name() == "GuiltyGearXrd.exe":
                    raise Exception(f"Cannot unpatch '{self.app_name}' if Xrd is running.\n"
                                    "Please close Xrd before using.")
        functions.unpatch_hitbox_overlay_exe(Path(self._config.xrd_path).joinpath("Binaries/Win32/GuiltyGearXrd.exe"))

    @property
    def _required_files(self) -> [str]:
        return [
            self._executable_name,
            self._key_dll,
            "ggxrd_hitbox_overlay.ini"
        ]

    @property
    def _executable_name(self) -> str:
        """
        If syswow64 is found, use the 64bit injector, else the 32.

        If not linux or windows raise error.
        :return: str
        """

        match sys.platform:
            case 'linux':
                # Get to the steam "root" folder
                # /home/$HOME/.local/share/Steam/steamapps
                steam_apps_path = Path(self._config.xrd_path).parent.parent

                drivec_windows_path = steam_apps_path.joinpath("compatdata/520440/pfx/drive_c/windows")
                if drivec_windows_path.exists() and drivec_windows_path.is_dir():
                    if drivec_windows_path.joinpath('syswow64').exists() and drivec_windows_path.joinpath('syswow64'):
                        return "ggxrd_hitbox_injector64bit.exe"
                return "ggxrd_hitbox_injector.exe"

            case 'win32':
                from sys import maxsize
                if maxsize > 2 ** 32:
                    return "ggxrd_hitbox_injector64bit.exe"
                return "ggxrd_hitbox_injector.exe"

            case _:
                raise NotImplementedError(f"System \"{sys.platform}\" is not supported for {self.__class__.__name__}")

    def _get_assets_whitelist(self, tag: str) -> [str]:
        assets_whitelist = ["ggxrd_hitbox_overlay.zip"]
        return assets_whitelist

    @property
    def _launch_extra_args(self) -> [str]:
        """
        "Force" the injection to avoid the window popup
        :return:
        """
        return ["-force"]


class GGXrdFreeCam(InjectorApp, GithubApp):
    @property
    def _key_dll(self) -> str:
        return "ggxrd_freecam_dll.dll"

    # @property
    # def _is_binary_patched(self) -> bool:
    #     """
    #     Code from kkots.
    #     """
    #     raise NotImplementedError
    #     hardcoded_patch_place_raw = 0x970126
    #     xrd_exe_path = Path(self._config.xrd_path).joinpath("Binaries/Win32/GuiltyGearXrd.exe")
    #
    #     with open(xrd_exe_path, "rb") as file:
    #         file.seek(hardcoded_patch_place_raw)
    #         if file.read(1) != b'\xe9':
    #             return False
    #     return True
    #
    # def _unpatch_binary(self):
    #     # TODO
    #     # Prevent unpatch if version is less than 15
    #     # Windows doesn't allow to write a file if it's already open.
    #     # So... on Windows raise an error if Xrd is open.
    #     raise NotImplementedError
    #     if sys.platform == 'win32':
    #         for pid in psutil.process_iter():
    #             if pid.name() == "GuiltyGearXrd.exe":
    #                 raise Exception(f"Cannot unpatch '{self.app_name}' if Xrd is running.\n"
    #                                 "Please close Xrd before using.")
    #     functions.unpatch_hitbox_overlay_exe(Path(self._config.xrd_path).joinpath("Binaries/Win32/GuiltyGearXrd.exe"))

    @property
    def _required_files(self) -> [str]:
        return [
            self._executable_name,
            self._key_dll,
            "ggxrd_freecam.ini"
        ]

    @property
    def _executable_name(self) -> str:
        """
        If syswow64 is found, use the 64bit injector, else the 32.

        If not linux or windows raise error.
        :return: str
        """

        match sys.platform:
            case 'linux':
                # Get to the steam "root" folder
                # /home/$HOME/.local/share/Steam/steamapps
                steam_apps_path = Path(self._config.xrd_path).parent.parent

                drivec_windows_path = steam_apps_path.joinpath("compatdata/520440/pfx/drive_c/windows")
                if drivec_windows_path.exists() and drivec_windows_path.is_dir():
                    if drivec_windows_path.joinpath('syswow64').exists() and drivec_windows_path.joinpath('syswow64'):
                        return "ggxrd_freecam_injector64bit.exe"
                return "ggxrd_freecam_injector.exe"

            case 'win32':
                from sys import maxsize
                if maxsize > 2 ** 32:
                    return "ggxrd_freecam_injector64bit.exe"
                return "ggxrd_freecam_injector.exe"

            case _:
                raise NotImplementedError(f"System \"{sys.platform}\" is not supported for {self.__class__.__name__}")

    def _get_assets_whitelist(self, tag: str) -> [str]:
        assets_whitelist = ["ggxrd_freecam.zip"]
        return assets_whitelist

    @property
    def _launch_extra_args(self) -> [str]:
        """
        "Force" the injection to avoid the window popup
        :return:
        """
        return ["-force"]


class VsRedistributableBase(StandAloneExeRequirement, ABC):

    @property
    def tag_name(self) -> str:
        if self.is_installed:
            return self._vs_redist_version
        return ""

    @tag_name.setter
    def tag_name(self, tag_name: str):
        pass

    @property
    def _is_installed(self) -> bool:
        return any(self._vs_redist_version)

    @property
    def _launch_extra_args(self) -> [str]:
        return ["/install", "/quiet", "/norestart"]

    @property
    def _download_file_url(self) -> str:
        return f"https://aka.ms/vs/17/release/{self._executable_name}"

    async def _get_latest_version_name(self) -> str:
        return "14"

    @property
    def _vs_redist_version(self) -> str:
        raise NotImplementedError


class VsRedistributable64(VsRedistributableBase):
    @property
    def _executable_name(self) -> str:
        return "vc_redist.x64.exe"

    @property
    def _vs_redist_version(self) -> str:
        return functions.redist_x64_version()


class VsRedistributable86(VsRedistributableBase):
    @property
    def _executable_name(self) -> str:
        return "vc_redist.x86.exe"

    @property
    def _vs_redist_version(self) -> str:
        return functions.redist_x86_version()


class DotNet(StandAloneExeRequirement):
    @property
    def tag_name(self) -> str:
        if self.is_installed:
            return self._dotnet_version
        return ""

    @tag_name.setter
    def tag_name(self, tag_name: str):
        pass

    async def _get_latest_version_name(self) -> str:
        return "6.0.X"

    @property
    def _launch_extra_args(self) -> [str]:
        match sys.platform:
            case 'win32':
                return ["/install", "/quiet", "/norestart"]
            case 'linux':
                return []

    @property
    def _executable_name(self) -> str:
        match sys.platform:
            case 'linux':
                steam_apps_path = Path(self._config.xrd_path).parent.parent
                drivec_windows_path = steam_apps_path.joinpath("compatdata/520440/pfx/drive_c/windows")
                if drivec_windows_path.joinpath('syswow64').exists() and drivec_windows_path.joinpath(
                        'syswow64').is_dir():
                    arch = "x64"
                else:
                    arch = "x86"
            case "win32":
                from sys import maxsize
                if maxsize > 2 ** 32:
                    arch = "x64"
                else:
                    arch = "x86"
            case _:
                raise NotImplementedError(f"System \"{sys.platform}\" is not supported for {self.__class__.__name__}")
        return f"dotnet-sdk-win-{arch}.exe"

    @property
    def _download_file_url(self) -> str:
        return f"https://aka.ms/dotnet/6.0/{self._executable_name}"

    @property
    def _is_installed(self) -> bool:
        return any(self._dotnet_version)

    @property
    def _dotnet_version(self) -> str:
        """
        Return the dotnet version.

        This assumes that the xrd path already found.
        :return:
        """

        # TODO improve checking.
        # Differentiate SDK from runtime. (aka find a previous commit)
        from sys import maxsize
        match sys.platform:
            case 'linux':
                from os import listdir
                # List folders in dotnet sdk.
                # Sort by name (meaning bigger versions will come first)
                # If dotnet.dll exists return the folder name (aka the version)

                steam_apps_path = Path(self._config.xrd_path).parent.parent
                if maxsize > 2 ** 32:
                    dotnet_path = steam_apps_path.joinpath(
                        "compatdata/520440/pfx/drive_c/Program Files/dotnet/shared/Microsoft.NETCore.App/")
                else:
                    dotnet_path = steam_apps_path.joinpath(
                        "compatdata/520440/pfx/drive_c/Program Files (x86)/dotnet/shared/Microsoft.NETCore.App/")
                if not dotnet_path.exists():
                    return ""

                dotnet_sdk_dirs = []
                dotnet_sdk_files = listdir(dotnet_path)
                dotnet_sdk_files.sort(reverse=True)

                for file in dotnet_sdk_files:
                    file_path = dotnet_path.joinpath(file)
                    if file.startswith("6.0") and file_path.is_dir():
                        dotnet_sdk_dirs.append(file_path.absolute())

                for sdkpath in dotnet_sdk_dirs:
                    dotnet_dll = sdkpath.joinpath(".version")
                    if dotnet_dll.exists() and dotnet_dll.is_file() and not dotnet_dll.is_dir():
                        return sdkpath.name

                return ""

            case "win32":
                if maxsize > 2 ** 32:
                    return functions.get_dotnet_x64_version_windows()
                else:
                    return functions.get_dotnet_x86_version_windows()
        return ""


class GGXrdBackgroundGamepad(XrdBinaryPatcher):
    def _disable_patch(self):
        xrd_exe_path = Path(self._config.xrd_path).joinpath("Binaries/Win32/GuiltyGearXrd.exe")
        with open(xrd_exe_path, "r+b") as file:
            file.seek(0x947762)
            file.write(b'\x0f\x84\x0d\x12\x00\x00')
            file.seek(0x9477f2 + 1)
            file.write(b'\x06')
            file.seek(0xc1dce7 + 12)
            file.write(b'\x06')
            file.seek(0x94c008 + 9)
            file.write(b'\x06')

    def _is_binary_patched(self) -> bool:
        xrd_exe_path = Path(self._config.xrd_path).joinpath("Binaries/Win32/GuiltyGearXrd.exe")
        with open(xrd_exe_path, "rb") as file:
            file.seek(0x947762)
            is_patched = (file.read(6) == b'\x90\x90\x90\x90\x90\x90')
        return is_patched

    def _patch(self):
        xrd_exe_path = Path(self._config.xrd_path).joinpath("Binaries/Win32/GuiltyGearXrd.exe")
        with open(xrd_exe_path, "r+b") as file:
            file.seek(0x947762)
            file.write(b'\x90\x90\x90\x90\x90\x90')
            file.seek(0x9477f2 + 1)
            file.write(b'\x0e')
            file.seek(0xc1dce7 + 12)
            file.write(b'\x0e')
            file.seek(0x94c008 + 9)
            file.write(b'\x0e')
