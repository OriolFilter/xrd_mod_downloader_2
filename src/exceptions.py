class XrdNotRunning(Exception):
    """
    Raised when the XRD process is not found, mostly due to the game not running.
    """


class WineLoaderNotFound(Exception):
    """
    Raised when the value/path for WineLoader couldn't be found (env WINELOADER)
    """


class WinePrefixNotFound(Exception):
    """
    Raised when the value/path for WinePrefix couldn't be found (env WINEPREFIX)
    """


class XrdFolderNotFound(Exception):
    """
    Raised when the Xrd Folder is not located
    """


class XrdFolderNotValid(Exception):
    """
    Raised when the Xrd folder either given or tried to use is not recognized as such.
    """
    # given_path: str

    def __init__(self, path: str):
        super().__init__(f"Path '{path}' is not a valid Xrd directory.")
