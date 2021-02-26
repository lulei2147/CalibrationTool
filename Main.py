import sys
from PyQt5.Qt import *
from PyQt5 import QtCore
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from UI.MainUi import Ui_MainWindow
from UI.portConfig import Ui_Dialog
import binascii
import math
import re


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
        self.RevDataLoadPara_A0 = {'LowLimit': {'value': None, 'decimal': None},
                                   'UpperLimit': {'value': None, 'decimal': None},
                                   'Unit': {'value': None},
                                   'DAP': {'value': None},
                                   'P-L': {'value': None, 'decimal': None},
                                   'P-H': {'value': None, 'decimal': None},
                                   'Func1': {'value': None},
                                   'AL1': {'value': None, 'decimal': None},
                                   'AH1': {'value': None, 'decimal': None},
                                   'DL1': {'value': None, 'decimal': None},
                                   'Func2': {'value': None},
                                   'AL2': {'value': None, 'decimal': None},
                                   'AH2': {'value': None, 'decimal': None},
                                   'DL2': {'value': None, 'decimal': None}}
        self.SendDataSetPara_A1 = {'LowLimit': {'value': None, 'decimal': None},
                                   'UpperLimit': {'value': None, 'decimal': None},
                                   'Unit': {'value': None},
                                   'DAP': {'value': None},
                                   'P-L': {'value': None, 'decimal': None},
                                   'P-H': {'value': None, 'decimal': None},
                                   'Func1': {'value': None},
                                   'AL1': {'value': None, 'decimal': None},
                                   'AH1': {'value': None, 'decimal': None},
                                   'DL1': {'value': None, 'decimal': None},
                                   'Func2': {'value': None},
                                   'AL2': {'value': None, 'decimal': None},
                                   'AH2': {'value': None, 'decimal': None},
                                   'DL2': {'value': None, 'decimal': None}}
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
        self.DL1DecimalIndexStart = self.DL1IndexEnd
        self.DL1DecimalIndexEnd = self.DL1DecimalIndexStart + MainUI.DL1DecimalSize * 2
        # Func2
        self.Func2IndexStart = self.DL1DecimalIndexEnd
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
        self.DL2DecimalIndexStart = self.DL2IndexEnd
        self.DL2DecimalIndexEnd = self.DL2DecimalIndexStart + MainUI.DL2DecimalSize * 2

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

    def tabWidgetIParamItemChanged(self, item):
        #print(item.text(), item.row(), item.column())
        itemRow = item.row()
        text = item.text()
        if itemRow == MainUI.LowLimitPos:
            dicVal = self.updateAndDispValue(text, MainUI.LowLimitPos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['LowLimit']['value'] = dicVal['value']
            self.SendDataSetPara_A1['LowLimit']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.UpperLimitPos:
            dicVal = self.updateAndDispValue(text, MainUI.UpperLimitPos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['UpperLimit']['value'] = dicVal['value']
            self.SendDataSetPara_A1['UpperLimit']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.UnitPos:
            pass
        elif itemRow == MainUI.DAPPos:
            self.SendDataSetPara_A1['DAP']['value'] = self.updateAndDispValue(text, MainUI.DAPPos, MainUI.ParamColNum)
        elif itemRow == MainUI.PLPos:
            dicVal = self.updateAndDispValue(text, MainUI.PLPos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['P-L']['value'] = dicVal['value']
            self.SendDataSetPara_A1['P-L']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.PHPos:
            dicVal = self.updateAndDispValue(text, MainUI.PHPos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['P-H']['value'] = dicVal['value']
            self.SendDataSetPara_A1['P-H']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.AL1Pos:
            dicVal = self.updateAndDispValue(text, MainUI.AL1Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['AL1']['value'] = dicVal['value']
            self.SendDataSetPara_A1['AL1']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.AH1Pos:
            dicVal = self.updateAndDispValue(text, MainUI.AH1Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['AH1']['value'] = dicVal['value']
            self.SendDataSetPara_A1['AH1']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.DL1Pos:
            dicVal = self.updateAndDispValue(text, MainUI.DL1Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['DL1']['value'] = dicVal['value']
            self.SendDataSetPara_A1['DL1']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.AL2Pos:
            dicVal = self.updateAndDispValue(text, MainUI.AL2Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['AL2']['value'] = dicVal['value']
            self.SendDataSetPara_A1['AL2']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.AH2Pos:
            dicVal = self.updateAndDispValue(text, MainUI.AH2Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['AH2']['value'] = dicVal['value']
            self.SendDataSetPara_A1['AH2']['decimal'] = dicVal['decimal']
        elif itemRow == MainUI.DL2Pos:
            dicVal = self.updateAndDispValue(text, MainUI.DL2Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['DL2']['value'] = dicVal['value']
            self.SendDataSetPara_A1['DL2']['decimal'] = dicVal['decimal']
        print(self.SendDataSetPara_A1)

    def setTextToTabWidget(self, row, col, str):
        # Prevent triggering signals
        self.tableWidget.itemChanged.disconnect()
        self.tableWidget.item(row, col).setText(str)
        self.tableWidget.itemChanged.connect(self.tabWidgetIParamItemChanged)

    def updateAndDispValue(self, strVal, row, col):
        if col == MainUI.ParamColNum:
            if row == MainUI.LowLimitPos or row == MainUI.UpperLimitPos or row == MainUI.PLPos or row == MainUI.PHPos or \
                row == MainUI.AL1Pos or row == MainUI.AH1Pos or row == MainUI.AL2Pos or row == MainUI.AH2Pos or \
                row == MainUI.DL1Pos or row == MainUI.DL2Pos:
                # 1,2,3,4-digit integer, X, XX, XXX, XXXX
                if re.match(r'^[0-9]$', strVal) != None or re.match(r'^[0-9]{2}$', strVal) != None or \
                        re.match(r'^[0-9]{3}$', strVal) != None or re.match(r'^[0-9]{4}$', strVal) != None:
                    val = int(strVal)
                    self.setTextToTabWidget(row, col, str(val))

                    valLen = len(str(val))
                    if valLen == 1: # X
                        return {'value': int(val * 1000), 'decimal': 3}
                    elif valLen == 2: # XX
                        return {'value': int(val * 100), 'decimal': 2}
                    elif valLen == 3: # XXX
                        return {'value': int(val * 10), 'decimal': 1}
                    elif valLen == 4: # XXXX
                        return {'value': int(val), 'decimal': 0}
                    else:
                        pass
                # X.X, X.XX, X.XXX, 0.X, 0.XX, 0.XXX
                elif re.match(r'^\d\.[0-9]$', strVal) != None or re.match(r'^\d\.[0-9]{2}$', strVal) != None or re.match(r'^\d\.[0-9]{3}$', strVal) != None:
                    val = float(strVal)
                    self.setTextToTabWidget(row, col, str(val))
                    return {'value': int(val * 1000), 'decimal': 3}
                # XX.X, XX.XX
                elif re.match(r'^[1-9][0-9]\.[0-9]$', strVal) != None or re.match(r'^[1-9][0-9]\.[0-9]{2}$', strVal) != None:
                    val = float(strVal)
                    self.setTextToTabWidget(row, col, str(val))
                    return {'value': int(val * 100), 'decimal': 2}
                # XXX.X
                elif re.match(r'^[1-9][0-9]{2}\.[0-9]$', strVal) != None:
                    val = float(strVal)
                    self.setTextToTabWidget(row, col, str(val))
                    return {'value': int(val * 10), 'decimal': 1}
                # 00.X, 00.XX
                elif re.match(r'^0{2}\.[0-9]$', strVal) != None or re.match(r'^0{2}\.[0-9]{2}$', strVal) != None:
                    val = float(strVal)
                    self.setTextToTabWidget(row, col, str(val))
                    return {'value': int(val * 1000), 'decimal': 3}
                # 000.X
                elif re.match(r'^0{3}\.[0-9]$', strVal) != None:
                    val = float(strVal)
                    self.setTextToTabWidget(row, col, str(val))
                    return {'value': int(val * 1000), 'decimal': 3}
                # 0X.X, 0X.XX
                elif re.match(r'^0[1-9]\.[0-9]$', strVal) != None or re.match(r'^0[1-9]\.[0-9]{2}$', strVal) != None:
                    val = float(strVal)
                    self.setTextToTabWidget(row, col, str(val))
                    return {'value': int(val * 1000), 'decimal': 3}
                # 00X.X
                elif re.match(r'^0{2}[1-9]\.[0-9]$', strVal) != None:
                    val = float(strVal)
                    self.setTextToTabWidget(row, col, str(val))
                    return {'value': int(val * 1000), 'decimal': 3}
                # 0XX.X
                elif re.match(r'^0[1-9][0-9]\.[0-9]$', strVal) != None:
                    val = float(strVal)
                    self.setTextToTabWidget(row, col, str(val))
                    return {'value': int(val * 100), 'decimal': 2}
                else:
                    self.setTextToTabWidget(row, col, '#Invalid')
                    self.pte_InfoOutput.insertPlainText('无效参数！参数范围：[0,9999] 或者 [0.0,999.9]' + '\n')
                    return None
            elif row == MainUI.UnitPos:
                self.cbox_Unit.setCurrentText(strVal)
                if strVal == 'Bar':
                    return MainUI.UnitBar
                else:
                    return MainUI.UnitPsi
            elif row == MainUI.DAPPos:
                if re.match(r'^[0-9]$', strVal) != None or re.match(r'^10$', strVal) != None:
                    self.setTextToTabWidget(row, col, strVal)
                    return int(strVal)
                else:
                    self.setTextToTabWidget(row, col, '#Invalid')
                    self.pte_InfoOutput.insertPlainText('无效参数！参数范围：[0,10]' + '\n')
                    return None
            elif row == MainUI.Func1Pos or row == MainUI.Func2Pos:
                if row == MainUI.Func1Pos:
                    self.cbox_Func1.setCurrentText(strVal)
                else:
                    self.cbox_Func2.setCurrentText(strVal)

                if strVal == 'LO':
                    return MainUI.FuncLO
                elif strVal == 'HI':
                    return MainUI.FuncHi
                elif strVal == 'WIN1':
                    return MainUI.FuncWin1
                elif strVal == 'WIN2':
                    return MainUI.FuncWin2
            else:
                return None
        else:
            return None

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

                    self.RevDataLoadPara_A0['LowLimit']['value'] = self.RevData['CmdData'][self.LowerLimitIndexStart:self.LowerLimitIndexEnd]
                    self.RevDataLoadPara_A0['LowLimit'] ['decimal']= self.RevData['CmdData'][self.LowerLimitDecimalIndexStart:self.LowerLimitDecimalIndexEnd]
                    self.RevDataLoadPara_A0['UpperLimit']['value'] = self.RevData['CmdData'][self.UpperLimitIndexStart:self.UpperLimitIndexEnd]
                    self.RevDataLoadPara_A0['UpperLimit']['decimal'] = self.RevData['CmdData'][self.UpperLimitDecimalIndexStart:self.UpperLimitDecimalIndexEnd]
                    self.RevDataLoadPara_A0['Unit']['value'] = self.RevData['CmdData'][self.UnitIndexStart:self.UnitIndexEnd]
                    self.RevDataLoadPara_A0['DAP']['value'] = self.RevData['CmdData'][self.DAPIndexStart:self.DAPIndexEnd]
                    self.RevDataLoadPara_A0['P-L']['value'] = self.RevData['CmdData'][self.PLIndexStart:self.PLIndexEnd]
                    self.RevDataLoadPara_A0['P-L']['decimal'] = self.RevData['CmdData'][self.PLDecimalIndexStart:self.PLDecimalIndexEnd]
                    self.RevDataLoadPara_A0['P-H']['value'] = self.RevData['CmdData'][self.PHIndexStart:self.PHIndexEnd]
                    self.RevDataLoadPara_A0['P-H']['decimal'] = self.RevData['CmdData'][self.PHDecimalIndexStart:self.PHDecimalIndexEnd]
                    self.RevDataLoadPara_A0['Func1']['value'] = self.RevData['CmdData'][self.Func1IndexStart:self.Func1IndexEnd]
                    self.RevDataLoadPara_A0['AL1']['value'] = self.RevData['CmdData'][self.AL1IndexStart:self.AL1IndexEnd]
                    self.RevDataLoadPara_A0['AL1']['decimal'] = self.RevData['CmdData'][self.AL1DecimalIndexStart:self.AL1DecimalIndexEnd]
                    self.RevDataLoadPara_A0['AH1']['value'] = self.RevData['CmdData'][self.AH1IndexStart:self.AH1IndexEnd]
                    self.RevDataLoadPara_A0['AH1']['decimal'] = self.RevData['CmdData'][self.AH1DecimalIndexStart:self.AH1DecimalIndexEnd]
                    self.RevDataLoadPara_A0['DL1']['value'] = self.RevData['CmdData'][self.DL1IndexStart:self.DL1IndexEnd]
                    self.RevDataLoadPara_A0['DL1']['decimal'] = self.RevData['CmdData'][self.DL1DecimalIndexStart:self.DL1DecimalIndexEnd]
                    self.RevDataLoadPara_A0['Func2']['value'] = self.RevData['CmdData'][self.Func2IndexStart:self.Func2IndexEnd]
                    self.RevDataLoadPara_A0['AL2']['value'] = self.RevData['CmdData'][self.AL2IndexStart:self.AL2IndexEnd]
                    self.RevDataLoadPara_A0['AL2']['decimal'] = self.RevData['CmdData'][self.AL2DecimalIndexStart:self.AL2DecimalIndexEnd]
                    self.RevDataLoadPara_A0['AH2']['value'] = self.RevData['CmdData'][self.AH2IndexStart:self.AH2IndexEnd]
                    self.RevDataLoadPara_A0['AH2']['decimal'] = self.RevData['CmdData'][self.AH2DecimalIndexStart:self.AH2DecimalIndexEnd]
                    self.RevDataLoadPara_A0['DL2']['value'] = self.RevData['CmdData'][self.DL2IndexStart:self.DL2IndexEnd]
                    self.RevDataLoadPara_A0['DL2']['decimal'] = self.RevData['CmdData'][self.DL2DecimalIndexStart:self.DL2DecimalIndexEnd]

                    self.cmdHandler()
        except:
            pass
            # QMessageBox.critical(self, "错误", "串口接收数据错误！")

    def cmdHandler(self):
        # Load system data from MCU
        if self.RevData['CmdHeader'] == b'a0':
            text = ''

            # lower limit
            lowerLimit = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['LowLimit']['value'])[::-1])
            lowerLimitDecimal = self.RevDataLoadPara_A0['LowLimit']['decimal']
            if lowerLimitDecimal == b'00':
                text = format(int(lowerLimit, 16), '.0f')
            elif lowerLimitDecimal == b'01':
                text = format(float(int(lowerLimit, 16)) / pow(10, 1), '.1f')
            elif lowerLimitDecimal == b'02':
                text = format(float(int(lowerLimit, 16)) / pow(10, 2), '.2f')
            elif lowerLimitDecimal == b'03':
                text = format(float(int(lowerLimit, 16)) / pow(10, 3), '.3f')
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.LowLimitPos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['LowLimit']['value'] = dicVal['value']
            self.SendDataSetPara_A1['LowLimit']['decimal'] = dicVal['decimal']

            # upper limit
            upperLimit = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['UpperLimit']['value'])[::-1])
            upperLimitDecimal = self.RevDataLoadPara_A0['UpperLimit']['decimal']
            if upperLimitDecimal == b'00':
                text = format(int(upperLimit, 16), '.0f')
            elif upperLimitDecimal == b'01':
                text = format(float(int(upperLimit, 16)) / pow(10, 1), '.1f')
            elif upperLimitDecimal == b'02':
                text = format(float(int(upperLimit, 16)) / pow(10, 2), '.2f')
            elif upperLimitDecimal == b'03':
                text = format(float(int(upperLimit, 16)) / pow(10, 3), '.3f')
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.UpperLimitPos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['UpperLimit']['value'] = dicVal['value']
            self.SendDataSetPara_A1['UpperLimit']['decimal'] = dicVal['decimal']

            # unit
            # b'00':PSI, b'01':BAR
            unit = self.RevDataLoadPara_A0['Unit']['value']
            if unit == b'01':
                text = 'Bar'
            elif unit == b'00':
                text = 'Psi'
            else:
                self.SendDataSetPara_A1['Unit']['value'] = None
            # assign value to the buffer to be sent
            self.SendDataSetPara_A1['Unit']['value'] = self.updateAndDispValue(text, MainUI.UnitPos, MainUI.ParamColNum)

            # DAP
            dap = self.RevDataLoadPara_A0['DAP']['value']
            text = str(int(dap, 16))
            # assign value to the buffer to be sent
            self.SendDataSetPara_A1['DAP']['value'] = self.updateAndDispValue(text, MainUI.DAPPos, MainUI.ParamColNum)

            # P-L
            PLVal = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['P-L']['value'])[::-1])
            PLDecimal = self.RevDataLoadPara_A0['P-L']['decimal']
            if PLDecimal == b'00':
                text = format(int(PLVal, 16), '.0f')
            elif PLDecimal == b'01':
                text = format(float(int(PLVal, 16)) / pow(10, 1), '.1f')
            elif PLDecimal == b'02':
                text = format(float(int(PLVal, 16)) / pow(10, 2), '.2f')
            elif PLDecimal == b'03':
                text = format(float(int(PLVal, 16)) / pow(10, 3), '.3f')
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.PLPos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['P-L']['value'] = dicVal['value']
            self.SendDataSetPara_A1['P-L']['decimal'] = dicVal['decimal']

            # P-H
            PHVal = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['P-H']['value'])[::-1])
            PHDecimal = self.RevDataLoadPara_A0['P-H']['decimal']
            if PHDecimal == b'00':
                text = format(int(PHVal, 16), '.0f')
            elif PHDecimal == b'01':
                text = format(float(int(PHVal, 16)) / pow(10, 1), '.1f')
            elif PHDecimal == b'02':
                text = format(float(int(PHVal, 16)) / pow(10, 2), '.2f')
            elif PHDecimal == b'03':
                text = format(float(int(PHVal, 16)) / pow(10, 3), '.3f')
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.PHPos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['P-H']['value'] = dicVal['value']
            self.SendDataSetPara_A1['P-H']['decimal'] = dicVal['decimal']

            # Func1
            Func1Val = self.RevDataLoadPara_A0['Func1']['value']
            if Func1Val == b'00':
                text = 'LO'
            elif Func1Val == b'01':
                text = 'HI'
            elif Func1Val == b'02':
                text = 'WIN1'
            elif Func1Val == b'03':
                text = 'WIN2'
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            self.SendDataSetPara_A1['Func1']['value'] = self.updateAndDispValue(text, MainUI.Func1Pos, MainUI.ParamColNum)

            # AL1
            AL1Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['AL1']['value'])[::-1])
            AL1Decimal = self.RevDataLoadPara_A0['AL1']['decimal']
            if AL1Decimal == b'00':
                text = format(int(AL1Val, 16), '.0f')
            elif AL1Decimal == b'01':
                text = format(float(int(AL1Val, 16)) / pow(10, 1), '.1f')
            elif AL1Decimal == b'02':
                text = format(float(int(AL1Val, 16)) / pow(10, 2), '.2f')
            elif AL1Decimal == b'03':
                text = format(float(int(AL1Val, 16)) / pow(10, 3), '.3f')
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.AL1Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['AL1']['value'] = dicVal['value']
            self.SendDataSetPara_A1['AL1']['decimal'] = dicVal['decimal']

            # AH1
            AH1Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['AH1']['value'])[::-1])
            AH1Decimal = self.RevDataLoadPara_A0['AH1']['decimal']
            if AH1Decimal == b'00':
                text = format(int(AH1Val, 16), '.0f')
            elif AH1Decimal == b'01':
                text = format(float(int(AH1Val, 16)) / pow(10, 1), '.1f')
            elif AH1Decimal == b'02':
                text = format(float(int(AH1Val, 16)) / pow(10, 2), '.2f')
            elif AH1Decimal == b'03':
                text = format(float(int(AH1Val, 16)) / pow(10, 3), '.3f')
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.AH1Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['AH1']['value'] = dicVal['value']
            self.SendDataSetPara_A1['AH1']['decimal'] = dicVal['decimal']

            # DL1
            DL1Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['DL1']['value'])[::-1])
            DL1Decimal = self.RevDataLoadPara_A0['DL1']['decimal']
            if DL1Decimal == b'00':
                text = format(int(DL1Val, 16), '.0f')
            elif DL1Decimal == b'01':
                text = format(float(int(DL1Val, 16)) / pow(10, 1), '.1f')
            elif DL1Decimal == b'02':
                text = format(float(int(DL1Val, 16)) / pow(10, 2), '.2f')
            elif DL1Decimal == b'03':
                text = format(float(int(DL1Val, 16)) / pow(10, 3), '.3f')
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.DL1Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['DL1']['value'] = dicVal['value']
            self.SendDataSetPara_A1['DL1']['decimal'] = dicVal['decimal']

            # Func2
            Func2Val = self.RevDataLoadPara_A0['Func2']['value']
            if Func2Val == b'00':
                text = 'LO'
            elif Func2Val == b'01':
                text = 'HI'
            elif Func2Val == b'02':
                text = 'WIN1'
            elif Func2Val == b'03':
                text = 'WIN2'
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            self.SendDataSetPara_A1['Func2']['value'] = self.updateAndDispValue(text, MainUI.Func2Pos, MainUI.ParamColNum)

            # AL2
            AL2Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['AL2']['value'])[::-1])
            AL2Decimal = self.RevDataLoadPara_A0['AL2']['decimal']
            if AL2Decimal == b'00':
                text = format(int(AL2Val, 16), '.0f')
            elif AL2Decimal == b'01':
                text = format(float(int(AL2Val, 16)) / pow(10, 1), '.1f')
            elif AL2Decimal == b'02':
                text = format(float(int(AL2Val, 16)) / pow(10, 2), '.2f')
            elif AL2Decimal == b'03':
                text = format(float(int(AL2Val, 16)) / pow(10, 3), '.3f')
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.AL2Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['AL2']['value'] = dicVal['value']
            self.SendDataSetPara_A1['AL2']['decimal'] = dicVal['decimal']

            # AH2
            AH2Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['AH2']['value'])[::-1])
            AH2Decimal = self.RevDataLoadPara_A0['AH2']['decimal']
            if AH2Decimal == b'00':
                text = format(int(AL2Val, 16), '.0f')
            elif AH2Decimal == b'01':
                text = format(float(int(AH2Val, 16)) / pow(10, 1), '.1f')
            elif AH2Decimal == b'02':
                text = format(float(int(AH2Val, 16)) / pow(10, 2), '.2f')
            elif AH2Decimal == b'03':
                text = format(float(int(AH2Val, 16)) / pow(10, 3), '.3f')
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.AH2Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['AH2']['value'] = dicVal['value']
            self.SendDataSetPara_A1['AH2']['decimal'] = dicVal['decimal']

            # DL2
            DL2Val = binascii.hexlify(binascii.unhexlify(self.RevDataLoadPara_A0['DL2']['value'])[::-1])
            DL2Decimal = self.RevDataLoadPara_A0['DL2']['decimal']
            if DL2Decimal == b'00':
                text = format(int(DL2Val, 16), '.0f')
            elif DL2Decimal == b'01':
                text = format(float(int(DL2Val, 16)) / pow(10, 1), '.1f')
            elif DL2Decimal == b'02':
                text = format(float(int(DL2Val, 16)) / pow(10, 2), '.2f')
            elif DL2Decimal == b'03':
                text = format(float(int(DL2Val, 16)) / pow(10, 3), '.3f')
            else:
                text = '#Invalid'
            # assign value to the buffer to be sent
            dicVal = self.updateAndDispValue(text, MainUI.DL2Pos, MainUI.ParamColNum)
            self.SendDataSetPara_A1['DL2']['value'] = dicVal['value']
            self.SendDataSetPara_A1['DL2']['decimal'] = dicVal['decimal']

            # parameter description
            self.setTextToTabWidget(MainUI.LowLimitPos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.UpperLimitPos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.UnitPos, MainUI.ParamDescColNum, 'Psi:0, Bar:1')
            self.setTextToTabWidget(MainUI.DAPPos, MainUI.ParamDescColNum, 'int, [0-10]')
            self.setTextToTabWidget(MainUI.PLPos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.PHPos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.Func1Pos, MainUI.ParamDescColNum, 'LO:0,HI:1,WIN1:2,WIN2:3')
            self.setTextToTabWidget(MainUI.AL1Pos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.AH1Pos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.DL1Pos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.Func2Pos, MainUI.ParamDescColNum, 'LO:0,HI:1,WIN1:2,WIN2:3')
            self.setTextToTabWidget(MainUI.AL2Pos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.AH2Pos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')
            self.setTextToTabWidget(MainUI.DL2Pos, MainUI.ParamDescColNum, 'float,int, [0, 9999]')

    def btnRestoreFactoryClicked(self):
        if self.port.isOpen():
            self.port.write(b'\xA7')

    def btnQueryParametersClicked(self):
        self.port.write(binascii.a2b_hex(self.CmdId['GetParam']))

    def btnSetParametersClicked(self):
        bitMapLow = 0b0
        bitMapHigh = 0b0
        setVal = b''

        # bit0, lower limit
        if self.chkBox_lowerlimit.isChecked():
            bitMapLow = bitMapLow | (1 << 0)
            setVal = setVal + (self.SendDataSetPara_A1['LowLimit']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['LowLimit']['decimal']).to_bytes(1, byteorder='big')
        # bit1, upper limit
        if self.chkBox_upperlimit.isChecked():
            bitMapLow = bitMapLow | (1 << 1)
            setVal = setVal + (self.SendDataSetPara_A1['UpperLimit']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['UpperLimit']['decimal']).to_bytes(1, byteorder='big')
        # bit2, unit
        if self.chkBox_Unit.isChecked():
            bitMapLow = bitMapLow | (1 << 2)
            setVal = setVal + self.SendDataSetPara_A1['Unit']['value'].to_bytes(1, byteorder='big')
        # bit3, DAP
        if self.chkBox_DAP.isChecked():
            bitMapLow = bitMapLow | (1 << 3)
            setVal = setVal + self.SendDataSetPara_A1['DAP']['value'].to_bytes(1, byteorder='big')
        # bit4, P-L
        if self.chkBox_PL.isChecked():
            bitMapLow = bitMapLow | (1 << 4)
            setVal = setVal + (self.SendDataSetPara_A1['P-L']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['P-L']['decimal']).to_bytes(1, byteorder='big')
        # bit5, P-H
        if self.chkBox_PH.isChecked():
            bitMapLow = bitMapLow | (1 << 5)
            setVal = setVal + (self.SendDataSetPara_A1['P-H']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['P-H']['decimal']).to_bytes(1, byteorder='big')
        # bit6, Func1
        if self.chkBox_Func1.isChecked():
            bitMapLow = bitMapLow | (1 << 6)
            setVal = setVal + self.SendDataSetPara_A1['Func1']['value'].to_bytes(1, byteorder='big')
        # bit7, AL1
        if self.chkBox_AL1.isChecked():
            bitMapLow = bitMapLow | (1 << 7)
            setVal = setVal + (self.SendDataSetPara_A1['AL1']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['AL1']['decimal']).to_bytes(1, byteorder='big')
        # bit8, AH1
        if self.chkBox_AH1.isChecked():
            bitMapHigh = bitMapHigh | (1 << 0)
            setVal = setVal + (self.SendDataSetPara_A1['AH1']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['AH1']['decimal']).to_bytes(1, byteorder='big')
        # bit9, DL1
        if self.chkBox_DL1.isChecked():
            bitMapHigh = bitMapHigh | (1 << 1)
            setVal = setVal + (self.SendDataSetPara_A1['DL1']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['DL1']['decimal']).to_bytes(1, byteorder='big')
        # bit10, Func2
        if self.chkBox_Func2.isChecked():
            bitMapHigh = bitMapHigh | (1 << 2)
            setVal = setVal + self.SendDataSetPara_A1['Func2']['value'].to_bytes(1, byteorder='big')
        # bit11, AL2
        if self.chkBox_AL2.isChecked():
            bitMapHigh = bitMapHigh | (1 << 3)
            setVal = setVal + (self.SendDataSetPara_A1['AL2']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['AL2']['decimal']).to_bytes(1, byteorder='big')
        # bit12, AH2
        if self.chkBox_AH2.isChecked():
            bitMapHigh = bitMapHigh | (1 << 4)
            setVal = setVal + (self.SendDataSetPara_A1['AH2']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['AH2']['decimal']).to_bytes(1, byteorder='big')
        # bit13, DL2
        if self.chkBox_DL2.isChecked():
            bitMapHigh = bitMapHigh | (1 << 5)
            setVal = setVal + (self.SendDataSetPara_A1['DL2']['value']).to_bytes(2, byteorder='big') + \
                     (self.SendDataSetPara_A1['DL2']['decimal']).to_bytes(1, byteorder='big')

        setVal = bitMapLow.to_bytes(1, byteorder='big') + bitMapHigh.to_bytes(1, byteorder='big') + setVal

        print(self.SendDataSetPara_A1)
        print(setVal)
        print(''.join('%02X,' % b for b in setVal))

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
        #self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        self.cbox_Unit.addItems(['Bar', 'Psi'])
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
    DL1DecimalSize = 1
    Func2Size = 1
    AL2Size = 2
    AL2DecimalSize = 1
    AH2Size = 2
    AH2DecimalSize = 1
    DL2Size = 2
    DL2DecimalSize = 1

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

    # Unit
    UnitPsi = 0
    UnitBar = 1
    # Func1
    FuncLO = 0
    FuncHi = 1
    FuncWin1 = 2
    FuncWin2 = 3

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainUI()
    win.show()
    sys.exit(app.exec_())
