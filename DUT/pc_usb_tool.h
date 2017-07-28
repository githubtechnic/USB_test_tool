#ifndef pc_usb_tool_h
#define pc_usb_tool_h

#ifdef __cplusplus
extern "C" {
#endif

// #ifdef PC_USB_TOOL_SUPPT
#define HEX_BUILD_INFO_MAGIC    0xBE57341D
#define STR_QUERY_SW_VER    "QUERY_SW_VER"
#define STR_QUERY_SN        "QUERY_SN"
#define STR_QUERY_VOLTAGE   "QUERY_VOL"
typedef enum _QUERY_TYPE_ENUM
{
    QUERY_IDLE,
    QUERY_SW_VER,
    QUERY_SN,
    QUERY_VOLTAGE,
    QUERY_MAX_NUM,
}QUERY_TYPE_ENUM;

#define FACTORY_SEC_VER 2
#define FACTORY_SEC_MAGIC      0xba80
typedef enum
{
    dev_version_and_magic,      //0
    dev_crc,                    // 1
    dev_reserv1,                // 2
    dev_reserv2,                //3// 3
    dev_name,                   //[4~66]
    dev_bt_addr=67,                //[67~68]
    dev_ble_addr=69,               //[69~70]
    dev_dongle_addr = 71,           //71
    dev_xtal_fcap=73,               //73
    dev_serial_number=74,               //[74~82]
    dev_data_len,
    dev_factory_flash_addr = 1023,
}nvrec_dev_enum;


int usb_test_tool_vendor_msg(struct USB_AUDIO_VENDOR_MSG_T *msg);
void pc_usb_set_key_voltage (uint8_t key_id, uint16_t key_vol);

// #endif
#ifdef __cplusplus
}
#endif

#endif