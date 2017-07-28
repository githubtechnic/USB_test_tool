#include <string.h>
#include "hal_trace.h"
#include "usb_audio.h"
#include "pc_usb_tool.h"
#include "crc32.h"

#define PC_USB_TOOL_SUPPT
#ifdef PC_USB_TOOL_SUPPT

//static uint16_t s_last_key_vol;
//static uint8_t s_last_key_id;
static uint32_t s_last_key_vol_id;

static uint8_t build_info_data[256];
static QUERY_TYPE_ENUM pctool_query_type = QUERY_IDLE;
// static uint32_t build_info_length = 0;

void pc_usb_set_key_voltage (uint8_t key_id, uint16_t key_vol)
{
    s_last_key_vol_id = ((key_vol << 16) | key_id);
}

static void pc_usb_query_type_set(struct USB_AUDIO_VENDOR_MSG_T *msg)
{
    size_t ret;

    if (0 == msg->length)
        return;
    ret = memcmp((void *)msg->data, (void *)STR_QUERY_SW_VER, strlen((char *)STR_QUERY_SW_VER));
    if (0 == ret)
    {
        pctool_query_type = QUERY_SW_VER;
        // memset(build_info_data, 0, sizeof(build_info_data));
        // msg->data = NULL;
        // msg->length = 0;
        return;
    }
    ret = memcmp((void *)msg->data, (void *)STR_QUERY_SN, strlen((char *)STR_QUERY_SN));
    if (0 == ret)
    {
        pctool_query_type = QUERY_SN;
        return;
    }
    ret = memcmp((void *)msg->data, (void *)STR_QUERY_VOLTAGE, strlen((char *)STR_QUERY_VOLTAGE));
    if (0 == ret)
    {
        pctool_query_type = QUERY_VOLTAGE;
        return;
    }
    TRACE("unknown pc usb tool query type:%s", msg->data);
    pctool_query_type = QUERY_IDLE;
}

static void pc_usb_query_type_reset(void)
{
    pctool_query_type = QUERY_IDLE;
}

static int build_info_data_init(void)
{
    uint32_t boot_struct_data[4];
    uint32_t build_info_addr = 0;
    // uint8_t *uint8_ptr = NULL;
    // bool find_buildinfo_magic = false;

    memcpy((void *)boot_struct_data,(void *)0x6c020000,sizeof(boot_struct_data));//FLASH_REGION_BASE
    build_info_addr = boot_struct_data[3];
    if (0 == build_info_addr)
    {
        TRACE("without build info.");
        return -1;
    }
    // TRACE("ln %d",__LINE__);
    memset(build_info_data, 0, sizeof(build_info_data));
    memcpy((void *)build_info_data, (void *)build_info_addr, sizeof(build_info_data));
#if 0
    uint8_ptr = build_info_data;
    while((NULL != uint8_ptr) && (build_info_length < sizeof(build_info_data)))
    {
        uint32_t *tmp_uint32_value = (uint32_t *)uint8_ptr;
        if(HEX_BUILD_INFO_MAGIC == *tmp_uint32_value)
        {
            find_buildinfo_magic = true;
            break;
        }
        uint8_ptr += 1;
        build_info_length += 1;
    }
    if(!find_buildinfo_magic)
    {
        memset(build_info_data, 0, sizeof(build_info_data));
        build_info_length = 0;
        TRACE("ln %d",__LINE__);
        return -1;
    }
#endif
    // TRACE("ln %d",__LINE__);
    return 0;
}

