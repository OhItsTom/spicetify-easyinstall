#  ______  ______  __  ______  ______  ______  __  ______  __  __         ______  ______  ______  __  __  __  __   __  ______  ______  ______  __      __
# /\  ___\/\  == \/\ \/\  ___\/\  ___\/\__  _\/\ \/\  ___\/\ \_\ \       /\  ___\/\  __ \/\  ___\/\ \_\ \/\ \/\ "-.\ \/\  ___\/\__  _\/\  __ \/\ \    /\ \
# \ \___  \ \  _-/\ \ \ \ \___\ \  __\\/_/\ \/\ \ \ \  __\\ \____ \      \ \  __\\ \  __ \ \___  \ \____ \ \ \ \ \-.  \ \___  \/_/\ \/\ \  __ \ \ \___\ \ \____
#  \/\_____\ \_\   \ \_\ \_____\ \_____\ \ \_\ \ \_\ \_\   \/\_____\      \ \_____\ \_\ \_\/\_____\/\_____\ \_\ \_\\"\_\/\_____\ \ \_\ \ \_\ \_\ \_____\ \_____\
#   \/_____/\/_/    \/_/\/_____/\/_____/  \/_/  \/_/\/_/    \/_____/       \/_____/\/_/\/_/\/_____/\/_____/\/_/\/_/ \/_/\/_____/  \/_/  \/_/\/_/\/_____/\/_____/

import asyncio
import sys

# Only start if running as main and not import
if __name__ == "__main__":
    # Setup logging console to file output
    from modules import logger

    # Sanity check: try importing all needed third party libs
    from PyQt5 import QtCore, QtGui, QtWidgets
    from qasync import asyncSlot, QEventLoop
    import win32api, win32event, winerror
    import aiofiles
    import aiohttp
    import psutil

    # Sanity checck: try importing all local modules
    from modules import globals, core, gui, progress, screens, singleton, utils

    # Setup singleton: only one app instance running at a time
    globals.singleton = singleton.Singleton("spicetify-easyinstall")

    # Create App
    globals.app = QtWidgets.QApplication(sys.argv)
    globals.app.setStyleSheet(gui.QSS)

    # Configure asyncio loop to work with PyQt5
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = QEventLoop(globals.app)
    asyncio.set_event_loop(loop)

    # Setup GUI
    globals.gui = gui.MainWindow()
    globals.gui.show()
    
    # Set off loop
    with loop:
        sys.exit(loop.run_until_complete(globals.gui.exit_request.wait()))