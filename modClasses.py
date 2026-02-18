import dataclasses
import json
import os.path
from json import JSONEncoder
from zipfile import ZipFile

from github import Github, GitRelease
from github.GitReleaseAsset import GitReleaseAsset


@dataclasses.dataclass
class AppStruct:
    repo_owner: str
    repo_name: str
    id: str | None = None
    tag_name: str | None = None
    published_at: str | None = None
    # app_type: str # Shouldn't be necessary/helpful.
    url_source_release: str | None = None
    # automatically_patch: bool = None
    patched: bool = False
    enabled: bool = False  # IDK
    hidden: bool = False
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
        cli = Github()
        if not self.__latest_release_available:
            self.__latest_release_available = cli.get_repo(self.app_name).get_latest_release()
        return self.__latest_release_available

    @property
    def latest_release_name(self) -> str:
        cli = Github()
        if not self.__latest_release_available:
            self.__latest_release_available = cli.get_repo(self.app_name).get_latest_release()
        return self.__latest_release_available.tag_name

    # def __patch_windows(self):
    #     raise NotImplementedError
    #
    # def __patch_linux(self):
    #     raise NotImplementedError

    def patch(self):
        # If linux
        # if Windows
        # Else
        linux = False
        windows = False
        if linux:
            ...
        elif windows:
            ...
        else:
            raise NotImplementedError

    def update_to(self, release: GitRelease):
        pass
        self.tag_name = release.tag_name
        # raise Exception(self.tag_name)
        return True
        # raise NotImplementedError

    def export_config_dict(self) -> {str: str | int | None | bool}:
        return {
            "id": self.id,
            "tag_name": self.tag_name,
            "published_at": self.published_at,
            "url_source_release": self.url_source_release,
            "patched": self.patched,
            "enabled": self.enabled,
            "hidden": self.hidden,
        }

    @property
    def up_to_date(self) -> bool:
        if self.tag_name and self.__latest_release_available and self.tag_name == self.__latest_release_available.tag_name:
            return True
        return False

    def download_app(self, path: str, release: GitRelease):
        """Download the mod/app files"""
        self.__download_app(path=path, release=release)

    def __download_app(self, path: str, release: GitRelease) -> None:
        files_to_download: [GitReleaseAsset] = []
        assets_whitelist = self.get_assets_whitelist(release=release)
        app_download_folder_path = "{}/{}/{}".format(path, self.app_name.replace("/", "_"), release.tag_name)

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
        if not os.path.exists(path=app_download_folder_path):
            os.makedirs(app_download_folder_path, exist_ok=True)
        elif not os.path.isdir(app_download_folder_path):
            raise Exception("Downloads path ({}) is occupied by a file".format(app_download_folder_path))

        for asset in files_to_download:
            asset: GitReleaseAsset
            asset.download_asset(path=f"{app_download_folder_path}/{asset.name}")

        # For each zip unzip
        for file in files_to_download:
            if file.name.endswith(".zip"):
                with ZipFile(f"{app_download_folder_path}/{file.name}") as z:
                    z.extractall(path=app_download_folder_path)
                    # TODO only extract desired files

    def get_assets_whitelist(self, release: GitRelease) -> [str]:
        raise NotImplementedError("_download_app for app {}".format(self.__class__))

    def launch(self):
        if self.can_be_launched():
            self._launch()
        else:
            raise Exception("Can't be launched")

    def _launch(self):
        raise NotImplementedError("_launch for app {}".format(self.__class__))

    @property
    def installed(self) -> bool:
        return any(self.tag_name)

    def can_be_launched(self) -> bool:
        return self.installed or self._can_be_launched


class WakeUpTool(AppStruct):
    _can_be_launched = True

    def get_assets_whitelist(self, release: GitRelease) -> [str]:
        assets_whitelist = ["GGXrdReversalTool.{}.zip".format(release.tag_name),
                            "GGXrdReversalTool-{}.zip".format(release.tag_name)]

        return assets_whitelist

    def _install(self):
        pass