static uint8_t *get_sn_from_factory_sect(void)
{
    static uint8_t str_sn[32];
    uint32_t calc_crc, flash_crc;
    uint32_t ver_magic_value;
    uint32_t *factory_ptr = (uint32_t *)0x6c0ff000;

    ver_magic_value = factory_ptr[0];
    TRACE("------------------ver and magic 0x%x-----------------", ver_magic_value);
    if(ver_magic_value != ((FACTORY_SEC_VER<<16)|FACTORY_SEC_MAGIC))
    {
        TRACE("unmatched factory section ver or magic!");
        return (uint8_t *)"SN INVALID!";
    }
    flash_crc = factory_ptr[1];
    TRACE("------------------flash crc 0x%x-----------------", flash_crc);
    calc_crc = crc32(0,(unsigned char *)(&factory_ptr[dev_reserv1]),(dev_factory_flash_addr-dev_reserv1)*sizeof(uint32_t));
    TRACE("------------------calc crc 0x%x-----------------", calc_crc);
    if (flash_crc != calc_crc)
    {
        TRACE("Invalid factory section crc!");
        return (uint8_t *)"SN INVALID!";
    }
    memset(str_sn, 0, sizeof(str_sn));
    memcpy(str_sn, (void *)(0x6c0ff000+(dev_serial_number*sizeof(uint32_t))), sizeof(str_sn));
    memcpy(str_sn, (void *)(&factory_ptr[dev_serial_number]), sizeof(str_sn));
    TRACE("SN read from flash:%s", str_sn);
    return (uint8_t *)str_sn;
}

static uint8_t *get_sw_ver_from_dut(void)
{
    uint32_t i = 0;
    uint8_t *target_value = NULL;

    target_value = (uint8_t *)strstr((char *)build_info_data, (char *)"SW_VER=");
    if (NULL == target_value)
    {
        return NULL;
    }
    target_value += strlen("SW_VER=");
    while(target_value[i] != 0xA)
        i++;
    target_value[i] = 0;
    return target_value;
}

int usb_test_tool_vendor_msg(struct USB_AUDIO_VENDOR_MSG_T *msg)
{
    static uint32_t init_ret = -1;
    uint8_t *target_value = NULL;
    static bool init_flag = false;
    // static const char *msg_data = "gyt is a fancy of Peppa Pig.";
    
    TRACE("@@@@@@@@@@@@@@@@@@@@length %d, %s", msg->length, msg->data);
    if(!init_flag)
    {
        init_ret = build_info_data_init();
        init_flag = true;
    }
    if (0 != init_ret)
    {
        msg->data = (uint8_t *)"without build info";
        msg->length = (uint16_t)strlen((const char *)msg->data);
        return 0;
    }
    if(0 == msg->length)
    {
        if(QUERY_SW_VER == pctool_query_type)
        {
            target_value = get_sw_ver_from_dut();
            if (NULL == target_value)
            {
                msg->data = (uint8_t *)"INVALID SW VER!";
                msg->length = (uint32_t)strlen((const char *)"INVALID SW VER!");
            }
            else
            {
                TRACE("sw_ver = %s", target_value);
                msg->data = (uint8_t *)target_value;
                msg->length = (uint32_t)strlen((const char *)target_value);
            }
        }
        else if(QUERY_SN == pctool_query_type)
        {
            msg->data = get_sn_from_factory_sect();
            TRACE("msg->data sn %s", msg->data);
            msg->length = (uint32_t)strlen((const char *)msg->data);
        }
        else if(QUERY_VOLTAGE == pctool_query_type)
        {
            TRACE("pctool query voltage.");
#if 0
            switch (s_last_key_id) {
                case 0: // vol+
                    // TODO:
                    break;
                case 1: // play
                    break;
                case 2: // vol-
                    break;
            }
#else
            //msg->data = (uint8_t *)&s_last_key_vol;
            //msg->length = sizeof(uint16_t);
            msg->data = (uint8_t *)&s_last_key_vol_id;
            msg->length = sizeof(uint32_t);
#endif
        }
        else
            TRACE("pctool query type %d.", pctool_query_type);

        pc_usb_query_type_reset();
    }
    else
    {
        pc_usb_query_type_set(msg);
        TRACE("current query type %d", pctool_query_type);
    }

    return 0;
}
#endif//PC_USB_TOOL_SUPPT
