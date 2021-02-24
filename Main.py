import sys
from PyQt5.Qt import *
from PyQt5 import QtCore
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
        self.CmdId = {'GetParam': 'A0', 'SetParam': 'A1', 'GetADCVal': 'A5', 'KeyMessage': 'A6', 'RestoreFactory': 'A7'}
        self.RevData = {'CmdHeader': '', 'CmdData': ''}
        self.RevDataLoadPara_A0 = {'LowLimit': '', 'LowLimit_Decimal': '', 'UpperLimit': '', 'UpperLimit_Decimal': '',
                                   'Unit': '', 'DAP': '', 'P-L': '', 'P-L_Decimal': '', 'P-H': '', 'P-H_Decimal': '',
                                   'Func1': '', 'AL1': '', 'AL1_Decimal': '', 'AH1': '', 'AH1_Decimal': '', 'DL1': '',
                                   'Func2': '', 'AL2': '', 'AL2_Decimal': '', 'AH2': '', 'AH2_Decimal': '', 'DL2': ''}
        QssTools.setQssToObj('./proQss.qss', self)

        self.portconfig = PortConfigUI()
        self.port = QSerialPort()
        self.pte_InfoOutput.insertPlainText('当前端口: ' + self.portconfig.cbox_port.currentText() + '\n')
        self.current_port = self.portconfig.cbox_port.currentText()
        self.port.readyRead.connect(self.portReceiveData)

        self.pte_InfoOutput.textChanged.connect(self.pte_InfoOutput.ensureCursorVisible)

        # USART data buffer from MCU
        self.dataBuffer = b''

        # all selected flag
        self.allSelected = False

        self.drawCheckBoxInTableWidget()

        # signal
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.allSelectedClicked)

        # data index
        # Upper limit
        self.UpperLimitIndexStart = 0
        self.UpperLimitIndexEnd = self.UpperLimitIndexStart + MainUI.UpperLimitSize * 2
        self.UpperLimitDecimalIndexStart = self.UpperLimitIndexEnd
        self.UpperLimitDecimalIndexEnd = self.UpperLimitDecimalIndexStart + MainUI.UpperLimitDecimalSize * 2
        # Lower limit
        self.LowerLimitIndexStart = self.UpperLimitDecimalIndexEnd
        self.LowerLimitIndexEnd = self.LowerLimitIndexStart + MainUI.LowerLimitSize * 2
        self.LowerLimitDecimalIndexStart = self.LowerLimitIndexEnd
        self.LowerLimitDecimalIndexEnd = self.LowerLimitDecimalIndexStart + MainUI.LowerLimitDecimalSize * 2
        # Unit
        self.UnitIndexStart = self.LowerLimitDecimalIndexEnd
        self.UnitIndexEnd = self.UnitIndexStart + MainUI.UnitSize * 2
        # DAP
        self.DAPIndexStart = self.UnitIndexEnd
        self.DAPIndexEnd = self.DAPIndexStart + MainUI.DAPSize * 2
        # P-L
        self.PLIndexStart = self.DAPIndexEnd
        self.PLIndexEnd = self.PLIndexStart + MainUI.PLSize * 2
        self.PLDecimalIndexStart = self.PLIndexEnd
        self.PLDecimalIndexEnd = self.PLDecimalIndexStart + MainUI.PLDecimalSize * 2
        # P-H
        self.PHIndexStart = self.PLDecimalIndexEnd
        self.PHIndexEnd = self.PHIndexStart + MainUI.PHSize * 2
        self.PHDecimalIndexStart = self.PHIndexEnd
        self.PHDecimalIndexEnd = self.PHDecimalIndexStart + MainUI.PHDecimalSize * 2
        # Func1
        self.Func1IndexStart = self.PHDecimalIndexEnd
        self.Func1IndexEnd = self.Func1IndexStart + MainUI.Func1Size * 2
        # AL1
        self.AL1IndexStart = self.Func1IndexEnd
        self.AL1IndexEnd = self.AL1IndexStart + MainUI.AL1Size * 2
        self.AL1DecimalIndexStart = self.AL1IndexEnd
        self.AL1DecimalIndexEnd = self.AL1DecimalIndexStart + MainUI.AL1DecimalSize * 2
        # AH1
        self.AH1IndexStart = self.AL1DecimalIndexEnd
        self.AH1IndexEnd = self.AH1IndexStart + MainUI.AH1Size * 2
        self.AH1DecimalIndexStart = self.AH1IndexEnd
        self.AH1DecimalIndexEnd = self.AH1DecimalIndexStart + MainUI.AH1DecimalSize * 2
        # DL1
        self.DL1IndexStart = self.AH1DecimalIndexEnd
        self.DL1IndexEnd = self.DL1IndexStart + MainUI.DL1Size * 2
        # Func2
        self.Func2IndexStart = self.DL1IndexEnd
        self.Func2IndexEnd = self.Func2IndexStart + MainUI.Func2Size * 2
        # AL2
        self.AL2IndexStart = self.Func2IndexEnd
        self.AL2IndexEnd = self.AL2IndexStart + MainUI.AL2Size * 2
        self.AL2DecimalIndexStart = self.AL2IndexEnd
        self.AL2DecimalIndexEnd = self.AL2DecimalIndexStart + MainUI.AL2DecimalSize * 2
        # AH2
        self.AH2IndexStart = self.AL2DecimalIndexEnd
        self.AH2IndexEnd = self.AH2IndexStart + MainUI.AH2Size * 2
        self.AH2DecimalIndexStart = self.AH2IndexEnd
        self.AH2DecimalIndexEnd = self.AH2DecimalIndexStart + MainUI.AH2DecimalSize * 2
        # DL2
        self.DL2IndexStart = self.AH2DecimalIndexEnd
        self.DL2IndexEnd = self.DL2IndexStart + MainUI.DL2Size * 2

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

                    self.RevDataLoadPara_A0['LowLimit'] = self.RevData['CmdData'][self.LowerLimitIndexStart:self.LowerLimitIndexEnd]
                    self.RevDataLoadPara_A0['LowLimit_Decimal'] = self.RevData['CmdData'][self.LowerLimitDecimalIndexStart:self.LowerLimitDecimalIndexEnd]
                    self.RevDataLoadPara_A0['UpperLimit'] = self.RevData['CmdData'][self.UpperLimitIndexStart:self.UpperLimitIndexEnd]
                    self.RevDataLoadPara_A0['UpperLimit_Decimal'] = self.RevData['CmdData'][self.UpperLimitDecimalIndexStart:self.UpperLimitDecimalIndexEnd]
                    self.RevDataLoadPara_A0['Unit'] = self.RevData['CmdData'][self.UnitIndexStart:self.UnitIndexEnd]
                    self.RevDataLoadPara_A0['DAP'] = self.RevData['CmdData'][self.DAPIndexStart:self.DAPIndexEnd]
                    self.RevDataLoadPara_A0['P-L'] = self.RevData['CmdData'][self.PLIndexStart:self.PLIndexEnd]
                    self.RevDataLoadPara_A0['P-L_Decimal'] = self.RevData['CmdData'][self.PLDecimalIndexStart:self.PLDecimalIndexEnd]
                    self.RevDataLoadPara_A0['P-H'] = self.RevData['CmdData'][self.PHIndexStart:self.PHIndexEnd]
                    self.RevDataLoadPara_A0['P-H_Decimal'] = self.RevData['CmdData'][self.PHDecimalIndexStart:self.PHDecimalIndexEnd]
                    self.RevDataLoadPara_A0['Func1'] = self.RevData['CmdData'][self.Func1IndexStart:self.Func1IndexEnd]
                    self.RevDataLoadPara_A0['AL1'] = self.RevData['CmdData'][self.AL1IndexStart:self.AL1IndexEnd]
                    self.RevDataLoadPara_A0['AL1_Decimal'] = self.RevData['CmdData'][self.AL1DecimalIndexStart:self.AL1DecimalIndexEnd]
                    self.RevDataLoadPara_A0['AH1'] = self.RevData['CmdData'][self.AH1IndexStart:self.AH1IndexEnd]
                    self.RevDataLoadPara_A0['AH1_Decimal'] = self.RevData['CmdData'][self.AH1DecimalIndexStart:self.AH1DecimalIndexEnd]
                    self.RevDataLoadPara_A0['DL1'] = self.RevData['CmdData'][self.DL1IndexStart:self.DL1IndexEnd]
                    self.RevDataLoadPara_A0['Func2'] = self.RevData['CmdData'][self.Func2IndexStart:self.Func2IndexEnd]
                    self.RevDataLoadPara_A0['AL2'] = self.RevData['CmdData'][self.AL2IndexStart:self.AL2IndexEnd]
                    self.RevDataLoadPara_A0['AL2_Decimal'] = self.RevData['CmdData'][self.AL2DecimalIndexStart:self.AL2DecimalIndexEnd]
                    self.RevDataLoadPara_A0['AH2'] = self.RevData['CmdData'][self.AH2IndexStart:self.AH2IndexEnd]
                    self.RevDataLoadPara_A0['AH2_Decimal'] = self.RevData['CmdData'][self.AH2DecimalIndexStart:self.AH2DecimalIndexEnd]
                    self.RevDataLoadPara_A0['DL2'] = self.RevData['CmdData'][self.DL2IndexStart:self.DL2IndexEnd]

                    self.cmdHandler()
        except:
            pass
            # QMessageBox.critical(self, "错误", "串口接收数据错误！")

    def cmdHandler(self):
        # Load system data from MCU
        if self.RevData['CmdHeader'] == b'a0':
            # lower limit
            lowerLimit = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['LowLimit'])[::-1])
            lowerLimitDecimal = self.RevDataLoadPara_A0['LowLimit_Decimal']
            if lowerLimitDecimal == b'00':
                self.tableWidget.item(MainUI.LowLimitPos, MainUI.ParamColNum).setText(format(float(int(lowerLimit, 16)) / pow(10, 0), '.0f'))
            elif lowerLimitDecimal == b'01':
                self.tableWidget.item(MainUI.LowLimitPos, MainUI.ParamColNum).setText(format(float(int(lowerLimit, 16)) / pow(10, 1), '.1f'))
            elif lowerLimitDecimal == b'02':
                self.tableWidget.item(MainUI.LowLimitPos, MainUI.ParamColNum).setText(format(float(int(lowerLimit, 16)) / pow(10, 2), '.2f'))
            elif lowerLimitDecimal == b'03':
                self.tableWidget.item(MainUI.LowLimitPos, MainUI.ParamColNum).setText(format(float(int(lowerLimit, 16)) / pow(10, 3), '.3f'))

            # upper limit
            upperLimit = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['UpperLimit'])[::-1])
            upperLimitDecimal = self.RevDataLoadPara_A0['UpperLimit_Decimal']
            if upperLimitDecimal == b'00':
                self.tableWidget.item(MainUI.UpperLimitPos, MainUI.ParamColNum).setText(format(float(int(upperLimit, 16)) / pow(10, 0), '.0f'))
            elif upperLimitDecimal == b'01':
                self.tableWidget.item(MainUI.UpperLimitPos, MainUI.ParamColNum).setText(format(float(int(upperLimit, 16)) / pow(10, 1), '.1f'))
            elif upperLimitDecimal == b'02':
                self.tableWidget.item(MainUI.UpperLimitPos, MainUI.ParamColNum).setText(format(float(int(upperLimit, 16)) / pow(10, 2), '.2f'))
            elif upperLimitDecimal == b'03':
                self.tableWidget.item(MainUI.UpperLimitPos, MainUI.ParamColNum).setText(format(float(int(upperLimit, 16)) / pow(10, 3), '.3f'))

            # unit
            # b'00':PSI, b'01':BAR
            unit = self.RevDataLoadPara_A0['Unit']
            if unit == b'01':
                self.cbox_Unit.setCurrentText('Bar')
            elif unit == b'00':
                self.cbox_Unit.setCurrentText('Psi')
            else:
                self.pte_InfoOutput.insertPlainText("加载单位(Unit)错误!" + '\n')

            # DAP
            dap = self.RevDataLoadPara_A0['DAP']
            self.tableWidget.item(MainUI.DAPPos, MainUI.ParamColNum).setText(str(int(dap, 16)))

            # P-L
            PLVal = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['P-L'])[::-1])
            PLDecimal = self.RevDataLoadPara_A0['P-L_Decimal']
            if PLDecimal == b'00':
                self.tableWidget.item(MainUI.PLPos, MainUI.ParamColNum).setText(format(float(int(PLVal, 16)) / pow(10, 0), '.0f'))
            elif PLDecimal == b'01':
                self.tableWidget.item(MainUI.PLPos, MainUI.ParamColNum).setText(format(float(int(PLVal, 16)) / pow(10, 1), '.1f'))
            elif PLDecimal == b'02':
                self.tableWidget.item(MainUI.PLPos, MainUI.ParamColNum).setText(format(float(int(PLVal, 16)) / pow(10, 2), '.2f'))
            elif PLDecimal == b'03':
                self.tableWidget.item(MainUI.PLPos, MainUI.ParamColNum).setText(format(float(int(PLVal, 16)) / pow(10, 3), '.3f'))

            # P-H
            PHVal = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['P-H'])[::-1])
            PHDecimal = self.RevDataLoadPara_A0['P-H_Decimal']
            if PHDecimal == b'00':
                self.tableWidget.item(MainUI.PHPos, MainUI.ParamColNum).setText(format(float(int(PHVal, 16)) / pow(10, 0), '.0f'))
            elif PHDecimal == b'01':
                self.tableWidget.item(MainUI.PHPos, MainUI.ParamColNum).setText(format(float(int(PHVal, 16)) / pow(10, 1), '.1f'))
            elif PHDecimal == b'02':
                self.tableWidget.item(MainUI.PHPos, MainUI.ParamColNum).setText(format(float(int(PHVal, 16)) / pow(10, 2), '.2f'))
            elif PHDecimal == b'03':
                self.tableWidget.item(MainUI.PHPos, MainUI.ParamColNum).setText(format(float(int(PHVal, 16)) / pow(10, 3), '.3f'))

            # Func1
            Func1Val = self.RevDataLoadPara_A0['Func1']
            if Func1Val == b'00':
                self.cbox_Func1.setCurrentText('LO')
            elif Func1Val == b'01':
                self.cbox_Func1.setCurrentText('HI')
            elif Func1Val == b'02':
                self.cbox_Func1.setCurrentText('WIN1')
            elif Func1Val == b'03':
                self.cbox_Func1.setCurrentText('WIN2')
            else:
                self.pte_InfoOutput.insertPlainText("Func1Val: {}  ".format(Func1Val))
                self.pte_InfoOutput.insertPlainText("加载Func1错误!" + '\n')

            # AL1
            AL1Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['AL1'])[::-1])
            AL1Decimal = self.RevDataLoadPara_A0['AL1_Decimal']
            if AL1Decimal == b'00':
                self.tableWidget.item(MainUI.AL1Pos, MainUI.ParamColNum).setText(format(float(int(AL1Val, 16)) / pow(10, 0), '.0f'))
            elif AL1Decimal == b'01':
                self.tableWidget.item(MainUI.AL1Pos, MainUI.ParamColNum).setText(format(float(int(AL1Val, 16)) / pow(10, 1), '.1f'))
            elif AL1Decimal == b'02':
                self.tableWidget.item(MainUI.AL1Pos, MainUI.ParamColNum).setText(format(float(int(AL1Val, 16)) / pow(10, 2), '.2f'))
            elif AL1Decimal == b'03':
                self.tableWidget.item(MainUI.AL1Pos, MainUI.ParamColNum).setText(format(float(int(AL1Val, 16)) / pow(10, 3), '.3f'))

            # AH1
            AH1Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['AH1'])[::-1])
            AH1Decimal = self.RevDataLoadPara_A0['AH1_Decimal']
            if AH1Decimal == b'00':
                self.tableWidget.item(MainUI.AH1Pos, MainUI.ParamColNum).setText(format(float(int(AH1Val, 16)) / pow(10, 0), '.0f'))
            elif AH1Decimal == b'01':
                self.tableWidget.item(MainUI.AH1Pos, MainUI.ParamColNum).setText(format(float(int(AH1Val, 16)) / pow(10, 1), '.1f'))
            elif AH1Decimal == b'02':
                self.tableWidget.item(MainUI.AH1Pos, MainUI.ParamColNum).setText(format(float(int(AH1Val, 16)) / pow(10, 2), '.2f'))
            elif AH1Decimal == b'03':
                self.tableWidget.item(MainUI.AH1Pos, MainUI.ParamColNum).setText(format(float(int(AH1Val, 16)) / pow(10, 3), '.3f'))

            # DL1
            DL1Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['DL1'])[::-1])
            self.tableWidget.item(MainUI.DL1Pos, MainUI.ParamColNum).setText(format(float(int(DL1Val, 16)) / pow(10, 0), '.0f'))

            # Func2
            Func2Val = self.RevDataLoadPara_A0['Func2']
            if Func2Val == b'00':
                self.cbox_Func2.setCurrentText('LO')
            elif Func2Val == b'01':
                self.cbox_Func2.setCurrentText('HI')
            elif Func2Val == b'02':
                self.cbox_Func2.setCurrentText('WIN1')
            elif Func2Val == b'03':
                self.cbox_Func2.setCurrentText('WIN2')
            else:
                self.pte_InfoOutput.insertPlainText("Func2Val: {}  ".format(Func2Val))
                self.pte_InfoOutput.insertPlainText("加载Func2错误!" + '\n')

            # AL2
            AL2Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['AL2'])[::-1])
            AL2Decimal = self.RevDataLoadPara_A0['AL2_Decimal']
            if AL2Decimal == b'00':
                self.tableWidget.item(MainUI.AL2Pos, MainUI.ParamColNum).setText(format(float(int(AL2Val, 16)) / pow(10, 0), '.0f'))
            elif AL2Decimal == b'01':
                self.tableWidget.item(MainUI.AL2Pos, MainUI.ParamColNum).setText(format(float(int(AL2Val, 16)) / pow(10, 1), '.1f'))
            elif AL2Decimal == b'02':
                self.tableWidget.item(MainUI.AL2Pos, MainUI.ParamColNum).setText(format(float(int(AL2Val, 16)) / pow(10, 2), '.2f'))
            elif AL2Decimal == b'03':
                self.tableWidget.item(MainUI.AL2Pos, MainUI.ParamColNum).setText(format(float(int(AL2Val, 16)) / pow(10, 3), '.3f'))

            # AH2
            AH2Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['AH2'])[::-1])
            AH2Decimal = self.RevDataLoadPara_A0['AH2_Decimal']
            if AH2Decimal == b'00':
                self.tableWidget.item(MainUI.AH2Pos, MainUI.ParamColNum).setText(format(float(int(AH2Val, 16)) / pow(10, 0), '.0f'))
            elif AH2Decimal == b'01':
                self.tableWidget.item(MainUI.AH2Pos, MainUI.ParamColNum).setText(format(float(int(AH2Val, 16)) / pow(10, 1), '.1f'))
            elif AH2Decimal == b'02':
                self.tableWidget.item(MainUI.AH2Pos, MainUI.ParamColNum).setText(format(float(int(AH2Val, 16)) / pow(10, 2), '.2f'))
            elif AH2Decimal == b'03':
                self.tableWidget.item(MainUI.AH2Pos, MainUI.ParamColNum).setText(format(float(int(AH2Val, 16)) / pow(10, 3), '.3f'))

            # DL1
            DL2Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['DL2'])[::-1])
            self.tableWidget.item(MainUI.DL2Pos, MainUI.ParamColNum).setText(format(float(int(DL2Val, 16)) / pow(10, 0), '.0f'))

            # parameter description
            #self.tableWidget.item(MainUI.LowLimitPos, MainUI.ParamDescColNum).setText("1200 或 12.00")
            #self.tableWidget.item(MainUI.UpperLimitPos, MainUI.ParamDescColNum).setText("xxxx 或 xx.xx")

    def btnRestoreFactoryClicked(self):
        if self.port.isOpen():
            self.port.write(b'\xA7')

    def btnQueryParametersClicked(self):
        self.port.write(binascii.a2b_hex(self.CmdId['GetParam']))

    def getSettingValue(self, strVal, row):
        pointPos = strVal.find('.')

        if pointPos == -1: # integer
            val = int(strVal)
            if val == 0:
                return [0, 3]
            elif val >= 1 and val <= 9:
                return [val * pow(10, 3), 3] # for example: strVal='3' -> 3000(3.000, decimal point pos: 3)
            elif val >= 10 and val <= 99:
                return [val * pow(10, 2), 2] # for example: strVal='12' -> 1200(12.00, decimal point pos: 2)
            elif val >= 100 and val <= 999:
                return [val * pow(10, 1), 1] # for example: strVal='120' -> 1200(120.0, decimal point pos: 1)
            elif val >= 1000 and val <= 9999:
                return [val, 0] # for example: strVal='1200' -> 1200(1200, decimal point pos: 0)
            else:
                self.tableWidget.item(row, MainUI.ParamColNum).setText('#Invalid')


    def btnSetParametersClicked(self):
        bitMapLow = 0b0
        bitMapHigh = 0b0
        paramList = []

        # bit0, lower limit
        if self.chkBox_lowerlimit.isChecked():
            bitMapLow = bitMapLow | (1 << 0)
            self.lowLimitData = self.tableWidget.item(0, 2).text()
            paramList.append(self.lowLimitData)
            print('lower limit: ', self.lowLimitData)

        # bit1, upper limit
        if self.chkBox_upperlimit.isChecked():
            bitMapLow = bitMapLow | (1 << 1)
            self.upperLimitData = self.tableWidget.item(1, 2).text()
            paramList.append(self.upperLimitData)
            print('upper limit: ', self.upperLimitData)

        # bit2, unit
        if self.chkBox_Unit.isChecked():
            bitMapLow = bitMapLow | (1 << 2)
            self.unitData = self.cbox_Unit.currentText()
            paramList.append(self.unitData)
            print('unit: ', self.unitData)

        # bit3, DAP
        if self.chkBox_DAP.isChecked():
            bitMapLow = bitMapLow | (1 << 3)
            self.dapData = self.tableWidget.item(3, 2).text()
            paramList.append(self.dapData)
            print('dap: ', self.dapData)

        # bit4, P-L
        if self.chkBox_PL.isChecked():
            bitMapLow = bitMapLow | (1 << 4)
            self.PLData = self.tableWidget.item(4, 2).text()
            paramList.append(self.PLData)
            print('P-L: ', self.PLData)

        # bit5, P-H
        if self.chkBox_PH.isChecked():
            bitMapLow = bitMapLow | (1 << 5)
            self.PHData = self.tableWidget.item(5, 2).text()
            paramList.append(self.PHData)
            print('P-H: ', self.PHData)

        # bit6, Func1
        if self.chkBox_Func1.isChecked():
            bitMapLow = bitMapLow | (1 << 6)
            self.Func1Data = self.cbox_Func1.currentText()
            paramList.append(self.Func1Data)
            print('func1: ', self.Func1Data)

        # bit7, AL1
        if self.chkBox_AL1.isChecked():
            bitMapLow = bitMapLow | (1 << 7)
            self.AL1Data = self.tableWidget.item(7, 2).text()
            paramList.append(self.AL1Data)
            print('AL1: ', self.AL1Data)

        # bit8, AH1
        if self.chkBox_AH1.isChecked():
            bitMapHigh = bitMapHigh | (1 << 0)
            self.AH1Data = self.tableWidget.item(8, 2).text()
            paramList.append(self.AH1Data)
            print('AH1: ', self.AH1Data)

        # bit9, DL1
        if self.chkBox_DL1.isChecked():
            bitMapHigh = bitMapHigh | (1 << 1)
            self.DL1Data = self.tableWidget.item(9, 2).text()
            paramList.append(self.DL1Data)
            print('DL1: ', self.DL1Data)

        # bit10, Func2
        if self.chkBox_Func2.isChecked():
            bitMapHigh = bitMapHigh | (1 << 2)
            self.Func2Data = self.cbox_Func2.currentText()
            paramList.append(self.Func2Data)
            print('func2: ', self.Func2Data)

        # bit11, AL2
        if self.chkBox_AL2.isChecked():
            bitMapHigh = bitMapHigh | (1 << 3)
            self.AL2Data = self.tableWidget.item(11, 2).text()
            paramList.append(self.AL2Data)
            print('AL2: ', self.AL2Data)

        # bit12, AH2
        if self.chkBox_AH2.isChecked():
            bitMapHigh = bitMapHigh | (1 << 4)
            self.AH2Data = self.tableWidget.item(12, 2).text()
            paramList.append(self.AH2Data)
            print('AH2: ', self.AH2Data)

        # bit13, DL2
        if self.chkBox_DL2.isChecked():
            bitMapHigh = bitMapHigh | (1 << 5)
            self.DL2Data = self.tableWidget.item(13, 2).text()
            paramList.append(self.DL2Data)
            print('DL2: ', self.DL2Data)

        print([bitMapLow, bitMapHigh] + paramList)
        #self.port.write(bytes([bitMapLow, bitMapHigh]))

    def widgetStatusRefresh(self):
        if self.port.isOpen():
            self.btn_portConfig.setDisabled()
        else:
            self.btn_portConfig.setEnabled()

    def btnKeyClicked(self):
        if self.port.isOpen():
            currentKey = self.sender()

            if currentKey == self.btn_keyUp:
                self.port.write(b'\xA6\xB0')
            elif currentKey == self.btn_keyDown:
                self.port.write(b'\xA6\xB1')
            elif currentKey == self.btn_keyM:
                self.port.write(b'\xA6\xB2')
            elif currentKey == self.btn_keyS:
                self.port.write(b'\xA6\xB3')
        else:
            self.pte_InfoOutput.insertPlainText("请打开串口！" + '\n')

    def allSelectedClicked(self, col):
        print(col)
        if col == 0:
            item = self.tableWidget.horizontalHeaderItem(0)

            if self.allSelected == False:
                item.setText('反选')
                self.allSelected = True
                self.chkBox_upperlimit.setChecked(True)
                self.chkBox_lowerlimit.setChecked(True)
                self.chkBox_Unit.setChecked(True)
                self.chkBox_DAP.setChecked(True)
                self.chkBox_PL.setChecked(True)
                self.chkBox_PH.setChecked(True)
                self.chkBox_Func1.setChecked(True)
                self.chkBox_AL1.setChecked(True)
                self.chkBox_AH1.setChecked(True)
                self.chkBox_DL1.setChecked(True)
                self.chkBox_Func2.setChecked(True)
                self.chkBox_AL2.setChecked(True)
                self.chkBox_AH2.setChecked(True)
                self.chkBox_DL2.setChecked(True)
            else:
                item.setText('全选')
                self.allSelected = False
                self.chkBox_upperlimit.setChecked(False)
                self.chkBox_lowerlimit.setChecked(False)
                self.chkBox_Unit.setChecked(False)
                self.chkBox_DAP.setChecked(False)
                self.chkBox_PL.setChecked(False)
                self.chkBox_PH.setChecked(False)
                self.chkBox_Func1.setChecked(False)
                self.chkBox_AL1.setChecked(False)
                self.chkBox_AH1.setChecked(False)
                self.chkBox_DL1.setChecked(False)
                self.chkBox_Func2.setChecked(False)
                self.chkBox_AL2.setChecked(False)
                self.chkBox_AH2.setChecked(False)
                self.chkBox_DL2.setChecked(False)

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
        self.cbox_Unit.addItems(['Bar', 'Psi', 'Mpa'])
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
        # Func1
        self.chkBox_Func1 = QCheckBox()
        hLayout6 = QHBoxLayout()
        hLayout6.addWidget(self.chkBox_Func1)
        hLayout6.setAlignment(self.chkBox_Func1, Qt.AlignCenter)
        widget6 = QWidget()
        widget6.setLayout(hLayout6)
        self.tableWidget.setCellWidget(6, 0, widget6)
        self.cbox_Func1 = QComboBox()
        self.tableWidget.setCellWidget(6, 2, self.cbox_Func1)
        self.cbox_Func1.addItems(['LO', 'HI', 'WIN1', 'WIN2'])
        self.cbox_Func1.setCurrentIndex(-1)
        # AL1
        self.chkBox_AL1 = QCheckBox()
        hLayout7 = QHBoxLayout()
        hLayout7.addWidget(self.chkBox_AL1)
        hLayout7.setAlignment(self.chkBox_AL1, Qt.AlignCenter)
        widget7 = QWidget()
        widget7.setLayout(hLayout7)
        self.tableWidget.setCellWidget(7, 0, widget7)
        # AH1
        self.chkBox_AH1 = QCheckBox()
        hLayout8 = QHBoxLayout()
        hLayout8.addWidget(self.chkBox_AH1)
        hLayout8.setAlignment(self.chkBox_AH1, Qt.AlignCenter)
        widget8 = QWidget()
        widget8.setLayout(hLayout8)
        self.tableWidget.setCellWidget(8, 0, widget8)
        # DL1
        self.chkBox_DL1 = QCheckBox()
        hLayout9 = QHBoxLayout()
        hLayout9.addWidget(self.chkBox_DL1)
        hLayout9.setAlignment(self.chkBox_DL1, Qt.AlignCenter)
        widget9 = QWidget()
        widget9.setLayout(hLayout9)
        self.tableWidget.setCellWidget(9, 0, widget9)
        # Func2
        self.chkBox_Func2 = QCheckBox()
        hLayout10 = QHBoxLayout()
        hLayout10.addWidget(self.chkBox_Func2)
        hLayout10.setAlignment(self.chkBox_Func2, Qt.AlignCenter)
        widget10 = QWidget()
        widget10.setLayout(hLayout10)
        self.tableWidget.setCellWidget(10, 0, widget10)
        self.cbox_Func2 = QComboBox()
        self.tableWidget.setCellWidget(10, 2, self.cbox_Func2)
        self.cbox_Func2.addItems(['LO', 'HI', 'WIN1', 'WIN2'])
        self.cbox_Func2.setCurrentIndex(-1)
        # AL2
        self.chkBox_AL2 = QCheckBox()
        hLayout11 = QHBoxLayout()
        hLayout11.addWidget(self.chkBox_AL2)
        hLayout11.setAlignment(self.chkBox_AL2, Qt.AlignCenter)
        widget11 = QWidget()
        widget11.setLayout(hLayout11)
        self.tableWidget.setCellWidget(11, 0, widget11)
        # AH2
        self.chkBox_AH2 = QCheckBox()
        hLayout12 = QHBoxLayout()
        hLayout12.addWidget(self.chkBox_AH2)
        hLayout12.setAlignment(self.chkBox_AH2, Qt.AlignCenter)
        widget12 = QWidget()
        widget12.setLayout(hLayout12)
        self.tableWidget.setCellWidget(12, 0, widget12)
        # DL2
        self.chkBox_DL2 = QCheckBox()
        hLayout13 = QHBoxLayout()
        hLayout13.addWidget(self.chkBox_DL2)
        hLayout13.setAlignment(self.chkBox_DL2, Qt.AlignCenter)
        widget13 = QWidget()
        widget13.setLayout(hLayout13)
        self.tableWidget.setCellWidget(13, 0, widget13)

    '''size (bytes)'''
    UpperLimitSize = 2
    UpperLimitDecimalSize = 1
    LowerLimitSize = 2
    LowerLimitDecimalSize = 1
    UnitSize = 1
    DAPSize = 1
    PLSize = 2
    PLDecimalSize = 1
    PHSize = 2
    PHDecimalSize = 1
    Func1Size = 1
    AL1Size = 2
    AL1DecimalSize = 1
    AH1Size = 2
    AH1DecimalSize = 1
    DL1Size = 2
    Func2Size = 1
    AL2Size = 2
    AL2DecimalSize = 1
    AH2Size = 2
    AH2DecimalSize = 1
    DL2Size = 2

    '''parameters position'''
    ParamColNum = 2
    ParamDescColNum = 3
    LowLimitPos = 0
    UpperLimitPos = 1
    UnitPos = 2
    DAPPos = 3
    PLPos = 4
    PHPos = 5
    Func1Pos = 6
    AL1Pos = 7
    AH1Pos = 8
    DL1Pos = 9
    Func2Pos = 10
    AL2Pos = 11
    AH2Pos = 12
    DL2Pos = 13

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainUI()
    win.show()
    sys.exit(app.exec_())
