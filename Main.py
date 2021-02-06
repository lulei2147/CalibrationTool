import sys
from PyQt5.Qt import *
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from UI.MainUi import Ui_MainWindow
from UI.portConfig import Ui_Dialog
import binascii
import math


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
        self.RevData = {'CmdHeader': '', 'CmdData': ''}
        self.RevDataLoadPara_A0 = {'LowLimit': '', 'UpperLimit': '', 'Unit': '', 'DAP': '', 'P-L': '', 'P-H': ''}
        QssTools.setQssToObj('./proQss.qss', self)

        self.portconfig = PortConfigUI()
        self.port = QSerialPort()
        self.pte_InfoOutput.insertPlainText('当前端口: ' + self.portconfig.cbox_port.currentText() + '\n')
        self.current_port = self.portconfig.cbox_port.currentText()
        self.port.readyRead.connect(self.portReceiveData)

        self.pte_InfoOutput.textChanged.connect(self.pte_InfoOutput.ensureCursorVisible)

        # USART data buffer from MCU
        self.dataBuffer = b''

        self.drawCheckBoxInTableWidget()

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
            rxData = binascii.b2a_hex(bytes(self.port.readAll()))
            self.dataBuffer = self.dataBuffer + rxData

            if len(self.dataBuffer) >= 2:
                # Wait for the data reception to complete, the byte stream ends with ‘\r\n’
                if self.dataBuffer[-2:] == b'0a' and self.dataBuffer[-4:-2] == b'0d':
                    print(self.dataBuffer)
                    self.RevData['CmdHeader'] = self.dataBuffer[0:2]
                    self.RevData['CmdData'] = self.dataBuffer[2:-4]
                    self.dataBuffer = b''

                    self.RevDataLoadPara_A0['LowLimit'] = self.RevData['CmdData'][0:2]
                    self.RevDataLoadPara_A0['UpperLimit'] = self.RevData['CmdData'][2:4]
                    self.RevDataLoadPara_A0['Unit'] = self.RevData['CmdData'][4:6]
                    self.RevDataLoadPara_A0['DAP'] = self.RevData['CmdData'][6:8]
                    self.RevDataLoadPara_A0['P-L'] = self.RevData['CmdData'][8:12]
                    self.RevDataLoadPara_A0['P-L_Decimal'] = self.RevData['CmdData'][12:14]
                    self.RevDataLoadPara_A0['P-H'] = self.RevData['CmdData'][14:18]
                    self.RevDataLoadPara_A0['P-H_Decimal'] = self.RevData['CmdData'][18:20]

                    self.cmdHandler()
        except:
            pass
            # QMessageBox.critical(self, "错误", "串口接收数据错误！")

    def cmdHandler(self):
        # Load system data from MCU
        if self.RevData['CmdHeader'] == b'a0':
            # lower and upper limit
            upperLimit = self.RevDataLoadPara_A0['UpperLimit']
            lowerLimit = self.RevDataLoadPara_A0['LowLimit']
            self.tableWidget.item(0, 2).setText(str(float(int(upperLimit, 16)) / 10))
            self.tableWidget.item(1, 2).setText(str(float(int(lowerLimit, 16)) / 10))

            # unit
            # b'00':PSI, b'01':BAR
            unit = self.RevDataLoadPara_A0['Unit']
            if unit == b'01':
                self.cbox_Unit.setCurrentText('bar')
            elif unit == b'00':
                self.cbox_Unit.setCurrentText('psi')
            else:
                self.pte_InfoOutput.insertPlainText("加载单位(Unit)错误!" + '\n')

            # DAP
            dap = self.RevDataLoadPara_A0['DAP']
            self.tableWidget.item(3, 2).setText(str(int(dap, 16)))

            # P-L
            PLVal = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['P-L'])[::-1])
            PLDecimal = self.RevDataLoadPara_A0['P-L_Decimal']
            print(PLDecimal)
            if PLDecimal == b'01':
                self.tableWidget.item(4, 2).setText(format(float(int(PLVal, 16)) / pow(10, 1), '.1f'))
            elif PLDecimal == b'02':
                self.tableWidget.item(4, 2).setText(format(float(int(PLVal, 16)) / pow(10, 2), '.2f'))
            elif PLDecimal == b'03':
                self.tableWidget.item(4, 2).setText(format(float(int(PLVal, 16)) / pow(10, 3), '.3f'))
            elif PLDecimal == b'04':
                self.tableWidget.item(4, 2).setText(format(float(int(PLVal, 16)) / pow(10, 0), '.0f'))

            # P-H
            PHVal = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['P-H'])[::-1])
            PHDecimal = self.RevDataLoadPara_A0['P-H_Decimal']
            print(PHVal)
            if PHDecimal == b'01':
                self.tableWidget.item(5, 2).setText(format(float(int(PHVal, 16)) / pow(10, 1), '.1f'))
            elif PHDecimal == b'02':
                self.tableWidget.item(5, 2).setText(format(float(int(PHVal, 16)) / pow(10, 2), '.2f'))
            elif PHDecimal == b'03':
                self.tableWidget.item(5, 2).setText(format(float(int(PHVal, 16)) / pow(10, 3), '.3f'))
            elif PHDecimal == b'04':
                self.tableWidget.item(5, 2).setText(format(float(int(PHVal, 16)) / pow(10, 0), '.0f'))


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

    def drawCheckBoxInTableWidget(self):
        # add checkbox to tablewidget
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # lower limit
        self.chkBox_lowerlimit = QCheckBox()
        hLayout0 = QHBoxLayout()
        hLayout0.addWidget(self.chkBox_lowerlimit)
        hLayout0.setAlignment(self.chkBox_lowerlimit, Qt.AlignCenter)
        widget0 = QWidget()
        widget0.setLayout(hLayout0)
        self.tableWidget.setCellWidget(0, 0, widget0)
        # upper limit
        self.chkBox_upperlimit = QCheckBox()
        hLayout1 = QHBoxLayout()
        hLayout1.addWidget(self.chkBox_upperlimit)
        hLayout1.setAlignment(self.chkBox_upperlimit, Qt.AlignCenter)
        widget1 = QWidget()
        widget1.setLayout(hLayout1)
        self.tableWidget.setCellWidget(1, 0, widget1)
        # unit
        self.chkBox_Unit = QCheckBox()
        hLayout2 = QHBoxLayout()
        hLayout2.addWidget(self.chkBox_Unit)
        hLayout2.setAlignment(self.chkBox_Unit, Qt.AlignCenter)
        widget2 = QWidget()
        widget2.setLayout(hLayout2)
        self.tableWidget.setCellWidget(2, 0, widget2)
        self.cbox_Unit = QComboBox()
        self.tableWidget.setCellWidget(2, 2, self.cbox_Unit)
        self.cbox_Unit.addItems(['bar', 'psi'])
        self.cbox_Unit.setCurrentIndex(-1)
        # DAP
        self.chkBox_DAP = QCheckBox()
        hLayout3 = QHBoxLayout()
        hLayout3.addWidget(self.chkBox_DAP)
        hLayout3.setAlignment(self.chkBox_DAP, Qt.AlignCenter)
        widget3 = QWidget()
        widget3.setLayout(hLayout3)
        self.tableWidget.setCellWidget(3, 0, widget3)
        # P-L
        self.chkBox_PL = QCheckBox()
        hLayout4 = QHBoxLayout()
        hLayout4.addWidget(self.chkBox_PL)
        hLayout4.setAlignment(self.chkBox_PL, Qt.AlignCenter)
        widget4 = QWidget()
        widget4.setLayout(hLayout4)
        self.tableWidget.setCellWidget(4, 0, widget4)
        # P-H
        self.chkBox_PH = QCheckBox()
        hLayout5 = QHBoxLayout()
        hLayout5.addWidget(self.chkBox_PH)
        hLayout5.setAlignment(self.chkBox_PH, Qt.AlignCenter)
        widget5 = QWidget()
        widget5.setLayout(hLayout5)
        self.tableWidget.setCellWidget(5, 0, widget5)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainUI()
    win.show()
    sys.exit(app.exec_())
