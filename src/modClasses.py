import dataclasses
import os.path
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from zipfile import ZipFile

import psutil
from github import GitRelease
from github.GitReleaseAsset import GitReleaseAsset
from exceptions import XrdNotRunning, WineLoaderNotFound, WinePrefixNotFound

from subprocess import Popen, DEVNULL

from functions import unpatch_hitbox_overlay_exe, is_redist_x64_installed, is_redist_x86_installed

import urllib.request
from urllib.parse import urlsplit


# from Config import GlobalConfig


@dataclasses.dataclass
class AppStruct(ABC):
    _config: object
    repo_owner: str
    repo_name: str
    release_id: str | None = ""
    tag_name: str | None = ""
    # app_type: str # Shouldn't be necessary/helpful.
    url_source_release: str | None = ""
    description: str = ""
    __latest_release_available: GitRelease = None

    # _requires_xrd_running_to_launch = True

    @property
    def app_name(self) -> str:
        return "{}/{}".format(self.repo_owner, self.repo_name)

    def get_repo_url(self) -> str:
        return "https://github.com/{}/{}".format(self.repo_owner, self.repo_name)

    def get_api_repo_url(self) -> str:
        return "https://api.github.com/repos/{}/{}".format(self.repo_owner, self.repo_name)

    # def fetch_releases_available(self) -> None:
    #     cli = Github()
    #     self.release_available = cli.get_repo(self.app_name).get_releases()

    @property
    def latest_release(self) -> GitRelease:
        if not self.__latest_release_available:
            self.__latest_release_available = self._config.github_client.get_repo(self.app_name).get_latest_release()
        return self.__latest_release_available

    @property
    def latest_release_name(self) -> str:
        if not self.__latest_release_available:
            self.__latest_release_available = self._config.github_client.get_repo(self.app_name).get_latest_release()
        return self.__latest_release_available.tag_name

    @property
    def _bat_file_enabled(self) -> bool:
        """
        Checks if the app.bat file is uncommented/ready
        :return: 
        """
        boot_xrd_bat = "BootGGXrd.bat"
        boot_xrd_path = Path(self._config.xrd_path).joinpath(boot_xrd_bat)
        with open(boot_xrd_path, 'r', encoding="utf-8") as boot_xrd_file:
            for line in boot_xrd_file.readlines():
                if line.startswith((f"start {self._bat_file_name}")):
                    return True
        return False

    @property
    def is_patched(self) -> bool:
        """
        Checking for xrd_path is to see if it's populated/found the xrd path.

        Otherwise, there is no reason to.

        Condition is (if autostart.bat patched or .exe patched) return true/false.

        :return:
        """
        return any(self._config.xrd_path) and (
                (self._bat_file_enabled and self._patch_files_exists) or self._custom_is_patched)

    @property
    def _win32_mod_folder_path(self) -> Path:
        """
        Returns the path for the Binaries/Win32/app_folder directory.


        :return:
        """
        return Path(self._config.xrd_path).joinpath("Binaries/Win32/").joinpath(self.app_name.replace("/", "_"))

    @property
    def _custom_is_patched(self) -> bool:
        """
        Returns False.

        Can be used/implemented to detect if the GuiltyGear.exe or something similar has been patched
        Like with the hitbox viewer.

        :return:
        """
        return False

    def _custom_unpatch(self):
        """
        Can be used/implemented to unpatch the .exe or doing whatever.
        Like with the hitbox viewer.
        """
        pass

    @property
    def _patch_files_exists(self) -> bool:
        """
        Check if files exists.
        Check if BootGGXrd.bat contains the DelayReplayTakeover.bat script.
        :return:
        """
        boot_xrd_bat = "BootGGXrd.bat"
        files_to_contain = [
            boot_xrd_bat,
        ]

        # Check .bat exists
        bat_path = Path(self._config.xrd_path).joinpath("Binaries/Win32").joinpath(self._bat_file_name)
        if not (bat_path.exists() and bat_path.is_file()):
            return False

        # Check App.bat (and other files) exists (we are not checking contents anyway)
        for file in files_to_contain:
            file_path = Path(self._config.xrd_path).joinpath(file)
            if not (file_path.exists() and file_path.is_file()):
                return False
        for file in self._required_files:
            file_path = self._win32_mod_folder_path.joinpath(file)
            if not (file_path.exists() and file_path.is_file()):
                return False
        return True

    async def patch(self):
        self._patch()

    async def disable_patch(self):
        """Toggle start on boot for the mod"""
        if self._custom_is_patched:
            self._custom_unpatch()

        self._disable_patch()

    def _disable_patch(self):
        """
        Find self.bat in BootXRD.bat and comment it.
        :return:
        """
        boot_xrd_bat = "BootGGXrd.bat"
        boot_xrd_path = Path(self._config.xrd_path).joinpath(boot_xrd_bat)
        new_file_contents: [str] = []
        with open(boot_xrd_path, 'r', encoding="utf-8") as file:
            for line in file:
                if len(self._bat_file_name) > 0 and line.startswith(f"start {self._bat_file_name}"):
                    new_file_contents.append(f":: start {self._bat_file_name}\n")
                # elif len(self._bat_file_name) > 0 and line.startswith(f":: {self._bat_file_name}"):
                #     new_file_contents.append(f"{self._bat_file_name}\n")
                else:
                    new_file_contents.append(line)

        with open(boot_xrd_path, "w", encoding="utf-8") as file:
            file.writelines(new_file_contents)

    @property
    @abstractmethod
    def _required_files(self) -> [str]:
        pass

    def _patch(self):
        # TODO Move patching away/into a single bat file, instead of 10/per mod.
        """
        Create/overwrite the DelayApp.bat file.
        Append the start of the bat at the bottom of the BootGGXrd.bat script.
        :return:
        """
        boot_xrd_bat = "BootGGXrd.bat"
        bat_contents = """
@echo off

SET "CHECK_XRD=(tasklist /FI "IMAGENAME eq GuiltyGearXrd.exe" /FI "WINDOWTITLE eq Guilty Gear Xrd -REVELATOR-" | findstr GuiltyGearXrd.exe > NUL)"

%CHECK_XRD% && goto :finish
echo Waiting for Xrd to launch...
FOR /L %%I IN (1,1,30) DO (
  %CHECK_XRD% && goto :finish || (ping -n 2 127.0.0.1 > NU)
)
:finish
%CHECK_XRD% && start /MIN {app_directory}/{takeover_inector} {extra_args} || echo Xrd didn't launch...
""".format(
            app_directory=self.app_name.replace("/", "_"),
            takeover_inector=self._executable_name,
            extra_args=" ".join(f'"{arg}"' for arg in self._launch_extra_args)
        )
        if not self._win32_mod_folder_path.exists():
            self._win32_mod_folder_path.mkdir(parents=True)

        # Check DelayApp.bat
        bat_file_path = Path(self._config.xrd_path).joinpath("Binaries/Win32").joinpath(self._bat_file_name)
        with open(bat_file_path, 'w+', encoding="utf-8") as file:
            file.write(bat_contents)

        # Check BootGGXrd.bat
        boot_xrd_path = Path(self._config.xrd_path).joinpath(boot_xrd_bat)

        new_file_contents: [str] = []
        with open(boot_xrd_path, 'r', encoding="utf-8") as file:
            # Skip if line exists (ie, when "upgrading/changing the version" of the mod.
            append_to_boot_xrd = True

            for line in file:
                if len(self._executable_name) > 0 and line.startswith(self._executable_name):
                    # Comment "old"/original method of patching
                    new_file_contents.append(f":: {line}")
                elif len(self._bat_file_name) > 0 and line.startswith(f":: start {self._bat_file_name}"):
                    # If bat exists but is commented uncomment
                    new_file_contents.append(f"\nstart {self._bat_file_name}\n")
                else:
                    new_file_contents.append(line)

                # Don't append if the bat already exists.
                if line.find(self._bat_file_name) >= 0:
                    append_to_boot_xrd = False
            # Append boot.bat
            if append_to_boot_xrd:
                new_file_contents.append(f"\nstart {self._bat_file_name}")

        with open(boot_xrd_path, "w", encoding="utf-8") as file:
            file.writelines(new_file_contents)

        # Copy exe and dll/files
        for file in self._required_files:
            source_file_path = self.current_release_files_path.joinpath(file)
            destination_file_path = self._win32_mod_folder_path.joinpath(file)
            Path(self._config.xrd_path).joinpath(boot_xrd_bat)
            if source_file_path.exists() and source_file_path.is_file() and not destination_file_path.is_dir():
                shutil.copy2(source_file_path, destination_file_path)
            else:
                raise Exception(f"File '{source_file_path}' couldn't be found.")

    async def install_release(self, release: GitRelease) -> bool:
        """
        The process of moving/replacing files, or changes required after having downloaded the mod/files locally.
        :param release:
        :return:
        """
        self.url_source_release = release.url
        self.tag_name = release.tag_name
        self.release_id = release.id
        if self.is_patched:
            if self._custom_is_patched:
                self._custom_unpatch()
            await self.patch()
        return True

    def export_config_dict(self) -> {str: str | int | None | bool}:
        return {
            "release_id": self.release_id,
            "tag_name": self.tag_name,
            "url_source_release": self.url_source_release,
            # "enabled": self.enabled,
            # "hidden": self.hidden,
        }

    @property
    def current_release_files_path(self) -> Path:
        return Path(self._config.app_download_path).joinpath(self.app_name.replace("/", "_")).joinpath(self.tag_name)

    @property
    @abstractmethod
    def _executable_name(self) -> str:
        """
        Returns the location of the .exe file or whatever that needs to be launched.
        Usually will be /app/tag/app.exe, but some might vary/have tag prefixes/suffixes.
        :return:
        """
        pass

    @property
    def _bat_file_name(self) -> str:
        return "{}.bat".format(self.app_name.replace('/', '_'))

    @property
    def up_to_date(self) -> bool:
        if self.tag_name \
                and self.__latest_release_available \
                and self.tag_name == self.__latest_release_available.tag_name:
            return True
        return False

    async def download_release(self, release: GitRelease) -> None:
        """Download the mod/app files"""
        match sys.platform:
            case 'win32':
                if self.is_installed and self.is_patched:
                    for pid in psutil.process_iter():
                        if pid.name() == "GuiltyGearXrd.exe":
                            # Windows doesn't allow to overwrite/delete/edit an already open file.
                            raise Exception("Can't update *patched* App because Xrd is running.")
            case _:
                pass

        await self.__download_release(release=release)
        # await asyncio.sleep(3)

    async def __download_release(self, release: GitRelease) -> None:
        files_to_download: [GitReleaseAsset] = []
        assets_whitelist = self._get_assets_whitelist(release=release)

        new_release_files_path = Path(self._config.app_download_path).joinpath(
            self.app_name.replace("/", "_")).joinpath(release.tag_name)

        release: GitRelease
        for asset in release.assets:
            asset: GitReleaseAsset
            if asset.name in assets_whitelist:
                files_to_download.append(asset)
        # raise Exception(f"{len(files_to_download) > 0}?")
        if not len(files_to_download) > 0:
            raise Exception(
                "No files matched the criteria to be Download."
                "\nFiles matched: {}."
                "\nFiles whitelisted: {}."
                "\nFiles found: {}".format(
                    files_to_download,
                    assets_whitelist,
                    [asset.name for asset in release.assets])
            )
        # Check download folder exists
        if not os.path.exists(path=new_release_files_path):
            os.makedirs(new_release_files_path, exist_ok=True)
        elif not os.path.isdir(new_release_files_path):
            raise Exception("Downloads path ({}) is occupied by a file".format(new_release_files_path))

        for asset in files_to_download:
            asset: GitReleaseAsset
            asset.download_asset(path=f"{new_release_files_path}/{asset.name}")

        # # For each zip unzip
        for file in files_to_download:
            if file.name.endswith(".zip"):
                with ZipFile(f"{new_release_files_path}/{file.name}") as z:
                    z.extractall(path=new_release_files_path)
                    # TODO only extract desired files

    def get_assets_whitelist(self, release: GitRelease):
        self.get_assets_whitelist(release=release)

    @abstractmethod
    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        raise NotImplementedError("_download_app for app {}".format(self.__class__))

    def launch(self) -> None:
        self._launch()

    def _launch(self):
        """
        # TODO
        """

        xrd_process = None
        for pid in psutil.process_iter():
            if pid.name() == "GuiltyGearXrd.exe":
                xrd_process = pid
                break
        del pid

        if not xrd_process:
            raise XrdNotRunning

        match sys.platform:
            case 'linux':
                envs = xrd_process.environ()
                wineloader = envs.get("WINELOADER")
                #
                if not wineloader:
                    raise WineLoaderNotFound

                wineprefix = envs.get("WINEPREFIX")
                if not wineprefix:
                    raise WinePrefixNotFound

                envs = {
                    "WINEFSYNC": "1",
                    "WINEPREFIX": wineprefix,
                    "DISPLAY": envs.get("DISPLAY")
                }

                subprocess.Popen(
                    shell=False,
                    args=[
                        wineloader,
                        self.current_release_files_path.joinpath(self._executable_name).absolute(),
                        *self._launch_extra_args,
                    ],
                    env=envs,
                    stdin=None,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    cwd=self.current_release_files_path.absolute(),
                    start_new_session=True,
                )
            case "win32":
                subprocess.Popen(
                    shell=False,
                    args=[
                        #                                         wineloader,
                        self.current_release_files_path.joinpath(self._executable_name).absolute(),
                        *self._launch_extra_args,
                    ],
                    stdin=None,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    cwd=self.current_release_files_path.absolute(),
                    start_new_session=True,
                )
            case _:
                raise NotImplementedError(f"OS {sys.platform} is currently not implemented.")

    @property
    def _launch_extra_args(self) -> [str]:
        return []

    @property
    def is_installed(self) -> bool:
        if self.tag_name:
            return self._is_installed
        return False

    @property
    def _is_installed(self) -> bool:
        """
        Wakeup tool only needs a few files.

        :return: True if all files exists.
        False if any is missing.
        """

        for file in self._required_files:
            # raise Exception(f"{self.current_release_files_path}/{file}")
            if not self.current_release_files_path.joinpath(file).is_file():
                return False

        return True

    def can_be_launched(self) -> bool:
        return any(self._executable_name)


