# -- coding: utf-8 --
# 该示例程序说明了如何通过主动取图的方式获取相机图像。
# 创建句柄，打开相机，开始取流，创建取流线程（用户分配采集buffer， MV_CC_GetOneFrameTimeout() 取图（拷贝）），停止取流，关闭相机，销毁句柄。
import sys
import threading
import msvcrt
import cv2
from yolo import YOLO
from PIL import Image
import numpy as np
from ctypes import *
from timeit import default_timer as timer

sys.path.append("./GrabImage")
# sys.path.append("../MvImport")   # 安装驱动后在C盘中的路径需要调用上一文件夹中的文件MvImport
from MvCameraControl_class import *
g_bExit = False
yolo = YOLO()

# 为线程定义一个函数
def work_thread(cam=0, pData=0, nDataSize=0):
    stFrameInfo = MV_FRAME_OUT_INFO_EX()
    memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
    # 视频检测中的检测帧率显示
    accum_time = 0   # 累计时间
    curr_fps = 0     # 当前帧数
    fps = "FPS: ??"
    prev_time = timer()   # 当前时间
    while True:
        ret = cam.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 1000)
        nWidth = stFrameInfo.nWidth
        nHeight = stFrameInfo.nHeight
        if ret == 0:
            data_ = np.frombuffer(data_buf, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
            data_r = data_[0:nWidth * nHeight * 3:3]
            data_g = data_[1:nWidth * nHeight * 3:3]
            data_b = data_[2:nWidth * nHeight * 3:3]

            data_r_arr = data_r.reshape(nHeight, nWidth)
            data_g_arr = data_g.reshape(nHeight, nWidth)
            data_b_arr = data_b.reshape(nHeight, nWidth)
            numArray = np.zeros([nHeight, nWidth, 3], "uint8")

            # 调换RGB格式为BGR格式，为opencv读取格式
            numArray[:, :, 2] = data_r_arr
            numArray[:, :, 1] = data_g_arr
            numArray[:, :, 0] = data_b_arr

            ############################自己添加的内容#######################################
            #图像数据来自于numArray变量
            cv2.namedWindow("raw_data", 0)
            # cv2.resizeWindow("raw_data", 640, 480)
            numArray = Image.fromarray(numArray)
            numArray = yolo.detect_image(numArray)
            numArray = np.array(numArray)

            curr_time = timer()            # 记录当前时间
            exec_time = curr_time - prev_time   # 执行时间=当前时间-之前时间
            prev_time = curr_time          # 用当前时间更新之前时间
            accum_time = accum_time + exec_time     # 计算累计时间 = 初始累计时间+执行时间
            curr_fps = curr_fps + 1    # 帧数计数+1
            if accum_time > 1:         # 判断累计时间大于1S，原因帧数为fps
                accum_time = accum_time - 1        # 重新将累计时间减去1s，为下一次计时做准备
                fps = "FPS: " + str(curr_fps)      # 1S累计的帧数
                curr_fps = 0                       # 将累计帧数记为0
            cv2.putText(numArray, text=fps, org=(40, 40), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=2, color=(0, 0, 255), thickness=2)         # 输出在图像中

            cv2.imshow("raw_data", numArray)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # cv2.waitKey(1)
            # cv2.destroyAllWindows()
            ###############################################################################
            # print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stFrameInfo.nWidth, stFrameInfo.nHeight, stFrameInfo.nFrameNum))
        else:
            print("no data[0x%x]" % ret)

deviceList = MV_CC_DEVICE_INFO_LIST()
tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE  # 工业相机的两种接口模式，表示查找GigE和USB3.0设备

# ch:枚举设备 | en:Enum device，根据编程引导第一步枚举所有设备，使用MV_CC_EnumDevices函数
ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
# if ret != 0:
#     print("enum devices fail! ret[0x%x]" % ret)
#     sys.exit()
#
# if deviceList.nDeviceNum == 0:
#     print("find no device!")
#     sys.exit()

# ####################第一个输出（发现设备数量）##################################
# print("Find %d devices!" % deviceList.nDeviceNum)
# ####################################################################

for i in range(0, deviceList.nDeviceNum):
    mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
    # 判断相机设备型号
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
# 判断连接设备数目与输入的设备数目标号是否一致
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
    hThreadHandle = threading.Thread(target=work_thread, args=(cam, byref(data_buf), nPayloadSize))
    hThreadHandle.start()
except:
    print("error: unable to start thread")

# print("press a key to stop grabbing.")
# msvcrt.getch()

g_bExit = True
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
