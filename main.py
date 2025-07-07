import sys
from PySide6.QtWidgets import QApplication, QWidget
from ui_trm_controller import TrmController


if __name__ == "__main__":
    app = QApplication([])
    trmController = TrmController()
    trmController.show()
    sys.exit(app.exec())
