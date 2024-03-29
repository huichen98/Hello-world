# -- coding: utf-8 --
# import numpy as np
import sys
import threading
import msvcrt
import numpy as np
from ctypes import *
from yolo import YOLO
from PIL import Image
import cv2
import numpy as np

sys.path.append("./GrabImage")
from MvCameraControl_class import *

g_bExit = False
yolo = YOLO()

# 为线程定义一个函数
def work_thread(cam=0, pData=0, nDataSize=0):
    stFrameInfo = MV_FRAME_OUT_INFO_EX()
    memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
    while True:
        temp = np.asarray(pData)  # 将c_ubyte_Array转化成ndarray得到（6041280）
        # print(pData) #<__main__.c_ubyte_Array_6041280 object at 0x000001A1F36BA7C8>,需要进行转化
        # print(temp) #[  0  61  49 ... 255 255 255]，一维数组
        temp = temp.reshape((1240, 1624, 3))  # 根据自己分辨率进行转化
        # print(temp.shape)
        temp = cv2.cvtColor(temp, cv2.COLOR_RGB2BGR)  # opencv显示为bgr格式，需要将相机读取到的rgb图像转变为bgr图像进行显示
        image = Image.fromarray(temp)
        # print(image)
        # image = Image.open(temp)
        temp_result = yolo.detect_image(image)
        temp_result = np.array(temp_result)
        cv2.namedWindow("result", 0)
        cv2.resizeWindow("result", 640, 480)
        cv2.imshow("result", temp_result)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        ret = cam.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 1000)
        # nWidth = stFrameInfo.nWidth
        # nHeight = stFrameInfo.nHeight
        # if ret == 0:
        #     print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
        #     stFrameInfo.nWidth, stFrameInfo.nHeight, stFrameInfo.nFrameNum))
        # else:
        #     print("no data[0x%x]" % ret)

        if g_bExit == True:
            break


deviceList = MV_CC_DEVICE_INFO_LIST()
tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE

# ch:枚举设备 | en:Enum device
ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
# if ret != 0:
#     print("enum devices fail! ret[0x%x]" % ret)
#     sys.exit()
#
# if deviceList.nDeviceNum == 0:
#     print("find no device!")
#     sys.exit()

# print("Find %d devices!" % deviceList.nDeviceNum)

for i in range(0, deviceList.nDeviceNum):
    mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
    if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
        print("\ngige device: [%d]" % i)
        strModeName = ""
        for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
            strModeName = strModeName + chr(per)
        print("device model name: %s" % strModeName)

        nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
        nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
        nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
        nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
        print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
    elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
        print("\nu3v device: [%d]" % i)
        strModeName = ""
        for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
            if per == 0:
                break
            strModeName = strModeName + chr(per)
        print("device model name: %s" % strModeName)

        strSerialNumber = ""
        for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
            if per == 0:
                break
            strSerialNumber = strSerialNumber + chr(per)
        print("user serial number: %s" % strSerialNumber)

# nConnectionNum = input("please input the number of the device to connect:")
nConnectionNum = 0
# if int(nConnectionNum) >= deviceList.nDeviceNum:
#     print("intput error!")
#     sys.exit()

# ch:创建相机实例 | en:Creat Camera Object
cam = MvCamera()

# ch:选择设备并创建句柄 | en:Select device and create handle
stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

ret = cam.MV_CC_CreateHandle(stDeviceList)
if ret != 0:
    print("create handle fail! ret[0x%x]" % ret)
    sys.exit()

# ch:打开设备 | en:Open device
ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
if ret != 0:
    print("open device fail! ret[0x%x]" % ret)
    sys.exit()

# ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
# if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
#     nPacketSize = cam.MV_CC_GetOptimalPacketSize()
#     if int(nPacketSize) > 0:
#         ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
#         if ret != 0:
#             print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
#     else:
#         print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

stBool = c_bool(False)
ret = cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", byref(stBool))
if ret != 0:
    print("get AcquisitionFrameRateEnable fail! ret[0x%x]" % ret)
    sys.exit()

# ch:设置触发模式为off | en:Set trigger mode as off
ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
if ret != 0:
    print("set trigger mode fail! ret[0x%x]" % ret)
    sys.exit()

# ch:获取数据包大小 | en:Get payload size
stParam = MVCC_INTVALUE()
memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))

ret = cam.MV_CC_GetIntValue("PayloadSize", stParam)
if ret != 0:
    print("get payload size fail! ret[0x%x]" % ret)
    sys.exit()
nPayloadSize = stParam.nCurValue

# ch:开始取流 | en:Start grab image
ret = cam.MV_CC_StartGrabbing()
if ret != 0:
    print("start grabbing fail! ret[0x%x]" % ret)
    sys.exit()

data_buf = (c_ubyte * nPayloadSize)()

try:
    # hThreadHandle = threading.Thread(target=work_thread, args=(cam, byref(data_buf), nPayloadSize))
    hThreadHandle = threading.Thread(target=work_thread, args=(cam, data_buf, nPayloadSize))
    hThreadHandle.start()
except:
    print("error: unable to start thread")

# print("press a key to stop grabbing.")
# msvcrt.getch()

# g_bExit = True
hThreadHandle.join()

# ch:停止取流 | en:Stop grab image
ret = cam.MV_CC_StopGrabbing()
if ret != 0:
    print("stop grabbing fail! ret[0x%x]" % ret)
    del data_buf
    sys.exit()

# ch:关闭设备 | Close device
ret = cam.MV_CC_CloseDevice()
if ret != 0:
    print("close deivce fail! ret[0x%x]" % ret)
    del data_buf
    sys.exit()

# ch:销毁句柄 | Destroy handle
ret = cam.MV_CC_DestroyHandle()
if ret != 0:
    print("destroy handle fail! ret[0x%x]" % ret)
    del data_buf
    sys.exit()

del data_buf