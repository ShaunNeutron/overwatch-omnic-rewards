from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import argparse
import logging
import os
import sys

from stats import Stats
from settings import SettingsManager
from systemtray import SystemTray

logger = logging.getLogger(__name__)


def main():
    options, qt_args = arg_parse()
    application_path = get_application_path()
    configure_logging(options, application_path)

    config_location = os.path.join(application_path, options.config)  # config.json
    history_location = os.path.join(application_path, options.history)  # history.csv

    settings = SettingsManager(config_location)
    stats = Stats(history_location)

    app = QApplication(sys.argv[:1] + qt_args)

    logger.debug(f'QT Desktop session: sessionId="{app.sessionId()}", sessionKey="{app.sessionKey()}"')

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, 'System tray not found', 'Can\'t start app. No system tray found')
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    if options.debug:
        set_local_urls()

    # Create the tray
    tray = SystemTray(settings, stats, quiet_mode=options.quiet, parent=app)
    app.aboutToQuit.connect(tray.prepare_to_exit)
    app.commitDataRequest.connect(tray.prepare_to_exit)

    app.setApplicationName("overwatch-omnic-rewards")
    app.setApplicationVersion("1.1.3")

    app.exec_()


def arg_parse():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    group.add_argument("-l", "--log", default="warning", help="Provide logging level")
    parser.add_argument("-fl", "--file-log", nargs='?', const="omnic.log",
                        help="Writes logs to a file. Will write to 'omnic.log' when no filename is provided")
    parser.add_argument("-q", "--quiet", help="Quiet mode. No system tray", action="store_true")
    parser.add_argument("-d", "--debug",
                        help="Debug Mode. Switches URL's endpoints to local ones for testing. See docs",
                        action="store_true")
    parser.add_argument("-cf", "--config", default="config.json",
                       help="Specify config file. Needs to be in the same dir as app")
    parser.add_argument("-hf", "--history", default="history.csv",
                       help="Specify history file. Needs to be in the same dir as app")

    options, qt_args = parser.parse_known_args()

    return options, qt_args


def configure_logging(options, application_path: str):
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }
    if options.verbose:
        level = levels.get('info')
    else:
        level = levels.get(options.log.lower())
    if level is None:
        raise ValueError(
            f"log level given: {options.log}"
            f" -- must be one of: {' | '.join(levels.keys())}")

    log_handlers = []

    stream_handler = logging.StreamHandler(sys.stdout)
    log_handlers.append(stream_handler)

    if options.file_log:
        file_handler = logging.FileHandler(os.path.join(application_path, options.file_log))
        file_handler.setFormatter(logging.Formatter("[%(asctime)s]" + logging.BASIC_FORMAT))
        log_handlers.append(file_handler)

    logging.basicConfig(handlers=log_handlers, level=level)


def get_application_path() -> str:
    # PyInstaller fix for application path
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(__file__)

def set_local_urls():
    logger.info("Using Local endpoints")
    import utils.checker as checker
    from utils.viewer import Viewer
    checker.OWL_URL = "http://127.0.0.1:5000/owlpage"
    checker.OWC_URL = "http://127.0.0.1:5000/owcpage"
    Viewer.TRACKING_OWL = "http://127.0.0.1:5000/owl"
    Viewer.TRACKING_OWC = "http://127.0.0.1:5000/owc"


if __name__ == "__main__":
    main()
