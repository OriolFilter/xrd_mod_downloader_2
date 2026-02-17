import dataclasses
import json
from json import JSONEncoder

from github import Github, GitRelease


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

    def get_latest_release(self) -> GitRelease:
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

    def __patch_windows(self):
        raise NotImplementedError

    def __patch_linux(self):
        raise NotImplementedError

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

    def download_mod(self) -> None:
        """Download the mod files"""
        raise NotImplementedError


if __name__ == '__main__':
    x = AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots")
    y = AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots")

    print(x.get_api_repo_url())
    print(x.app_name)
    print(x.get_repo_url())
