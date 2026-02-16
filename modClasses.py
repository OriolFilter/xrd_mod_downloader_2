import dataclasses
import json
from json import JSONEncoder

from github import Github, GitRelease


@dataclasses.dataclass
class AppStruct:
    repo_owner: str
    repo_name: str
    id: int | None = None
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
    description: str = None

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

    def get_latest_release_available(self, prerelease=False) -> GitRelease:
        cli = Github()
        return cli.get_repo(self.app_name).get_latest_release()

    def patch_windows(self):
        raise NotImplementedError

    def patch_linux(self):
        raise NotImplementedError

    def update_to(self, release: GitRelease):
        pass
        self.tag_name = release.name
        # raise Exception(self.tag_name)
        return True
        # raise NotImplementedError

    def default(self, obj):
        if isinstance(obj, complex):
            return [obj.real, obj.imag]
        # Let the base class default method raise the TypeError
        return super().default(obj)

    def export_config_dict(self) -> {str: str | int | None | bool}:
        return {
                "tag_name": self.tag_name,
                "url_source_release": self.url_source_release,
                # automatically_patch: bool = None
                # patched: False,
                # enabled: False  # IDK
                # hidden: False
            }


if __name__ == '__main__':
    x = AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots")
    y = AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots")

    print(x.get_api_repo_url())
    print(x.app_name)
    print(x.get_repo_url())
