#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import freeze_support
import sys
import os
import sip
import time
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import uic
from PyQt4.Qt import *
import pywinusb.hid as hid
from multiprocessing import Pipe
import threading
from win32api import GetLastError
from GlobalModule import *
from USBHID_Process import USBHID_Process


Ui_MainWindow, QtBaseClass = uic.loadUiType("mainwnd.ui")
class USBHidTestTool(QtGui.QMainWindow, Ui_MainWindow):
    gui_signal = QtCore.pyqtSignal(object)
    def __init__(self):
        global g_thistool_version
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle('Bes USB Tester' + g_thistool_version)
        self.setWindowIcon(QIcon('images\\usb.png'))
        self.pipe_handle = {'gui_usbhid_pipe':-1, 'usbhid_gui_pipe':-1}
        self.notify_handle = {'main_sub_pipe': -1, 'sub_main_pipe':-1}
        self.key_detect_gui_init()
        self.pipe_handle['gui_usbhid_pipe'], self.pipe_handle['usbhid_gui_pipe'] = Pipe()
        self.notify_handle['main_sub_pipe'], self.notify_handle['sub_main_pipe'] = Pipe()
        self.gui_signal.connect(self.slot_gui_update)
        vendor_id, product_id = GlobalModule.get_config_vendor_product_id()
        self.monitor_thread = ProgressMonitor(self.pipe_handle, self.gui_signal)
        self.monitor_thread.start()        
        self.subproc = USBHID_Process(vendor_id, product_id, self.pipe_handle, self.notify_handle)
        self.subproc.start()

    def display_dev_connect_status(self, str_status):
        '''display dev connecting...'''
        if str_status == 'connecting' or str_status == 'disconnected':
            self.label_connect_status.setPixmap(QtGui.QPixmap('images\\disconnected.png'))
        elif str_status == 'connected':
            self.label_connect_status.setPixmap(QtGui.QPixmap('images\\connected.png'))
        else:
            pass

    def slot_gui_update(self, param):
        ''' gui update func'''
        msg = param[0]
        if msg == 'increase_down':
            self.label_volume_add.setPixmap(QtGui.QPixmap('images\\add_down.png'))
        elif msg == 'decrease_down':
            self.label_volume_sub.setPixmap(QtGui.QPixmap('images\\sub_down.png'))
        elif msg == 'play_pause_down':
            self.label_pause_play.setPixmap(QtGui.QPixmap('images\\play_down.png'))
        elif msg == 'key_up':
            self.key_detect_gui_init()
        elif msg == DEVICE_CONNECTING:
            self.display_dev_connect_status('connecting...')
        elif msg == DEVICE_CONNECTED:
            self.display_dev_connect_status('connected')
        elif msg == DEVICE_DISCONNECTED:
            self.display_dev_connect_status('disconnected')
            self.text_ProductName.setText('')
            self.text_VendorId.setText('')
            self.text_ProductID.setText('')
            self.text_SwVer.setText('')
            self.text_SN.setText('')
            self.key_add_vol.setText('')
            self.key_pause_play_vol.setText('')
            self.key_sub_vol.setText('')
        elif msg == STR_UPDATE_KEY_VOLT:
            key_value = param[1]
            str_voltage = str(param[2])
            if key_value == 0:
                self.key_add_vol.setText(str_voltage)
            elif key_value == 1:
                self.key_pause_play_vol.setText(str_voltage)
            elif key_value == 2:
                self.key_sub_vol.setText(str_voltage)
        elif msg == DEVICE_INFO:
            # self.label_connect_status.setText('connected')
            self.text_ProductName.setText(param[1])
            self.text_VendorId.setText(param[2])
            self.text_ProductID.setText(param[3])
        elif msg == DEVICE_SWVER_SN:
            self.text_SwVer.setText(param[1])
            self.text_SN.setText(param[2])

    def key_detect_gui_init(self):
        '''key detect gui init'''
        self.label_volume_add.setPixmap(QtGui.QPixmap('images\\add_up.png'))
        self.label_pause_play.setPixmap(QtGui.QPixmap('images\\play_up.png'))
        self.label_volume_sub.setPixmap(QtGui.QPixmap('images\\sub_up.png'))

    def closeEvent(self, event):
        '''closeEvent'''
        self.notify_handle['main_sub_pipe'].send(['app_exit'])
        event.accept()

class bestesttool_app_instance(object):
    def __init__(self):
        global G_APP_NAME
        from win32event import CreateMutex
        self.mutexName = '%s.%s' % ('Bestechnic', G_APP_NAME)
        self.myMutex = CreateMutex(None, False, self.mutexName)
        self.lastErr = GetLastError()

    def app_is_alive(self):
        if self.lastErr == ERROR_ALREADY_EXISTS:
            return True
        else:
            return False


class ProgressMonitor(threading.Thread):
    def __init__(self, pipe_handle, gui_signal):
        threading.Thread.__init__(self)
        self.pipe_handle = pipe_handle
        self.gui_signal = gui_signal

    def run(self):
        while True:
            rcv_msg = self.pipe_handle['gui_usbhid_pipe'].recv()
            if rcv_msg[0] == 'get_dev_hid_data':
                data = format(rcv_msg[1])
                # print "Raw data: {0}".format(rcv_msg[1])
                if data == '[1, 2, 0]':
                    self.gui_signal.emit(['decrease_down'])
                elif data == '[1, 1, 0]':
                    self.gui_signal.emit(['increase_down'])
                elif data == '[1, 4, 0]':
                    self.gui_signal.emit(['play_pause_down'])
                else:
                    self.gui_signal.emit(['key_up'])
            elif rcv_msg[0] == 'display_dev_info_req':
                msg_list = rcv_msg[1]
                if msg_list[0] == DEVICE_CONNECTING:
                    self.gui_signal.emit([DEVICE_CONNECTING])
                elif msg_list[0] == DEVICE_CONNECTED:
                    self.gui_signal.emit([DEVICE_CONNECTED])
                elif msg_list[0] == DEVICE_DISCONNECTED:
                    self.gui_signal.emit([DEVICE_DISCONNECTED])
                elif msg_list[0] == DEVICE_INFO:
                    self.gui_signal.emit([DEVICE_INFO, msg_list[1], msg_list[2], msg_list[3]])
                elif msg_list[0] == DEVICE_SWVER_SN:
                    self.gui_signal.emit([DEVICE_SWVER_SN, msg_list[1], msg_list[2]])
            elif rcv_msg[0] == STR_UPDATE_KEY_VOLT:
                key_vol_info = rcv_msg[1]
                volt_value = (key_vol_info[3] << 8) | (key_vol_info[2])
                print 'key %d, volt %d' % (key_vol_info[0], volt_value)
                self.gui_signal.emit([STR_UPDATE_KEY_VOLT, key_vol_info[0], volt_value])
            elif rcv_msg[0] == 'app_exit':
                break
        print 'mainproc ProgressMonitor run over...'



if __name__ == '__main__':
    # first be kind with local encodings
    import sys
    freeze_support()
    if sys.version_info >= (3,):
        # as is, don't handle unicodes
        unicode = str
        raw_input = input
    else:
        # allow to show encoded strings
        import codecs
        sys.stdout = codecs.getwriter('mbcs')(sys.stdout)
    app_instance = bestesttool_app_instance()
    bes_testtool_app = QApplication(sys.argv)
    bes_testtool_window = USBHidTestTool()
    bes_testtool_window.show()
    sys.exit(bes_testtool_app.exec_())


