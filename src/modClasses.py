import dataclasses
import os.path
import pathlib
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from zipfile import ZipFile

import psutil
from github import GitRelease
from github.GitReleaseAsset import GitReleaseAsset
from exceptions import XrdNotRunning, WineLoaderNotFound, WinePrefixNotFound

from subprocess import Popen, DEVNULL


# from Config import GlobalConfig


@dataclasses.dataclass
class AppStruct(ABC):
    _config: object
    repo_owner: str
    repo_name: str
    release_id: str | None = None
    tag_name: str | None = None
    published_at: str | None = None
    # app_type: str # Shouldn't be necessary/helpful.
    url_source_release: str | None = None
    # automatically_patch: bool = None
    # enabled: bool = False  # IDK
    # hidden: bool = False
    # release_available: [GitRelease] = None
    # track_updates: bool = False
    # tracked: bool = False
    # In case multiple fulfill the same role/have the same name, ie Iquis vs Kkots, or ibrow19 for the replay takeover

    # recommended: bool = False
    description: str = ""
    __latest_release_available: GitRelease = None

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

    # def __patch_windows(self):
    #     raise NotImplementedError
    #
    # def __patch_linux(self):
    #     raise NotImplementedError

    @abstractmethod
    def is_patched(self) -> bool:
        pass

    async def patch(self):
        if not self.is_patched():
            self._patch()

        # match sys.platform:
        #     case "linux":
        #         self._patch_linux()
        #     case "win32" | "cygwin":
        #         self._patch_linux()
        #     case _:
        #         raise NotImplementedError(f"Platform '{sys.platform}' not supported, reach out to the owners if you "
        #                                   f"want you device to be implemented.")

    @abstractmethod
    def _patch(self):
        pass

    # @abstractmethod
    # def _patch_linux(self):
    #     pass
    #
    # @abstractmethod
    # def _patch_windows(self):
    #     pass

    # def update_to(self, release: GitRelease) -> bool:
    #     self.download_release(release)
    #     return True
    #     # raise NotImplementedError

    async def install_release(self, release: GitRelease) -> bool:
        """
        The process of moving/replacing files, or changes required after having downloaded the mod/files locally.
        :param release:
        :return:
        """
        self._install_release(release)
        self.published_at = release.published_at
        self.url_source_release = release.url
        self.tag_name = release.tag_name
        self.release_id = release.id
        # await asyncio.sleep(3)
        return True

    @abstractmethod
    def _install_release(self, release: GitRelease):
        """
        Some mods might not need this and will be set as "pass"
        :param release:
        :return:
        """
        pass

    def export_config_dict(self) -> {str: str | int | None | bool}:
        return {
            "release_id": self.release_id,
            "tag_name": self.tag_name,
            # "published_at": self.published_at, # TODO datetime
            "url_source_release": self.url_source_release,
            # "enabled": self.enabled,
            # "hidden": self.hidden,
        }

    @property
    def current_release_files_path(self) -> str:
        return "{}/{}/{}".format(self._config.app_download_path,
                                 self.app_name.replace("/", "_"), self.tag_name)

    @property
    @abstractmethod
    def _executable_path(self) -> str:
        """
        Returns the location of the .exe file or whatever that needs to be launched.
        Usually will be /app/tag/app.exe, but some might vary/have tag prefixes/suffixes.
        :return:
        """
        pass

    @property
    def up_to_date(self) -> bool:
        if self.tag_name \
                and self.__latest_release_available \
                and self.tag_name == self.__latest_release_available.tag_name:
            return True
        return False

    async def download_release(self, release: GitRelease) -> None:
        """Download the mod/app files"""
        await self.__download_release(release=release)
        # await asyncio.sleep(3)

    async def __download_release(self, release: GitRelease) -> None:
        files_to_download: [GitReleaseAsset] = []
        assets_whitelist = self._get_assets_whitelist(release=release)

        # TODO move to pathlib lib
        new_release_files_path = "{}/{}/{}".format(self._config.app_download_path,
                                                   self.app_name.replace("/", "_"), release.tag_name)

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
        Launch .exe RN this assumes you are on Linux
        """

        xrd_process = None
        for pid in psutil.process_iter():
            if pid.name() == "GuiltyGearXrd.exe":
                xrd_process = pid
                break
        del pid

        if not xrd_process:
            raise XrdNotRunning

        envs = xrd_process.environ()

        wineloader = envs.get("WINELOADER")

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
                self._executable_path,
                *self._launch_extra_args,
            ],
            env=envs,
            stdin=None,
            stdout=DEVNULL,
            stderr=DEVNULL,
            cwd=self.current_release_files_path,
            start_new_session=True,
        )
        # raise Exception([
        #         wineloader,
        #         self._executable_path,
        #         *self._launch_extra_args,
        #         p.pid
        #     ])

    @property
    def _launch_extra_args(self) -> [str]:
        return []

    @property
    def is_installed(self) -> bool:
        if self.tag_name:
            return self._is_installed
        return False

    @property
    @abstractmethod
    def _is_installed(self) -> bool:
        """
        Returns if the app is installed or not.
        What "installed" means is a bit loose, but most of the time will be checking if X files are at Z place.
        :return:
        """
        pass

    # @property
    # def is_patched(self) -> bool:
    #     return self._is_installed

    # @property
    # @abstractmethod
    # def _is_patched(self) -> bool:
    #     pass

    def can_be_launched(self) -> bool:
        return any(self._executable_path)


class GenericApp(AppStruct):
    def _patch(self):
        pass

    def is_patched(self) -> bool:
        pass

    @property
    def _executable_path(self) -> str:
        pass

    def _install_release(self, release: GitRelease):
        pass

    # def _patch_windows(self):
    #     raise NotImplementedError("_patch_windows for app {}".format(self.__class__))
    #
    # def _patch_linux(self):
    #     raise NotImplementedError("_patch_linux for app {}".format(self.__class__))

    # @property
    # def _is_patched(self) -> bool:
    #     raise NotImplementedError("_is_patched for app {}".format(self.__class__))

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        raise NotImplementedError("_download_app for app {}".format(self.__class__))

    @property
    def _is_installed(self):
        return False


class WakeUpTool(AppStruct):
    def _patch(self):
        pass

    def is_patched(self) -> bool:
        pass

    @property
    def _executable_path(self) -> str:
        return f"{self.current_release_files_path}/GGXrdReversalTool.exe"

    def _install_release(self, release: GitRelease):
        """
        This mod only needs to download files.
        :param release:
        :return:
        """
        pass

    @property
    def _is_installed(self) -> bool:
        """
        Wakeup tool only needs a few files.

        :return: True if all files exists.
        False if any is missing.
        """
        files_to_find = ["GGXrdReversalTool.exe"]

        for file in files_to_find:
            # raise Exception(f"{self.current_release_files_path}/{file}")
            if not os.path.isfile(f"{self.current_release_files_path}/{file}"):
                return False

        return True

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        assets_whitelist = ["GGXrdReversalTool.{}.zip".format(release.tag_name),
                            "GGXrdReversalTool-{}.zip".format(release.tag_name)]

        return assets_whitelist

    def _install(self):
        pass


class ReplayTakeover(AppStruct):
    def is_patched(self) -> bool:
        """
        Check if files exists.
        Check if BootGGXrd.bat contains the DelayReplayTakeover.bat script.
        :return:
        """
        boot_xrd_bat = "BootGGXrd.bat"
        delay_takeover_bat = "DelayReplayTakeover.bat"
        files_to_contain = [
            boot_xrd_bat,
        ]
        files_to_contain_binaries_win32 = [
            "GGXrdReplayTakeover.dll",
            "GGXrdReplayTakeoverInjector.exe",
            delay_takeover_bat
        ]

        # Check DelayReplayTakeover.bat (and other files) exists (we are not checking contents anyway)
        for file in files_to_contain:
            file_path = pathlib.Path(self._config.xrd_path).joinpath(file)
            if not (file_path.exists() and file_path.is_file()):
                return False
        for file in files_to_contain_binaries_win32:
            file_path = pathlib.Path(self._config.xrd_path).joinpath("Binaries/Win32/").joinpath(file)
            if not (file_path.exists() and file_path.is_file()):
                return False
                # Check if the init script has the line, even if it's commented,
        boot_xrd_path = pathlib.Path(self._config.xrd_path).joinpath(boot_xrd_bat)
        boot_xrd_file = open(boot_xrd_path, 'r', encoding="utf-8")
        for line in boot_xrd_file.readlines():
            if line.find(delay_takeover_bat) >= 0:
                return True
        return False

    def _patch(self):
        """
        Create/overwrite the DelayReplayTakeover.bat file.
        Append the start of the bat at the bottom of the BootGGXrd.bat script.
        :return:
        """
        delay_takeover_bat = "DelayReplayTakeover.bat"
        takeover_injector = "GGXrdReplayTakeoverInjector.exe"
        boot_xrd_bat = "BootGGXrd.bat"
        files_to_copy_binaries_win32 = [
            "GGXrdReplayTakeover.dll",
            takeover_injector,
        ]
        bat_contents = """
