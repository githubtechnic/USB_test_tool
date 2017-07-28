# typec earphone test tool
python组件:
pyQt, pyusb, pywinusb.

pyQt负责UI显示.
pywinusb：
        优点:
            接收到固件按键消息,用于按键检测.
        缺点:
            支持report交互,但是固件不支持report direction(固件--->pc).查了相关文档没看到pywinusb
            对于vendor msg的支持.
pyusb:
        很方便使用vendor msg和固件交互。通过USB控制传输方式向固件查询信息(查询SW Version,SN等).

代码结构：
    主进程进行UI显示.开启线程ProgressMonitor用于接受来自子进程的消息.
    子进程(USBHID_Process)通过pyusb接收固件的枚举信息,查询固件的Sw Version和SN.查询结果通过pipe发送给
    主进程显示.