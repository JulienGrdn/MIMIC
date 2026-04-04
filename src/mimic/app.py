import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from mimic.logger import configure_logging
from mimic.main_window import MainWindow


def main() -> None:
    configure_logging()

    # All config paths in the application are relative to the repo root
    # (config/ui_parameters.json, config/devices_configuration.yaml, etc.)
    # Ensure CWD is the repo root regardless of where the entry-point is invoked from.
    repo_root = Path(__file__).parent.parent.parent
    os.chdir(repo_root)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
