import asyncio
import dataclasses
import json
import os.path
import platform
import sys
import time
from json import JSONEncoder
from zipfile import ZipFile

from github import GitRelease
from github.GitReleaseAsset import GitReleaseAsset

from abc import ABC, abstractmethod, abstractproperty


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
    # In case multiple fulfill the same role/have the same name, ie Iquis vs Kkots, or ibrow19 for the replay takover
    recommended: bool = False
    description: str = ""
    __latest_release_available: GitRelease = None
    _can_be_launched = False

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

    # def patch(self):
    #     # If linux
    #     # if Windows
    #     # Else
    #     match sys.platform:
    #         case "linux":
    #             self._patch_linux()
    #         case "win32" | "cygwin":
    #             self._patch_linux()
    #         case _:
    #             raise NotImplementedError(f"Platform '{sys.platform}' not supported, reach out to the owners if you "
    #                                       f"want you device to be implemented.")

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
        await asyncio.sleep(3)
        return True


    @abstractmethod
    def _install_release(self, release: GitRelease):
        pass

    def export_config_dict(self) -> {str: str | int | None | bool}:
        return {
            "release_id": self.release_id,
            "tag_name": self.tag_name,
            # "published_at": self.published_at,
            "url_source_release": self.url_source_release,
            # "enabled": self.enabled,
            # "hidden": self.hidden,
        }

    @property
    def up_to_date(self) -> bool:
        if self.tag_name and self.__latest_release_available and self.tag_name == self.__latest_release_available.tag_name:
            return True
        return False

    async def download_release(self, release: GitRelease) -> None:
        """Download the mod/app files"""
        await self.__download_app(release=release)
        await asyncio.sleep(3)

    async def __download_app(self, release: GitRelease) -> None:
        files_to_download: [GitReleaseAsset] = []
        assets_whitelist = self._get_assets_whitelist(release=release)
        release_download_folder_path = "{}/{}/{}".format(self._config.app_download_path,
                                                         self.app_name.replace("/", "_"), release.tag_name)

        release: GitRelease
        for asset in release.assets:
            asset: GitReleaseAsset
            if asset.name in assets_whitelist:
                files_to_download.append(asset)
        # raise Exception(f"{len(files_to_download) > 0}?")
        if not len(files_to_download) > 0:
            raise Exception(
                "No files matched the criteria to be Download.\nFiles matched: {}.\nFiles whitelisted: {}\nFiles found: {}".format(
                    files_to_download,
                    assets_whitelist,
                    [asset.name for asset in release.assets])
            )
        # Check download folder exists
        if not os.path.exists(path=release_download_folder_path):
            os.makedirs(release_download_folder_path, exist_ok=True)
        elif not os.path.isdir(release_download_folder_path):
            raise Exception("Downloads path ({}) is occupied by a file".format(release_download_folder_path))

        for asset in files_to_download:
            asset: GitReleaseAsset
            asset.download_asset(path=f"{release_download_folder_path}/{asset.name}")

        # # For each zip unzip
        for file in files_to_download:
            if file.name.endswith(".zip"):
                with ZipFile(f"{release_download_folder_path}/{file.name}") as z:
                    z.extractall(path=release_download_folder_path)
                    # TODO only extract desired files

    def get_assets_whitelist(self, release: GitRelease):
        self.get_assets_whitelist(release=release)

    @abstractmethod
    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        raise NotImplementedError("_download_app for app {}".format(self.__class__))

    def launch(self):
        if self.can_be_launched():
            self._launch()
        else:
            raise Exception("Can't be launched")

    @abstractmethod
    def _launch(self):
        pass

    @property
    def is_installed(self) -> bool:
        return self._is_installed

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
        return self.is_installed or self._can_be_launched


class GenericApp(AppStruct):
    def _install_release(self, release: GitRelease):
        pass

    # def _patch_windows(self):
    #     raise NotImplementedError("_patch_windows for app {}".format(self.__class__))
    #
    # def _patch_linux(self):
    #     raise NotImplementedError("_patch_linux for app {}".format(self.__class__))

    def _launch(self):
        raise NotImplementedError("_launch for app {}".format(self.__class__))

    # @property
    # def _is_patched(self) -> bool:
    #     raise NotImplementedError("_is_patched for app {}".format(self.__class__))

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        raise NotImplementedError("_download_app for app {}".format(self.__class__))

    @property
    def _is_installed(self):
        return False


class WakeUpTool(AppStruct):
    def _install_release(self, release: GitRelease):
        pass

    _can_be_launched = True

    # def _patch_windows(self):
    #     """No need to patch"""
    #     pass
    #
    # def _patch_linux(self):
    #     """No need to patch"""
    #     pass

    def _launch(self):
        raise NotImplementedError("_launch for app {}".format(self.__class__))

    # @property
    # def _is_patched(self) -> bool:
    #     """
    #     Doesn't need to patch, if it's installed is patched :thumbsup:
    #     :return:
    #     """
    #     return self.is_installed

    @property
    def _is_installed(self) -> bool:
        """
        Wakeup tool only needs a few files.

        :return: True if all files exists.
        False if any is missing.
        """
        files_to_find = ["GGXrdReversalTool.exe"]

        release_download_folder_path = "{}/{}/{}".format(self._config.app_download_path,
                                                         self.app_name.replace("/", "_"), self.tag_name)

        for file in files_to_find:
            if not os.path.isfile(f"{release_download_folder_path}/{file}"):
                return False

        return True

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        assets_whitelist = ["GGXrdReversalTool.{}.zip".format(release.tag_name),
                            "GGXrdReversalTool-{}.zip".format(release.tag_name)]

        return assets_whitelist

    def _install(self):
        pass


class ReplayTakeover(AppStruct):
    def _install_release(self, release: GitRelease):
        pass

    # def _patch_linux(self):
    #     pass
    #
    # def _patch_windows(self):
    #     pass

    def _get_assets_whitelist(self, release: GitRelease) -> [str]:
        assets_whitelist = ["GGXrdReplayTakeover.zip".format(release.tag_name)]
        return assets_whitelist

    def _launch(self):
        pass

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

        release_download_folder_path = "{}/{}/{}".format(self._config.app_download_path,
                                                         self.app_name.replace("/", "_"), self.tag_name)

        for file in files_to_find:
            if not os.path.isfile(f"{release_download_folder_path}/{file}"):
                return False
        return True

    # @property
    # def _is_patched(self) -> bool:
    #     return False
