import asyncio
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

import aiohttp
import psutil
from github import GitRelease
from github.GitReleaseAsset import GitReleaseAsset

import functions
from exceptions import XrdNotRunning, WineLoaderNotFound, WinePrefixNotFound


# from async_property import async_property

class AppPublic(ABC):
    """
    This is an empty class that's only used to represent the methods available "externally"
    """

    @property
    @abstractmethod
    def app_name(self) -> str:
        """
        Return the name of the app.
        Mostly to identify itself when displayed or with
        :return:
        """
        pass

    @property
    @abstractmethod
    async def is_up_to_date(self) -> bool:
        """
        Whether if is considered to be up-to-date.

        Meaning if "current version" == "latest stable released"

        Couldn't manage to make it sync while keeping some async logic.
        :return:
        """

    @property
    @abstractmethod
    def is_installed(self) -> bool:
        """
        Whether if is considered to be installed.
        This mostly would mean if the files are downloaded to be launched locally.
        Instances like the XrdBinaryPatcher or StandAloneExeRequirement will use a more loose meaning.
        :return:
        """

    @property
    @abstractmethod
    def can_be_launched(self) -> bool:
        """
        Whether if the game/.exe can currently be launched.
        # TODO probably will nuke this. Or refactor it.
        """
        pass

    @abstractmethod
    def update_app_to_latest(self):
        """
        Update the app to the latest version available.
        :return:
        """
        pass

    @property
    @abstractmethod
    def starts_at_boot(self) -> bool:
        pass


@dataclasses.dataclass
class AppStruct(AppPublic, ABC):
    """
    Actual Skel/Base for the mods/apps.
    """

    _config: object
    # TODO rename to owner and name (?)
    repo_owner: str
    repo_name: str
    description: str = ""
    _tag_name: str = ""
    _latest_version_name: str = ""

    @property
    def tag_name(self) -> str:
        return self._tag_name

    @tag_name.setter
    def tag_name(self, tag_name: str):
        self._tag_name = tag_name

    @property
    def app_name(self) -> str:
        # Move to GithubApp, move the owner=name etc from __init__ values to the class itself.
        return "{}/{}".format(self.repo_owner, self.repo_name)

    # TODO NUKE
    # @property
    # @abstractmethod
    # def latest_release(self) -> GitRelease:
    #     raise NotImplementedError
    #     # TODO rename/re-figure it out
    #     # TODO probably delete

    async def get_latest_version_name(self) -> str:
        return await self._get_latest_version_name()

    @abstractmethod
    async def _get_latest_version_name(self) -> str:
        """
        Return the desired target version.
        Required to determine the installation path.
        :return:
        """

        pass
        # TODO rename/re-figure it out

    @property
    def _win32_mod_folder_path(self) -> Path:
        """
        Returns the path for the Binaries/Win32/app_folder directory.


        :return:
        """
        return Path(self._config.xrd_path).joinpath("Binaries/Win32/").joinpath(self.app_name.replace("/", "_"))

    async def download_version(self, version: str) -> bool:
        """# TODO IDK"""
        match sys.platform:
            case 'win32':
                if self.is_installed and self.starts_at_boot:
                    for pid in psutil.process_iter():
                        if pid.name() == "GuiltyGearXrd.exe":
                            # Windows doesn't allow to overwrite/delete/edit an already open file.
                            raise Exception("Can't update *patched* App because Xrd is running.")
            case _:
                pass

        return await self._download_version(version)

    @abstractmethod
    async def _download_version(self, version: str) -> bool:
        raise NotImplementedError

    # @abstractmethod
    async def update_app_to_latest(self):
        """
        1. Download the files
        2. Launches at boot, execute patch
        # TODO, differentiate "patch_boot" and "patch_exe" (?)
        :return:
        """
        # await asyncio.sleep(1)
        # loop = asyncio.get_event_loop()
        # latest_version = loop.run_until_complete(self.get_latest_version_name())
        # loop.close()
        latest_version = await self.get_latest_version_name()
        downloads_result = await self.download_version(latest_version)
        # raise Exception(f"download result={downloads_result}")
        # raise Exception(f"Downloads result = {await downloads_result}")
        if not downloads_result:
            raise Exception(f"Failed downloading the version {latest_version} for {self.app_name}.")
        self.set_current_version(latest_version)

    # @abstractmethod
    def set_current_version(self, version: str):
        """
        Used to swap between the selected version.
        If patched -> replace files
        """
        self.tag_name = version

    # States
    @property
    @abstractmethod
    def starts_at_boot(self) -> bool:
        raise NotImplementedError

    @property
    def _is_binary_patched(self) -> bool:
        """
        Returns False.

        Can be used/implemented to detect if the GuiltyGear.exe or something similar has been patched
        Like with the hitbox viewer.

        :return:
        """
        return False

    # Misc
    def export_config_dict(self) -> {str: str | int | None | bool}:
        return {
            "tag_name": self.tag_name,
        }

    def _unpatch_binary(self):
        """
        Can be used/implemented to unpatch the .exe or doing whatever.
        Like with the hitbox viewer.
        """
        pass

    @property
    def current_version_files_path(self) -> Path:
        return Path(self._config.app_download_path).joinpath(self.app_name.replace("/", "_")).joinpath(self.tag_name)


