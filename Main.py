import sys
from PyQt5.Qt import *
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from UI.MainUi import Ui_MainWindow
from UI.portConfig import Ui_Dialog
import binascii


class QssTools(object):
    @classmethod
    def setQssToObj(cls, file_path, obj):
        with open(file_path, 'r') as f:
            obj.setStyleSheet(f.read())


class PortConfigUI(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUi()
        self.searchPort()

    def initUi(self):
        # USART Parameters
        self.cbox_baudrate.addItems(['9600', '115200'])
        self.cbox_databit.addItems(['8'])
        self.cbox_paritybit.addItems(['None'])
        self.cbox_stopbit.addItems(['One'])

    def searchPort(self):
        self.cbox_port.clear()
        port_list = QSerialPortInfo.availablePorts()
        for info in port_list:
            self.cbox_port.addItem(info.portName())


class MainUI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        self.setupUi(self)
        self.CmdId = {'GetParam': 'A0', 'SetParam': 'A1', 'GetADCVal': 'A5'}
        QssTools.setQssToObj('./proQss.qss', self)

        self.portconfig = PortConfigUI()
        self.port = QSerialPort()
        self.pte_InfoOutput.insertPlainText('当前端口: ' + self.portconfig.cbox_port.currentText() + '\n')
        self.current_port = self.portconfig.cbox_port.currentText()
        self.port.readyRead.connect(self.portReceiveData)

        self.pte_InfoOutput.textChanged.connect(self.pte_InfoOutput.ensureCursorVisible)

        # USART data buffer from MCU
        self.dataBuffer = []

        self.drawTableWidgetParamItem()

        self.bytesNum = 0

    def drawTableWidgetParamItem(self):
        # add checkbox to tablewidget
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.chkBox1 = QCheckBox()
        hLayout1 = QHBoxLayout()
        hLayout1.addWidget(self.chkBox1)
        hLayout1.setAlignment(self.chkBox1, Qt.AlignCenter)
        widget1 = QWidget()
        widget1.setLayout(hLayout1)
        self.tableWidget.setCellWidget(0, 0, widget1)

        self.chkBox2 = QCheckBox()
        hLayout2 = QHBoxLayout()
        hLayout2.addWidget(self.chkBox2)
        hLayout2.setAlignment(self.chkBox2, Qt.AlignCenter)
        widget2 = QWidget()
        widget2.setLayout(hLayout2)
        self.tableWidget.setCellWidget(1, 0, widget2)

        # self.chkBox3 = QCheckBox()
        # hLayout3 = QHBoxLayout()
        # hLayout3.addWidget(self.chkBox3)
        # hLayout3.setAlignment(self.chkBox3, Qt.AlignCenter)
        # widget3 = QWidget()
        # widget3.setLayout(hLayout3)
        # self.tableWidget.setCellWidget(2, 0, widget3)

    def btnPortConfigClicked(self):
        selected = self.portconfig.exec()

        if selected == QDialog.Accepted:
            self.current_port = self.portconfig.cbox_port.currentText()
            self.pte_InfoOutput.insertPlainText('当前端口: ' + self.portconfig.cbox_port.currentText() + '\n')
        else:
            print('NO')
        # QAction

    def btnOpenPortClicked(self):
        if self.current_port == '':
            QMessageBox.warning(self, "警告", "端口配置失败！")
            return

        self.port.setPortName(self.current_port)
        if self.port.open(QSerialPort.ReadWrite):
            self.btn_portstatus.setStyleSheet("background-color: rgb(255, 99, 52)")
            self.pte_InfoOutput.insertPlainText("端口打开！" + '\n')

    def btnClosePortClicked(self):
        self.port.close()
        self.btn_portstatus.setStyleSheet("background-color: gray;")
        self.pte_InfoOutput.insertPlainText("端口关闭！" + '\n')

    def portReceiveData(self):
        try:
            #rxData = (bytes(self.port.readAll())).decode('UTF-8')
            #self.pte_InfoOutput.insertPlainText(rxData)

            rxData = binascii.b2a_hex(bytes(self.port.readAll()))
            self.dataBuffer.append(rxData)
        except:
            pass
            # QMessageBox.critical(self, "错误", "串口接收数据错误！")

        if len(self.dataBuffer) >= 2:
            # Wait for the data reception to complete, the byte stream ends with ‘\r\n’
            if self.dataBuffer[-1] == b'0a' and self.dataBuffer[-2] == b'0d':
                print(self.dataBuffer)
                self.dataBuffer.clear()



    def btnGetADCValue(self):
        try:
            self.port.write(binascii.a2b_hex(self.CmdId['GetADCVal']))
        except:
            self.pte_InfoOutput.insertPlainText("串口发送失败！" + '\n')

        #print(self.port.isOpen())

    def btnQueryParametersClicked(self):
        self.port.write(binascii.a2b_hex(self.CmdId['GetParam']))

    def btnSetParametersClicked(self):
        self.port.write(binascii.a2b_hex(self.CmdId['SetParam']))

    def widgetStatusRefresh(self):
        if self.port.isOpen():
            self.btn_portConfig.setDisabled()
        else:
            self.btn_portConfig.setEnabled()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainUI()
    win.show()
    sys.exit(app.exec_())
