from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from widget_app.window import WidgetWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Personal System Widget")
    window = WidgetWindow()
    window.show()
    return app.exec()
