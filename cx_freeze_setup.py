import sys
from cx_Freeze import setup, Executable

from yttt import __version__

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

build_exe_options = {"includes": "atexit"}

bdist_mac_options = {
    "bundle_name": "yttt",
}

bdist_dmg_options = {
    "volume_label": "YTTT",
}

executables = [Executable("yttt/gui.py",
                          base=base,
                          target_name="yttt",
                          icon="icon.ico",
                          shortcut_name="Youtube Time Tracking tools",
                          shortcut_dir="DesktopFolder")]

setup(
    name="yttt",
    version=__version__,
    description="Youtube Time Tracking tools",
    options={
        "build_exe": build_exe_options,
        "bdist_mac": bdist_mac_options,
        "bdist_dmg": bdist_dmg_options,
    },
    executables=executables,
)