class InjectorApp(AppStruct, ABC):
    """
    Used by apps that require injection
    """

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
                if line.startswith(f"start {self._bat_file_name}"):
                    return True
        return False

    @property
    def starts_at_boot(self) -> bool:
        # @property
        # @abstractmethod
        # def starts_at_boot(self) -> bool:
        """
        Whether if mod/app is considered to start at Xrd boot.

        Types:
        - .exe binary is patched (literal sense of the word)
        - mod starts with xrd at boot through the BootXrd.bat file

        If xrd_path is not populated/found forces a False.

        Condition is (if autostart.bat patched or .exe patched) return true/false.
        :return:
        """

        return any(self._config.xrd_path) and (
                (self._bat_file_enabled and self._patch_files_exists) or self._is_binary_patched)

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
        if self._is_binary_patched:
            self._unpatch_binary()

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
                if any(self._bat_file_name) and line.startswith(f"start {self._bat_file_name}"):
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
        # TODO replace how it works
        """
        Create/overwrite the DelayApp.bat file.
        Append the start of the bat at the bottom of the BootGGXrd.bat script.
        :return:
        """
        boot_xrd_bat = "BootGGXrd.bat"
        bat_contents = """
    @echo off
    :: This file is automatically generated. Don't edit it manually as it can be overwritten anytime.
    SET "CHECK_XRD=(tasklist /FI "IMAGENAME eq GuiltyGearXrd.exe" /FI "WINDOWTITLE eq Guilty Gear Xrd -REVELATOR-" | findstr GuiltyGearXrd.exe > NUL)"

    %CHECK_XRD% && goto :finish
    echo Waiting for Xrd to launch...
    FOR /L %%I IN (1,1,30) DO (
      %CHECK_XRD% && goto :finish || (ping -n 2 127.0.0.1 > NU)
    )
    :finish
    %CHECK_XRD% && start /MIN {app_directory}/{executable_name} {extra_args} || echo Xrd didn't launch...
    """.format(
            app_directory=self.app_name.replace("/", "_"),
            executable_name=self._executable_name,
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
            # Skip if line exists (ie, when "upgrading/changing the version" of the mod.)
            append_to_boot_xrd = True

            for line in file:
                if any(self._executable_name) and line.startswith(self._executable_name):
                    # Comment "old"/original method of patching
                    new_file_contents.append(f":: {line}")
                elif any(self._bat_file_name) and line.startswith(f":: start {self._bat_file_name}"):
                    # If bat exists but is commented uncomment
                    new_file_contents.append(f"start {self._bat_file_name}\n")
                else:
                    new_file_contents.append(line)

                # Don't append if the bat already exists.
                if line.find(self._bat_file_name) >= 0:
                    append_to_boot_xrd = False
            # Append boot.bat
            if append_to_boot_xrd:
                new_file_contents.append(f"start {self._bat_file_name}\n")

        with open(boot_xrd_path, "w", encoding="utf-8") as file:
            file.writelines(new_file_contents)

        # Copy exe and dll/files
        for file in self._required_files:
            source_file_path = self.current_version_files_path.joinpath(file)
            destination_file_path = self._win32_mod_folder_path.joinpath(file)
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
        # TODO refactor, this should be specific to github Struct

        self.tag_name = release.tag_name
        if self.starts_at_boot:
            if self._is_binary_patched:
                self._unpatch_binary()
            await self.patch()
        return True

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
    async def is_up_to_date(self) -> bool:
        if self.tag_name \
                and self.tag_name == await self.get_latest_version_name():
            # and self.latest_release \
            return True
        return False

    async def _download_version(self, version_name: str) -> bool:
        # raise NotImplementedError(f"_download_version {self.__class__}")
        # release: GitRelease = ...  # TODO send curl, get version -> generate GitRelease object
        release: GitRelease = self._config.github_client.get_repo(self.app_name).get_release(version_name)
        files_to_download: [GitReleaseAsset] = []
        assets_whitelist = self.get_assets_whitelist(tag=release.tag_name)

        new_release_files_path = Path(self._config.app_download_path).joinpath(
            self.app_name.replace("/", "_")).joinpath(release.tag_name)
        for asset in release.assets:
            asset: GitReleaseAsset
            if asset.name in assets_whitelist:
                files_to_download.append(asset)
        # raise Exception(f"{files_to_download}?")
        if not any(files_to_download):
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
        return True

    def get_assets_whitelist(self, tag: str) -> [str]:
        return self._get_assets_whitelist(tag)

    def _get_assets_whitelist(self, tag: str) -> [str]:
        raise NotImplementedError("_download_app for app {}".format(self.__class__))

    def launch(self) -> None:
        if self._is_injected:
            raise Exception("Cannot launch, the mod is already running/injected")
        self._launch(self._launch_extra_args)

    def _launch(self, extra_args=None):
        """
        Uses popen to launch/execute the respective mod/injector/.exe.

        On Linux populates the WinePrefix Display and WineFSync envs.
        Uses the respective wine file as an executable and passes the .exe as an argument.
        """

        if extra_args is None:
            extra_args = []

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

                process = subprocess.Popen(
                    shell=False,
                    args=[
                        wineloader,
                        self.current_version_files_path.joinpath(self._executable_name).absolute(),
                        *extra_args,
                    ],
                    env=envs,
                    stdin=None,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    cwd=self.current_version_files_path.absolute(),
                    start_new_session=True,
                )
            case "win32":
                process = subprocess.Popen(
                    shell=False,
                    args=[
                        self.current_version_files_path.joinpath(self._executable_name).absolute(),
                        *extra_args,
                    ],
                    stdin=None,
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    cwd=self.current_version_files_path.absolute(),
                    start_new_session=True,
                )
            case _:
                raise NotImplementedError(f"OS {sys.platform} is currently not implemented.")

        # TODO.
        # Fixes Causes zombie process with the wakeup tool
        # ps -aux | grep '<defunct>'
        # $USER    105574  ... [start.exe] <defunct>
        # case 'linux':
        process.wait()

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
        :return: True if all files exists.
        False if any is missing.
        """

        for file in self._required_files:
            # raise Exception(f"{self.current_release_files_path}/{file}")
            if not self.current_version_files_path.joinpath(file).is_file():
                return False

        return True

    @property
    def can_be_launched(self) -> bool:
        return any(self._executable_name)

    @property
    def _is_injected(self) -> bool:
        if any(self._key_dll):
            loaded_files = functions.get_xrd_loaded_dll()
            for file in loaded_files:
                file: str
                match sys.platform:
                    case 'linux':
                        if file.endswith(f"/{self._key_dll}") and not file.endswith("/"):
                            return True
                    case 'win32':
                        if file.endswith(f"\\{self._key_dll}") and not file.endswith("\\"):
                            return True
        return False

    @property
    @abstractmethod
    def _key_dll(self) -> str:
        """
        Relevant dll file to look for when checking if the mod is already injected.
        :return:
        """
        pass


class GithubApp(AppStruct, ABC):
    """
    Used by apps that use Github as their source.
    """

    __latest_release_available: GitRelease = None

    def get_repo_url(self) -> str:
        return "https://github.com/{}/{}".format(self.repo_owner, self.repo_name)

    def get_api_repo_url(self) -> str:
        return "https://api.github.com/repos/{}/{}".format(self.repo_owner, self.repo_name)

    # @property
    # def latest_release(self) -> GitRelease:
    #     if not self.__latest_release_available:
    #         self.__latest_release_available = self._config.github_client.get_repo(self.app_name).get_latest_release()
    #     return self.__latest_release_available

    async def _get_latest_version_name(self) -> str:
        if not self._latest_version_name:
            url = f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/latest"
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as resp:
                    latest_url = resp.headers.get("Location")
                    if resp.status and any(latest_url) and latest_url.startswith(
                            f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/tag/"):
                        print("OK!")
                        latest_tag = latest_url.removeprefix(
                            f"https://github.com/{self.repo_owner}/{self.repo_name}/releases/tag/")
                        if latest_tag:
                            return latest_tag
        return self._latest_version_name

    # def fetch_releases_available(self) -> None:
    #     cli = Github()
    #     self.release_available = cli.get_repo(self.app_name).get_releases()


class StandAloneExeRequirement(InjectorApp, ABC):
    """
    Apps that require to run a .exe unrelated to mods and such.
    Ie, dotnet or visual redistributable
    """

    @property
    def tag_name(self) -> str:
        if self.is_installed:
            return self.get_latest_version_name()
        return ""

    @tag_name.setter
    def tag_name(self, _: str):
        pass

    @property
    async def is_up_to_date(self) -> bool:
        if self.is_installed:
            return True
        return False

    @property
    def _key_dll(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def _download_file_url(self) -> str:
        """
        URL of the file to download.
        :return:
        """
        return ""

    @property
    def starts_at_boot(self) -> bool:
        return self.is_installed

    async def _download_version(self, version_name: str) -> bool:
        if len(self._download_file_url) < 1:
            raise Exception(
                "App has '{}' no available to download.".format(
                    self.__class__)
            )

        downloads_files_path = self.current_version_files_path
        if not downloads_files_path.exists():
            downloads_files_path.mkdir(parents=True)

        urllib.request.urlretrieve(self._download_file_url, downloads_files_path.joinpath(self._executable_name))
        # TODO check if it did download and all that
        return True

    @property
    def _required_files(self) -> [str]:
        return [self._executable_name]

    # @property
    # def latest_release(self) -> None:
    #     """
    #     Set to return none for compatibility reasons.
    #     Don't use.
    #     :return:
    #     """
    #     return None

    async def install_release(self, release: GitRelease) -> bool:
        """
        # TODO nuke GitRelease
        Execute the .exe

        Wait for it to finish.

        Change values
        """
        self.launch()
        self.tag_name = await self.get_latest_version_name()
        return True

    @property
    def current_version_files_path(self) -> Path:
        """
        Since the installation step includes setting the self.name_tag, it's using the latest_release_name to determine
        the download destination.

        self.latest_release_name is hardcoded.
        :return:
        """
        # TODO fix/remove installation step
        return Path(self._config.app_download_path).joinpath(self.app_name.replace("/", "_")).joinpath(
            asyncio.run(self.get_latest_version_name()))

    def patch(self):
        # IDK if I should be passing the extra args but
        # TODO check again
        self._launch(self._launch_extra_args)

    def launch(self) -> None:
        self._launch(self._launch_extra_args)

    @property
    def is_installed(self) -> bool:
        return self._is_installed

    @property
    @abstractmethod
    def _is_installed(self) -> bool:
        pass


class XrdBinaryPatcher(AppStruct, ABC):
    pass
    # @abstractmethod
    # async def _get_latest_version_name(self) -> str:
    #     """
    #     Return the desired target version.
    #     Required to determine the installation path.
    #     :return:
    #     """