class GenericApp(AppStruct):

    @property
    def _required_files(self) -> [str]:
        return []

    @property
    def _executable_name(self) -> str:
        return "placeholder.exe"

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        raise NotImplementedError("_download_app for app {}".format(self.__class__))


class WakeUpTool(AppStruct):

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

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        assets_whitelist = ["GGXrdReversalTool.{}.zip".format(release.tag_name),
                            "GGXrdReversalTool-{}.zip".format(release.tag_name)]

        return assets_whitelist


class ReplayTakeover(AppStruct):

    @property
    def _required_files(self) -> [str]:
        return [
            "GGXrdReplayTakeover.dll",
            self._executable_name,
        ]

    @property
    def _executable_name(self) -> str:
        return "GGXrdReplayTakeoverInjector.exe"

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        assets_whitelist = ["GGXrdReplayTakeover.zip".format(release.tag_name)]
        return assets_whitelist


class HitboxOverlay(AppStruct):
    @property
    def _custom_is_patched(self) -> bool:
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

    def _custom_unpatch(self):
        # TODO
        # Prevent unpatch if version is less than 15
        # Windows doesn't allow to write a file if it's already open.
        # So... on Windows raise an error if Xrd is open.
        if sys.platform == 'win32':
            for pid in psutil.process_iter():
                if pid.name() == "GuiltyGearXrd.exe":
                    raise Exception(f"Cannot unpatch '{self.app_name}' if Xrd is running.\n"
                                    "Please close Xrd before using.")
        unpatch_hitbox_overlay_exe(Path(self._config.xrd_path).joinpath("Binaries/Win32/GuiltyGearXrd.exe"))

    @property
    def _required_files(self) -> [str]:
        return [
            self._executable_name,
            "ggxrd_hitbox_overlay.dll",
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
                steam_apps_path = Path(self._config.xrd_path).parent.parent.parent

                drivec_windows_path = steam_apps_path.joinpath("compatdata/520440/pfx/drive_c/windows")
                if drivec_windows_path.exists() and drivec_windows_path.is_dir():
                    if drivec_windows_path.joinpath('syswow64').exists() and drivec_windows_path.joinpath('syswow64'):
                        return "ggxrd_hitbox_injector64bit.exe"
                return "ggxrd_hitbox_injector.exe"

            case 'win32':
                from sys import maxsize
                if maxsize is 2 ** 32:
                    return "ggxrd_hitbox_injector64bit.exe"
                return "ggxrd_hitbox_injector.exe"

            case _:
                raise NotImplementedError

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        assets_whitelist = ["ggxrd_hitbox_overlay.zip"]
        return assets_whitelist

    @property
    def _launch_extra_args(self) -> [str]:
        """
        "Force" the injection to avoid the window popup
        :return:
        """
        return ["-force"]


class StandAloneExeRequirement(AppStruct, ABC):

    @property
    @abstractmethod
    def latest_release_name(self) -> str:
        """
        Return the desired target version.
        It's not relevant but to simplify some stuff...
        :return:
        """
        pass

    @property
    @abstractmethod
    def _download_file_url(self) -> str:
        """
        URL of the file to download.
        :return:
        """
        return ""

    @property
    def is_patched(self) -> bool:
        return self.is_installed

    async def download_release(self, release: object):
        if len(self._download_file_url) < 1:
            raise Exception(
                "App has '{}' no available to download.".format(
                    self.__class__)
            )

        downloads_files_path = self.current_release_files_path
        if not downloads_files_path.exists():
            downloads_files_path.mkdir(parents=True)

        urllib.request.urlretrieve(self._download_file_url, downloads_files_path.joinpath(self._executable_name))

    @property
    def _required_files(self) -> [str]:
        return [self._executable_name]

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        raise NotImplementedError

    @property
    def latest_release(self) -> None:
        return

    async def install_release(self, release: GitRelease) -> bool:
        """
        Execute the .exe

        Wait for it to finish.

        Change values
        """
        self.launch()
        self.url_source_release = self.url_source_release
        self.tag_name = self.latest_release_name
        self.release_id = self.latest_release_name
        return True

    @property
    def current_release_files_path(self) -> Path:
        return Path(self._config.app_download_path).joinpath(self.app_name.replace("/", "_")).joinpath(
            self.latest_release_name)

    def patch(self):
        self.launch()

    def launch(self) -> None:
        if self._is_installed:
            raise Exception("Once App {} is installed, it cannot be uninstalled nor patched")
        self._launch()

    def _launch(self):
        """
        Launch the .exe

        Wait for it to finish/close.
        """
        # TODO Linux
        match sys.platform:
            case 'linux':
                raise NotImplementedError(f"Launch app {self.__class__}")
            #         envs = xrd_process.environ()
            #         wineloader = envs.get("WINELOADER")
            #         #
            #         if not wineloader:
            #             raise WineLoaderNotFound
            #
            #         wineprefix = envs.get("WINEPREFIX")
            #         if not wineprefix:
            #             raise WinePrefixNotFound
            #
            #         envs = {
            #             "WINEFSYNC": "1",
            #             "WINEPREFIX": wineprefix,
            #             "DISPLAY": envs.get("DISPLAY")
            #         }
            #
            #         subprocess.Popen(
            #             shell=False,
            #             args=[
            #                 wineloader,
            #                 self.current_release_files_path.joinpath(self._executable_name).absolute(),
            #                 *self._launch_extra_args,
            #             ],
            #             env=envs,
            #             stdin=None,
            #             stdout=DEVNULL,
            #             stderr=DEVNULL,
            #             cwd=self.current_release_files_path.absolute(),
            #             start_new_session=True,
            #         )
            case 'win32':
                process = subprocess.Popen(
                    shell=False,
                    args=[
                        #                                         wineloader,
                        self.current_release_files_path.joinpath(self._executable_name).absolute(),
                        *self._launch_extra_args,
                    ],
                    stdin=None,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    cwd=self.current_release_files_path.absolute(),
                    start_new_session=True,
                )
        process.wait()

    @property
    def is_installed(self) -> bool:
        return self._is_installed


class VsRedistributableBase(StandAloneExeRequirement, ABC):
    @property
    def _launch_extra_args(self) -> [str]:
        return ["/install", "/quiet", "/norestart"]

    @property
    def _download_file_url(self) -> str:
        return f"https://aka.ms/vs/17/release/{self._executable_name}"

    @property
    def latest_release_name(self) -> str:
        return "14"


class VsRedistributable64(VsRedistributableBase):
    @property
    def _executable_name(self) -> str:
        return "vc_redist.x64.exe"

    @property
    def _is_installed(self) -> bool:
        return is_redist_x64_installed()


class VsRedistributable86(VsRedistributableBase):
    @property
    def _executable_name(self) -> str:
        return "vc_redist.x86.exe"

    @property
    def _is_installed(self) -> bool:
        return is_redist_x86_installed()
