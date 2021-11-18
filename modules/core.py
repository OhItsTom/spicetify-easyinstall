import os
import shutil
import asyncio
import tempfile
from pathlib import Path

from modules import globals, utils


async def install(launch=False):
    steps_count = 8
    user_profile = os.path.expanduser("~")  # Vars
    appdata_local = os.environ["LOCALAPPDATA"]
    appdata = os.environ["APPDATA"]
    temp = tempfile.gettempdir()
    spotify_prefs = Path(user_profile + "\\AppData\\Roaming\\Spotify\\prefs")
    folders = [
        (user_profile + "\\spicetify-cli"),
        (user_profile + "\\.spicetify"),
        (appdata_local + "\\spotify"),
        (appdata + "\\spotify"),
        (temp),
    ]

    print(f"(1/{steps_count}) Uninstalling Spotify...")  # Section 1
    if os.path.isdir(appdata + "\\Spotify"):
        utils.kill_processes("Spotify.exe")
        await utils.powershell(
            'cmd /c "%USERPROFILE%\\AppData\\Roaming\\Spotify\\Spotify.exe" /UNINSTALL /SILENT\ncmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:D\ncmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:R',
            verbose=False,
        )
        print("Finished uninstalling Spotify!\n")
    else:
        print("Spotify is not installed!\n")

    print(f"(2/{steps_count}) Wiping folders...")  # Section 2
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                utils.verbose_print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                utils.verbose_print(f'"{folder}" has been deleted.')
        except Exception as e:
            utils.verbose_print(f'"{folder}" was not deleted: {e}.')
    print("Finished wiping folders!\n")

    print(f"(3/{steps_count}) Downloading correct Spotify version...")  # Section 3
    if not os.path.isdir(temp):
        os.mkdir(temp)
    await utils.chunked_download(
        url=globals.FULL_SETUP_URL,
        path=(temp + globals.INSTALLER_NAME),
        label=(temp + globals.INSTALLER_NAME) if globals.verbose else globals.INSTALLER_NAME[1:],
    )
    print("Finished downloading Spotify!\n")

    print(f"(4/{steps_count}) Installing Spotify...")  # Section 4
    utils.kill_processes("Spotify.exe")
    spotify_install_pid = utils.start_process(
        temp + globals.INSTALLER_NAME, silent=True
    ).pid
    while utils.process_pid_running(spotify_install_pid):
        await asyncio.sleep(0.25)
    i = 0
    while not spotify_prefs.is_file():
        i += 1
        if i > 40:
            raise FileNotFoundError(
                "Spotify preferences were not created, something went wrong installing."
            )
        await asyncio.sleep(0.25)
    utils.kill_processes("Spotify.exe")
    os.remove(temp + globals.INSTALLER_NAME)
    print("Finished installing Spotify!\n")

    print(f"(5/{steps_count}) Installing Spicetify...")  # Section 5
    await utils.powershell(
        "$ProgressPreference = 'SilentlyContinue'\n$v='%s'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/khanhas/spicetify-cli/master/install.ps1' | Invoke-Expression\nspicetify\nspicetify -n backup apply enable-devtool"
        % globals.SPICETIFY_VERSION
    )
    print("Finished installing Spicetify!\n")

    print(f"(6/{steps_count}) Preventing Spotify from updating...")  # Section 6
    utils.kill_processes("Spotify.exe")
    if not os.path.isdir(appdata_local + "\\Spotify\\Update"):
        os.mkdir(appdata_local + "\\Spotify\\Update")
    await utils.powershell(
        "cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D\ncmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R"
    )
    print("Finished blocking Spotify updates!\n")

    print(f"(7/{steps_count}) Downloading themes...")  # Section 7
    shutil.rmtree(user_profile + "\\spicetify-cli\\Themes", ignore_errors=True)
    await utils.chunked_download(
        url=globals.DOWNLOAD_THEME_URL,
        path=(user_profile + "\\spicetify-cli\\Themes.zip"),
        label=(user_profile + "\\spicetify-cli\\Themes.zip") if globals.verbose else "Themes.zip",
    )
    print("Finished downloading themes!\n")

    print(f"(8/{steps_count}) Unpacking themes...")  # Section 8
    shutil.unpack_archive(
        user_profile + "\\spicetify-cli\\Themes.zip", user_profile + "\\spicetify-cli"
    )
    os.remove(user_profile + "\\spicetify-cli\\Themes.zip")
    os.rename(
        user_profile + "\\spicetify-cli" + globals.THEMES_EXTRACTED,
        user_profile + "\\spicetify-cli\\Themes",
    )
    for item in list(Path(user_profile + "\\spicetify-cli\\Themes").glob("*")):
        fullpath = str(item)
        if os.path.isdir(fullpath):
            filename = str(item.name)
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)
    os.rename(
        user_profile + "\\spicetify-cli\\Themes\\Default",
        user_profile + "\\spicetify-cli\\Themes\\SpicetifyDefault",
    )
    for item in list(Path(user_profile + "\\spicetify-cli\\Themes").glob("**/*.js")):
        fullpath = str(item)
        destpath = user_profile + "\\spicetify-cli\\Extensions" + fullpath[fullpath.rfind("\\"):fullpath.rfind(".")] + "Theme.js"
        if os.path.exists(destpath):
            os.remove(destpath)
        shutil.move(fullpath, destpath)
    print("Finished unpacking themes!\n")

    if launch:
        utils.start_process(appdata + "\\spotify\\spotify.exe", silent=False)


