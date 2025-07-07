from PySide6.QtWidgets import QComboBox, QMessageBox
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QPixmap
import serial
import serial.tools.list_ports
import time

class SerialReader(QObject):
    data_received = Signal(bytes)
    error = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self._running = True

    def run(self):
        while self._running:
            try:
                if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    if data:
                        self.data_received.emit(data)
                time.sleep(0.05)  # avoid busy loop
            except Exception as e:
                self.error.emit(str(e))
                break

    def stop(self):
        self._running = False

class Communication(QObject):
    data_received_signal = Signal(bytes)

    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.serial_port = None
        self.reader_thread = None
        self.reader_worker = None

    def update_com_ports(self):
        self.ui.comPort.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ui.comPort.addItem(port.device)
        QComboBox.showPopup(self.ui.comPort)

    def setConnection(self, com_port, baud_rate):
        try:
            # Close previous connection if open
            if self.serial_port and self.serial_port.is_open:
                self.stop_reader()
                self.serial_port.close()
                print("Previous serial port closed.")

            self.serial_port = serial.Serial(port=com_port, baudrate=int(baud_rate), timeout=1)
            if self.serial_port.is_open:
                print("Serial port opened successfully")
                self.ui.connect.setText("Connected")
                self.ui.connect.setStyleSheet(
                    "QPushButton {"
                    "   background-color: green;"
                    "   color: black;"
                    "   border: none;"
                    "   height: 35px;"
                    "   border-radius: 5px;"
                    "   font-size: 16px;"
                    "}"
                )
                QMessageBox.information(None, "Connection", f"Connected to {com_port} successfully!")
                self.start_reader()
            else:
                print("Failed to open serial port")
                self.ui.connect.setText("Connect")
                self.ui.connect.setStyleSheet(
                    "QPushButton {"
                    "   background-color: orange;"
                    "   color: black;"
                    "   border: none;"
                    "   height: 35px;"
                    "   border-radius: 5px;"
                    "   font-size: 16px;"
                    "}"
                )
                QMessageBox.warning(None, "Connection", f"Failed to connect to {com_port}.")
                self.set_all_icons_off()
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.ui.connect.setText("Connect")
            self.ui.connect.setStyleSheet(
                "QPushButton {"
                "   background-color: orange;"
                "   color: black;"
                "   border: none;"
                "   height: 35px;"
                "   border-radius: 5px;"
                "   font-size: 16px;"
                "}"
            )
            QMessageBox.warning(None, "Connection", f"Failed to connect to {com_port}.\n{e}")
            self.set_all_icons_off()

    def start_reader(self):
        self.stop_reader()  # Ensure previous thread is stopped
        self.reader_thread = QThread()
        self.reader_worker = SerialReader(self.serial_port)
        self.reader_worker.moveToThread(self.reader_thread)
        self.reader_thread.started.connect(self.reader_worker.run)
        self.reader_worker.data_received.connect(self.on_data_received)
        self.reader_worker.error.connect(self.on_reader_error)
        self.reader_thread.start()

    def stop_reader(self):
        if self.reader_worker:
            self.reader_worker.stop()
        if self.reader_thread:
            self.reader_thread.quit()
            self.reader_thread.wait()
        self.reader_worker = None
        self.reader_thread = None

    def sendControl(self, data):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(data)
            print("Control data sent")
        else:
            print("Serial port is not open")

    # This method is now handled by the thread, but you can still call it manually if needed
    def receive_data(self, num_bytes=1024):
        if self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.read(num_bytes)
                print(f"Received data: {data}")
                return data
            except serial.SerialException as e:
                print(f"Error reading data: {e}")
                return None
        else:
            print("Serial port is not open")
            return None

    def toggleConnection(self, com_port, baud_rate):
        if self.serial_port and self.serial_port.is_open:
            self.stop_reader()
            self.serial_port.close()
            print("Serial port closed.")
            self.ui.connect.setText("Connect")
            self.ui.connect.setStyleSheet(
                "QPushButton {"
                "   background-color: orange;"
                "   color: black;"
                "   border: none;"
                "   height: 35px;"
                "   border-radius: 5px;"
                "   font-size: 16px;"
                "}"
            )
            QMessageBox.information(None, "Connection", f"Disconnected from {com_port}.")
            self.set_all_icons_off()
        else:
            self.setConnection(com_port, baud_rate)

    def set_all_icons_off(self):
        off_icon = QPixmap(u":/resources/Off.png")
        for label in [
            self.ui.fpLf1, self.ui.fpLf2, self.ui.fpLf3, self.ui.fpLf4,
            self.ui.fpLf5, self.ui.fpLf6, self.ui.fpLf7, self.ui.fpLf8,
            self.ui.fpRl1, self.ui.fpRl2, self.ui.fpRl3, self.ui.fpRl4,
            self.ui.fpRl5, self.ui.fpRl6, self.ui.fpRl7, self.ui.fpRl8,
        ]:
            label.setPixmap(off_icon)

        for label in [
            self.ui.leftTemp1, self.ui.rightTemp1, self.ui.leftTemp2,
            self.ui.rightTemp2, self.ui.psTemp, self.ui.fpgaTemp, self.ui.current,
            self.ui.v48M1, self.ui.v48M2, self.ui.v5Mon1, self.ui.v5Mon2, self.ui.v45Mon
        ]:
            label.setText(".....")
        self.ui.textbox.clear()
        

    # Slot for received data
    def on_data_received(self, data):
        if data[0] == 0xAA and len(data) > 27: 
            self.data_received_signal.emit(data)
        else:
            print("Invalid data received", data)
            # QMessageBox.warning(None, "Error", f"Invalid data received.")

    # Slot for reader errors
    def on_reader_error(self, error):
        print(f"Serial read error: {error}")
        QMessageBox.warning(None, "Serial Error", error)