import dataclasses


@dataclasses.dataclass
class AppStruct:
    repo_owner: str
    repo_name: str
    id: int | None = None
    tag_name: str | None = None
    published_at: str | None = None
    # app_type: str # Shouldn't be necessary/helpful.
    url_source_version: str | None = None
    automatically_patch: bool = None
    patched: bool = False
    enabled: bool = False
    hidden: bool = False
    track_updates: bool = False
    tracked: bool = False
    # In case multiple fulfill the same role/have the same name, ie Iquis vs Kkots, or ibrow19 for the replay takover
    recommended: bool = False

    @property
    def app_name(self) -> str:
        return "{}/{}".format(self.repo_owner, self.repo_name)

    def get_repo_url(self):
        return "https://github.com/{}/{}".format(self.repo_owner, self.repo_name)

    def get_api_repo_url(self):
        return "https://api.github.com/repos/{}/{}".format(self.repo_owner, self.repo_name)


if __name__ == '__main__':
    x = AppStruct(repo_name="ggxrd_hitbox_overlay_2211", repo_owner="kkots")
    y = AppStruct(repo_name="rev2-wakeup-tool", repo_owner="kkots")

    print(x.get_api_repo_url())
    print(x.app_name)
    print(x.get_repo_url())