async def apply_config(theme, colorscheme, extensions, customapps):
    steps_count = 2

    print(f"(1/{steps_count}) Setting options...")  # Section 1
    utils.set_config_entry("current_theme", theme)
    utils.set_config_entry("color_scheme", colorscheme)
    utils.set_config_entry(
        "extensions", "|".join(extension + ".js" for extension in extensions)
    )

    utils.set_config_entry("custom_apps", "|".join(customapps))
    print("Finished setting options!\n")

    print(f"(2/{steps_count}) Applying config...")  # Section 2
    await utils.powershell("spicetify apply -n")
    await utils.powershell("spicetify restart", wait=False, verbose=False)
    print("Finished applying config!\n")


async def uninstall():
    steps_count = 1
    user_profile = os.path.expanduser("~")  # Vars
    temp = "C:\\Users\\WDAGUtilityAccount\\AppData\\Local\\temp"
    folders = [
        (user_profile + "\\spicetify-cli"),
        (user_profile + "\\.spicetify"),
        (temp),
    ]

    print(f"(1/{steps_count}) Wiping folders...")  # Section 1
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                utils.verbose_print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                utils.verbose_print(f'"{folder}" has been deleted.')
        except Exception as e:
            utils.verbose_print(f'"{folder}" was not deleted: {e}.')
    print("Finished wiping folders!\n")
    # subprocess.Popen( #Delete ENV VAR
    # ["powershell", 'cmd /c setx Path '])

    # End of the terminal page
    # Needs rewriting


async def update_addons(addon_type):
    steps_count = 3
    if addon_type in ["shipped", "latest"]:
        download_url = globals.DOWNLOAD_THEME_URL
    user_profile = os.environ["USERPROFILE"]
    folders = [
        (user_profile + "\\spicetify-cli\\Themes"),
    ]

    print(f"(1/{steps_count}) Wiping old themes...")  # Section 1
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                utils.verbose_print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                utils.verbose_print(f'"{folder}" has been deleted.')
        except Exception as e:
            utils.verbose_print(f'"{folder}" was not deleted: {e}.')
    print("Finished wiping old themes!\n")

    print(f"(2/{steps_count}) Downloading {addon_type} themes...")  # Section 2
    await utils.chunked_download(
        url=download_url,
        path=(user_profile + "\\spicetify-cli\\Themes.zip"),
        label=(user_profile + "\\spicetify-cli\\Themes.zip") if globals.verbose else "Themes.zip",
    )
    print(f"Finished downloading {addon_type} themes!\n")

    print(f"(3/{steps_count}) Unpacking new themes...")  # Section 3
    shutil.unpack_archive(
        user_profile + "\\spicetify-cli\\Themes.zip", user_profile + "\\spicetify-cli"
    )
    os.remove(user_profile + "\\spicetify-cli\\Themes.zip")
    os.rename(
        user_profile + "\\spicetify-cli" + globals.THEMES_EXTRACTED,
        user_profile + "\\spicetify-cli\\Themes",
    )
    for item in list(Path(user_profile + "\\spicetify-cli\\Themes").glob("*")):
        fullpath = str(item)
        if os.path.isdir(fullpath):
            filename = str(item.name)
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)
    os.rename(
        user_profile + "\\spicetify-cli\\Themes\\Default",
        user_profile + "\\spicetify-cli\\Themes\\SpicetifyDefault",
    )
    for item in list(Path(user_profile + "\\spicetify-cli\\Themes").glob("**/*.js")):
        fullpath = str(item)
        destpath = user_profile + "\\spicetify-cli\\Extensions" + fullpath[fullpath.rfind("\\"):fullpath.rfind(".")] + "Theme.js"
        if os.path.exists(destpath):
            os.remove(destpath)
        shutil.move(fullpath, destpath)
    print("Finished unpacking new themes!\n")