@echo off

SET "CHECK_XRD=(tasklist /FI "IMAGENAME eq GuiltyGearXrd.exe" /FI "WINDOWTITLE eq Guilty Gear Xrd -REVELATOR-" | findstr GuiltyGearXrd.exe > NUL)"

%CHECK_XRD% && goto :finish
echo Waiting for Xrd to launch...
FOR /L %%I IN (1,1,30) DO (
  %CHECK_XRD% && goto :finish || (ping -n 2 127.0.0.1 > NU)
)
:finish
%CHECK_XRD% && start {takeover_inector} || echo Xrd didn't launch...
""".format(takeover_inector=takeover_injector)
        # Check DelayReplayTakeover.bat
        delay_takeover_path = pathlib.Path(self._config.xrd_path).joinpath("Binaries/Win32").joinpath(delay_takeover_bat)
        with open(delay_takeover_path, 'w+', encoding="utf-8") as file:
            file.write(bat_contents)

        # Check BootGGXrd.bat
        boot_xrd_path = pathlib.Path(self._config.xrd_path).joinpath(boot_xrd_bat)

        # Skip if line exists (ie, when "upgrading/changing the version" of the mod.
        append_to_boot_xrd = True
        with open(boot_xrd_path, 'r', encoding="utf-8") as file:
            for line in file.readlines():
                if line.find(delay_takeover_bat) >= 0:
                    append_to_boot_xrd = False
        # Append line
        if append_to_boot_xrd:
            with open(boot_xrd_path, 'a', encoding="utf-8") as file:
                file.write(f"start {delay_takeover_bat}\n")

        # Copy exe and dll/files
        for file in files_to_copy_binaries_win32:
            source_file_path = pathlib.Path(self.current_release_files_path).joinpath(file)
            destination_file_path = pathlib.Path(self._config.xrd_path).joinpath("Binaries/Win32/").joinpath(file)
            pathlib.Path(self._config.xrd_path).joinpath(boot_xrd_bat)
            if source_file_path.exists() and source_file_path.is_file() and not destination_file_path.is_dir():
                shutil.copy2(source_file_path, destination_file_path)
            else:
                raise Exception(f"File '{source_file_path}' couldn't be found.")

    @property
    def _executable_path(self) -> str:
        return "GGXrdReplayTakeoverInjector.exe"

    def _install_release(self, release: GitRelease):
        """
        # TODO
        :param release:
        :return:
        """
        pass

    # def _patch_linux(self):
    #     pass
    #
    # def _patch_windows(self):
    #     pass

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        assets_whitelist = ["GGXrdReplayTakeover.zip".format(release.tag_name)]
        return assets_whitelist

    @property
    def _is_installed(self) -> bool:
        """
        Replay Takeover:
         - Check if dll and exe is in local folder.
         - Check if dll is in XRD folder and equal to the one in the download folder. # TODO

        :return: True if all files exists.
        False if any is missing.
        """
        files_to_find = ["GGXrdReplayTakeoverInjector.exe", "GGXrdReplayTakeover.dll"]

        for file in files_to_find:
            if not os.path.isfile(f"{self.current_release_files_path}/{file}"):
                return False
        return True

    # @property
    # def _is_patched(self) -> bool:
    #     return False


class HitboxOverlay(AppStruct):
    def is_patched(self) -> bool:
        pass

    def _patch(self):
        pass

    @property
    def _executable_path(self) -> str:
        return f"{self.current_release_files_path}/ggxrd_hitbox_injector.exe"

    def _install_release(self, release: GitRelease):
        pass

    # def _patch_windows(self):
    #     raise NotImplementedError("_patch_windows for app {}".format(self.__class__))
    #
    # def _patch_linux(self):
    #     raise NotImplementedError("_patch_linux for app {}".format(self.__class__))

    # @property
    # def _is_patched(self) -> bool:
    #     raise NotImplementedError("_is_patched for app {}".format(self.__class__))

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

    @property
    def _is_installed(self) -> bool:
        """
        TODO not sure what it needs right now

        :return: True if all files exists.
        False if any is missing.
        """
        files_to_find = [
            "ggxrd_hitbox_overlay.ini",
            "ggxrd_hitbox_overlay.dll",
            "ggxrd_hitbox_injector.exe",
            "ggxrd_hitbox_injector64bit.exe",
        ]

        for file in files_to_find:
            # raise Exception(f"{self.current_release_files_path}/{file}")
            if not os.path.isfile(f"{self.current_release_files_path}/{file}"):
                return False

        return True
