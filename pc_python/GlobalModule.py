import os,sys
import json, string
from collections import OrderedDict

g_thistool_version = ' V1.0.7'
G_APP_NAME = 'Bes USB Tester'

DEVICE_NOT_FOUND = 'DEVICE_NOT_FOUND'
DEVICE_INFO = 'DEVICE_INFO'
DEVICE_SWVER_SN = 'DEVICE_SWVER_SN'
DEVICE_CONNECTING = 'DEVICE_CONNECTING'
DEVICE_CONNECTED = 'DEVICE_CONNECTED'
DEVICE_DISCONNECTED = 'DEVICE_DISCONNECTED'
STR_QUERY_SW_VER = 'QUERY_SW_VER'
STR_QUERY_SN = 'QUERY_SN'
STR_QUERY_VOLTAGE = 'QUERY_VOL'

STR_UPDATE_KEY_VOLT = 'UPDATE_KEY_VOLT'

class GlobalModule(object):
    json_cfg_data = None
    json_path = 'config\\config.json'
    def __init__(self):
        pass

    @staticmethod
    def get_tool_config():
        '''get config from config/config.json'''
        exist_flag = os.path.isfile(GlobalModule.json_path)
        if exist_flag is False:
            return None
        try:
            readobj = open(GlobalModule.json_path).read()
        except os.error:
            return None
        try:
            GlobalModule.json_cfg_data = json.loads(readobj, object_pairs_hook=OrderedDict)
        except os.error:
            return None
        return GlobalModule.json_cfg_data

    @staticmethod
    def get_config_vendor_product_id():
        '''get vendor id and product id'''
        cfg = GlobalModule.get_tool_config()
        str_vendor_id = str(cfg['Device']['vendor_id'])
        str_product_id = str(cfg['Device']['product_id'])
        vendor_id = string.atoi(str_vendor_id, 16)
        product_id = string.atoi(str_product_id, 16)
        return vendor_id, product_id
