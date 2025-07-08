from PySide6.QtGui import QPixmap
from PySide6.QtCore import QObject, Signal

class Controls(QObject):
    send_control_signal = Signal(bytes)
    def __init__(self, ui, communication):
        super().__init__()
        self.ui = ui
        # self.communication = communication

    def changeAttTxControls(self, index):
        for i in range(1, 9):
            getattr(self.ui, f'attTxCh{i}').setCurrentIndex(index)
           
    def changeAttRxControls(self, index):      
        for i in range(1, 9):
            getattr(self.ui, f'attRxCh{i}').setCurrentIndex(index)

    def changePhTxControls(self, index):
        for i in range(1, 9):
            getattr(self.ui, f'phTxCh{i}').setCurrentIndex(index)

    def changePhRxControls(self, index):
        for i in range(1, 9):
            getattr(self.ui, f'phRxCh{i}').setCurrentIndex(index)

    def toggleControls(self, cmd):
        controls = [
            self.ui.attTxAllCh, self.ui.attRxAllCh, self.ui.phTxAllCh, self.ui.phRxAllCh,
            self.ui.lblAttTx, self.ui.lblAttRx, self.ui.lblPhTx, self.ui.lblPhRx
        ]
        if cmd in (1, 2):
            for ctrl in controls:
                ctrl.hide()
        else:
            for ctrl in controls:
                ctrl.show()

    def getStatus(self):

        data = [ 0x33, 0x01, 0x00, 0x00, 0x00, 0xBB ]

        # data = [ 0xAA, 0xFF, 0xFF,  0xAB, 0x3C,
        #         0xAB, 0x3C, 0xAB, 0x3C,
        #         0xAB, 0x3C, 0xAB, 0x3C,
        #         0xAB, 0x3C, 0xAB, 0x3C,
        #         0xAB, 0x3C, 0xAB, 0x3C,
        #         0xAB, 0x3C, 0xAB, 0x3C,
        #         0xAB, 0x3C, 0xAB, 0x3C,
        #         0xAB, 0x3C, 0xAB, 0x3C,
        #         0xBB ]

        data_bytes = bytes(data)
        # self.communication.sendControl(data_bytes)
        self.send_control_signal.emit(data_bytes)

    def getIsolation(self, cmd, channel):

        # Dwell
        if cmd == 0:
            tx_attenuations = [getattr(self.ui, f'attTxCh{i}').currentIndex() for i in range(1, 9)]
            tx_phases = [getattr(self.ui, f'phTxCh{i}').currentIndex() for i in range(1, 9)]
            rx_attenuations = [getattr(self.ui, f'attRxCh{i}').currentIndex() for i in range(1, 9)]
            rx_phases = [getattr(self.ui, f'phRxCh{i}').currentIndex() for i in range(1, 9)]
            data = [0xAA, cmd + 1, channel, 0x00, 0x00, *tx_attenuations, 0x00, *rx_attenuations, 0x00, *tx_phases, 0x00, *rx_phases, 0xBB]

        # Tx Calibration
        elif cmd == 1:
            if 0 <= channel <= 7:
                att = getattr(self.ui, f'attTxCh{channel+1}').currentIndex()
                ph = getattr(self.ui, f'phTxCh{channel+1}').currentIndex()
                data = [0xAA, cmd + 1, channel, 0x00, 0x00, att, ph, 0xBB]
        
        # Rx Calibration
        elif cmd == 2:
            if 0 <= channel <= 7:
                att = getattr(self.ui, f'attRxCh{channel+1}').currentIndex()
                ph = getattr(self.ui, f'phRxCh{channel+1}').currentIndex()
                data = [0xAA, cmd + 1, channel, 0x00, 0x00, att, ph, 0xBB]
                      
        # Tx Pattern
        elif cmd == 3:
            tx_attenuations = [getattr(self.ui, f'attTxCh{i}').currentIndex() for i in range(1, 9)]
            tx_phases = [getattr(self.ui, f'phTxCh{i}').currentIndex() for i in range(1, 9)]
            data = [0xAA, cmd + 1, channel, 0x00, 0x00, *tx_attenuations, 0x00, *tx_phases, 0xBB]
                   
        # Rx Pattern    
        elif cmd == 4: 
            rx_attenuations = [getattr(self.ui, f'attRxCh{i}').currentIndex() for i in range(1, 9)]
            rx_phases = [getattr(self.ui, f'phRxCh{i}').currentIndex() for i in range(1, 9)]            
            data = [0xAA, cmd + 1, channel, 0x00, 0x00, *rx_attenuations, 0x00, *rx_phases, 0xBB]

        # Isolation
        elif cmd == 5:
            data = [0xAA, cmd + 1, channel, 0x00, 0x00, 0xBB]

        else:
            print("Invalid command")
            return
        
        data_bytes = bytes(data)
        
        # self.communication.sendControl(data_bytes)
        self.send_control_signal.emit(data_bytes)

    def handle_received_data(self, data):
        if not self._should_process:
            print("Received data ignored (waiting for btnGetStatus)")
            return

        print(f"Processing received data: {data}")
        self._should_process = False

        fpRf = data[1]
        fpLf = data[2]
        tempLeft1 = data[3:5]
        tempRight1 = data[5:7]
        tempLeft2 = data[7:9]
        tempRight2 = data[9:11]
        tempPs = data[11:13]
        tempFPGA = data[13:15]
        current = data[15:17]
        v48Mon1 = data[17:19]
        v48Mon2 = data[19:21]
        v5Mon1 = data[21:23]
        v5Mon2 = data[23:25]
        v45Mon2 = data[25:27]

        self.updateField(tempLeft1, self.ui.leftTemp1)
        self.updateField(tempRight1, self.ui.rightTemp1)
        self.updateField(tempLeft2, self.ui.leftTemp2)
        self.updateField(tempRight2, self.ui.rightTemp2)
        self.updateField(tempPs, self.ui.psTemp)
        self.updateField(tempFPGA, self.ui.fpgaTemp)
        self.updateField(current, self.ui.current, suffix="A")
        self.updateField(v48Mon1, self.ui.v48M1, suffix="V")
        self.updateField(v48Mon2, self.ui.v48M2, suffix="V")
        self.updateField(v5Mon1, self.ui.v5Mon1, suffix="V")
        self.updateField(v5Mon2, self.ui.v5Mon2, suffix="V")
        self.updateField(v45Mon2, self.ui.v45Mon, suffix="V")
          
        self.updateIcons(fpRf, [
            self.ui.fpRl1, self.ui.fpRl2, self.ui.fpRl3, self.ui.fpRl4,
            self.ui.fpRl5, self.ui.fpRl6, self.ui.fpRl7, self.ui.fpRl8,
        ])
        self.updateIcons(fpLf, [
            self.ui.fpLf1, self.ui.fpLf2, self.ui.fpLf3, self.ui.fpLf4,
            self.ui.fpLf5, self.ui.fpLf6, self.ui.fpLf7, self.ui.fpLf8,
        ])
        

    def updateIcons(self, sys, labels):
        """ Updates multiple labels based on bit positions and prints the bit position. """
        for i, label in enumerate(labels):
            status = (sys >> i) & 1
            print(f"Bit position {i}: {status}")
            self.update_status(label, status)

    def update_status(self, label, status):
        icon_path = u":/resources/Ok.png" if status else u":/resources/Error.png"
        label.setPixmap(QPixmap(icon_path))

    def updateField(self, temps, label_field, suffix="°C"):
        first_byte = temps[0]                # 0xAB
        second_byte_4bits = temps[1] & 0x0F  # 0x3C & 0x0F = 0x0C

        combined = (first_byte << 4) | second_byte_4bits
        # self.ui.leftTemp1.setText(f"{combined:.2f}") # '2748.00'
        # self.ui.leftTemp1.setText(f"{combined / 100:.2f} °C") # '27.48'
        label_field.setText(f"{combined / 100:.2f} {suffix}")




    