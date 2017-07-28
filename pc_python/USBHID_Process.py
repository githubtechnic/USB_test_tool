import os,sys
import time
import multiprocessing
import threading
import pywinusb.hid as hid
from time import sleep
import usb.core
import usb.util
from GlobalModule import *

class USBHID_Process(multiprocessing.Process):
    'sub process for USBHID.'
    dev_status = 'idle'
    w_devstatus_mutex = threading.Lock()
    def __init__(self, target_vendor_id, target_product_id, pipe_handle, notify_handle):
        self.hid_target = None
        self.vendor_id = target_vendor_id
        self.product_id = target_product_id
        self.pipe_handle = pipe_handle
        self.notify_handle = notify_handle
        self.pyusb_device = None
        self.bes_typec_dev = None
        self.courier_thread = None
        multiprocessing.Process.__init__(self)
        USBHID_Process.dev_status = 'ready'

    def run(self):
        USBHID_Process.dev_status = 'run'
        self.courier_thread = self.CourierMainProcCmd(self.notify_handle, self.pipe_handle)
        self.courier_thread.start()
        self.usb_tester_working()
        self.courier_thread.join()
        print 'subprocess run over...'

    def bes_hid_dev_raw_data_handler(self, data):
        '''notify gui process'''
        # print("Raw data: {0}".format(data))
        self.pipe_handle['usbhid_gui_pipe'].send(['get_dev_hid_data', data])
        which_key_down = format(data)
        if which_key_down == '[1, 1, 0]' or which_key_down == '[1, 2, 0]' or which_key_down == '[1, 4, 0]':#[205, 171][CD,AB]
            msg = STR_QUERY_VOLTAGE
            ret_len = self.pyusb_device.ctrl_transfer(0x40, 0x01, 0, 0, msg)
            assert ret_len == len(msg)
            ret_data = self.pyusb_device.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_IN, 0x20, 0, 0, 32)
            # print ret_data
            self.pipe_handle['usbhid_gui_pipe'].send([STR_UPDATE_KEY_VOLT, ret_data])
            # ret_data[0]

        # self.pipe_handle['usbhid_gui_pipe'].send(data)
        # print("Raw data: {0}".format(data))

    def  usb_device_info_notify(self, data_list):
        '''notify main process to display device info'''
        self.pipe_handle['usbhid_gui_pipe'].send(['display_dev_info_req', data_list])

    def pyusb_dut_data_query(self):
        '''query DUT about SN,sw version,voltage...'''
        while True:
            if USBHID_Process.dev_status != 'run':
                break
            self.pyusb_device = usb.core.find(idVendor = self.vendor_id, idProduct = self.product_id)
            if self.pyusb_device is None:
                self.usb_device_info_notify([DEVICE_NOT_FOUND])
                # print 'pyusb device not found!'
                time.sleep(0.5)
            else:
                try:
                    # dev.set_configuration()
                    dev_product = str(self.pyusb_device.product)
                    dev_idVendor = hex(self.pyusb_device.idVendor)
                    dev_idProduct = hex(self.pyusb_device.idProduct)
                    dev_info_list = [DEVICE_INFO, dev_product, dev_idVendor, dev_idProduct]
                    self.usb_device_info_notify(dev_info_list)
                    break
                except:
                    # print 'can not get device info from dev!'
                    time.sleep(0.5)
        try:
            msg = STR_QUERY_SW_VER
            ret_len = self.pyusb_device.ctrl_transfer(0x40, 0x01, 0, 0, msg)
            assert ret_len == len(msg)
            ret_data = self.pyusb_device.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_IN, 0x20, 0, 0, 64)
            str_sw_ver = ''.join([chr(x) for x in ret_data])
            # print str_sw_ver

            msg = STR_QUERY_SN
            ret_len = self.pyusb_device.ctrl_transfer(0x40, 0x01, 0, 0, msg)
            assert ret_len == len(msg)
            ret_data = self.pyusb_device.ctrl_transfer(usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_IN, 0x20, 0, 0, 32)
            str_sn = ''.join([chr(x) for x in ret_data])
            # print str_sn
            dut_data_list = [DEVICE_SWVER_SN, str_sw_ver, str_sn]
            self.usb_device_info_notify(dut_data_list)
        except:
            print 'ctrl transfer end...'

    def usb_tester_working(self):
        '''browse filter devices...'''
        while USBHID_Process.dev_status == 'run':
            # self.usb_device_info_notify([DEVICE_CONNECTING])
            self.pyusb_dut_data_query()
            self.hid_target = hid.HidDeviceFilter(vendor_id = self.vendor_id, product_id = self.product_id)
            all_items = self.hid_target.get_devices()
            len_items = len(all_items)
            if len_items == 1:
                self.bes_typec_dev = all_items[0]
                print "got Bes device: %s!" % repr(self.bes_typec_dev)
                try:
                    self.bes_typec_dev.open()
                    self.usb_device_info_notify([DEVICE_CONNECTED])
                    self.bes_typec_dev.set_raw_data_handler(self.bes_hid_dev_raw_data_handler)
                    while True:
                        if USBHID_Process.dev_status == 'run':
                            is_plugged = self.bes_typec_dev.is_plugged()
                            if is_plugged is False:
                                # USBHID_Process.w_devstatus_mutex.acquire()
                                # USBHID_Process.dev_status = 'idle'
                                # USBHID_Process.w_devstatus_mutex.release()
                                break
                        elif USBHID_Process.dev_status == 'idle':
                            # self.bes_typec_dev.close()
                            break
                        time.sleep(0.2)
                finally:
                    time.sleep(0.2)
                self.bes_typec_dev.close()
                self.usb_device_info_notify([DEVICE_DISCONNECTED])
            elif len_items == 0:
                print 'waiting for Bes device plug...'
                time.sleep(0.5)
            else:
                print 'keep ONE usb HID plugged!'
                time.sleep(1)



    class CourierMainProcCmd(threading.Thread):
        def __init__(self, notify_handle, pipe_handle):
            threading.Thread.__init__(self)
            self.notify_handle = notify_handle
            self.pipe_handle = pipe_handle

        def run(self):
            while USBHID_Process.dev_status == 'run':
                rcv_msg = self.notify_handle['sub_main_pipe'].recv()
                if rcv_msg[0] == 'app_exit':
                    # all_hids = hid.find_all_hid_devices()
                    # self.usbhid_dev = all_hids[0]
                    USBHID_Process.w_devstatus_mutex.acquire()
                    USBHID_Process.dev_status = 'idle'
                    USBHID_Process.w_devstatus_mutex.release()
                    self.pipe_handle['usbhid_gui_pipe'].send(['app_exit'])
                    print 'app exit...'
                    break
                else:
                    print rcv_msg
            print 'CourierMainProcCmd run over...'


    def back_up_func(self):
        # browse devices...
        all_hids = hid.find_all_hid_devices()
        if all_hids:
            while True:
                print "Choose a device to courier raw input reports:\n"
                print("0 => Exit")
                for index, device in enumerate(all_hids):
                    device_name = unicode("{0.vendor_name} {0.product_name}" \
                            "(vID=0x{1:04x}, pID=0x{2:04x})"\
                            "".format(device, device.vendor_id, device.product_id))
                    print("{0} => {1}".format(index+1, device_name))
                # print "\n\nDevice('0' to '%d', '0' to exit.) [press enter after number]:" % len(all_hids)
                print '\npress enter after number:'
                index_option = raw_input()
                if index_option.isdigit() and int(index_option) <= len(all_hids):
                    # invalid
                    break
            int_option = int(index_option)
            if int_option:
                self.usb_hid_device = all_hids[int_option-1]
                try:
                    self.usb_hid_device.open()
                    #set custom raw data handler
                    self.usb_hid_device.set_raw_data_handler(self.bes_hid_dev_raw_data_handler)
                    print("\nWaiting for data...\nPress any (system keyboard) key to stop...")
                    # while not kbhit() and self.usb_hid_device.is_plugged():
                    #     #just keep the self.usb_hid_device opened to receive events
                    #     sleep(0.5)
                    # return
                finally:
                    self.usb_hid_device.close()
        else:
            print("There's not any non system HID class device available")
