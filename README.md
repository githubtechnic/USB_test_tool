# typec earphone test tool
python���:
pyQt, pyusb, pywinusb.

pyQt����UI��ʾ.
pywinusb��
        �ŵ�:
            ���յ��̼�������Ϣ,���ڰ������.
        ȱ��:
            ֧��report����,���ǹ̼���֧��report direction(�̼�--->pc).��������ĵ�û����pywinusb
            ����vendor msg��֧��.
pyusb:
        �ܷ���ʹ��vendor msg�͹̼�������ͨ��USB���ƴ��䷽ʽ��̼���ѯ��Ϣ(��ѯSW Version,SN��).

����ṹ��
    �����̽���UI��ʾ.�����߳�ProgressMonitor���ڽ��������ӽ��̵���Ϣ.
    �ӽ���(USBHID_Process)ͨ��pyusb���չ̼���ö����Ϣ,��ѯ�̼���Sw Version��SN.��ѯ���ͨ��pipe���͸�
    ��������ʾ.