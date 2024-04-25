#!/usr/bin/env python3
# -- coding: utf-8 --

# SPDX-FileCopyrightText: Bosch Rexroth AG
#
# SPDX-License-Identifier: MIT

import signal
import time
import sys
import threading
import termios
import os
from datetime import datetime
from typing import List

from flask import Flask, request, render_template, redirect, send_from_directory
import shutil

import numpy as np
import cv2
import argparse
import pytesseract
import re

from ctypes import *

from MVImport.MvCameraControl_class import *

import threading
import logging
from time import time
from time import sleep

from pyModbusTCP.server import ModbusServer

logger = logging.getLogger(__name__)


__close_app = False


global g_numArray
g_numArray = None

MEDIA_FOLDER = '/var/snap/rexroth-solutions/common/solutions/activeConfiguration/active/'

app = Flask(__name__)
app.secret_key = b'_1#y2l"F4Q8z\n\xec]/'

variable = 99
lst = "EMPTY"
time_duration = 0.0
email_ext = "EMPTY"
time_toweb = 0.0
s = "TEMP"
ip_modbus = " "
img_scale=2.5
jpeg_quality = 90
temp_ip = " "
reg_string = "\S+@\S+"

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(MEDIA_FOLDER, filename, as_attachment=True)
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    global variable
    global email_ext
    global time_toweb
    global time_duration
    global ip_modbus
    global img_scale
    global jpeg_quality
    global reg_string
    if request.method == "POST":
        try:
            if request.form.get("variable"):
                variable = int(request.form.get("variable"))
                return redirect('/')   
            elif request.form.get("ip_modbus"):       
                ip_modbus = str(request.form.get("ip_modbus"))
                return redirect('/')
            elif request.form.get("img_scale"):
                img_scale = float(request.form.get("img_scale"))
                return redirect('/')
            elif request.form.get("jpeg_quality"):
                jpeg_quality = int(request.form.get("jpeg_quality"))
                return redirect('/')
            elif request.form.get("reg_string"):
                jpeg_quality = str(request.form.get("reg_string"))
                return redirect('/')
        except:
            print("Wrong data type")
        return redirect('/')
        
    return render_template('index.html', variable=variable, email_ext=email_ext, time_toweb=time_toweb, ip_modbus=ip_modbus, img_scale=img_scale, jpeg_quality=jpeg_quality, reg_string=reg_string)


def handler(signum, frame):
    """handler"""
    global __close_app
    __close_app = True
    # print('Here you go signum: ', signum, __close_app, flush=True)




# Mono图像转为python数组
def Mono_numpy(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
    data_mono_arr = data_.reshape(nWidth, nHeight)
    numArray = np.zeros([nWidth, nHeight, 1], "uint8")
    numArray[:, :, 0] = data_mono_arr
    return numArray


# 彩色图像转为python数组
def Color_numpy(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
    data_r = data_[0:nWidth * nHeight * 3:3]
    data_g = data_[1:nWidth * nHeight * 3:3]
    data_b = data_[2:nWidth * nHeight * 3:3]

    data_r_arr = data_r.reshape(nWidth, nHeight)
    data_g_arr = data_g.reshape(nWidth, nHeight)
    data_b_arr = data_b.reshape(nWidth, nHeight)
    numArray = np.zeros([nWidth, nHeight, 3], "uint8")

    numArray[:, :, 0] = data_r_arr
    numArray[:, :, 1] = data_g_arr
    numArray[:, :, 2] = data_b_arr
    return numArray

def startApp():
    app.run(debug=False, host='0.0.0.0', port=8001)

def sig():
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGABRT, handler)

def mbServ():

    global ip_modbus    
    global variable
    global email_ext
    global lst
    global temp_ip
    
   

    
    while not __close_app:

        server = ModbusServer(ip_modbus, 12345, no_block=True)


        if ip_modbus!=temp_ip:

            temp_ip=ip_modbus
            print("Starting Server...")
            server.start()
            print("Server is online")
            state = [0]    
        
        if variable == 2:               
            
            res = bytes(lst[0], 'utf-8')
            server.data_bank.set_holding_registers(0, res)
            print(res)
        
            
        sleep(1)



def read_text_from_image(image):
    """Reads text from an image file and outputs found text to text file"""
    # Convert the image to grayscale
    global s
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Perform OTSU Threshold
    ret, thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))

    dilation = cv2.dilate(thresh, rect_kernel, iterations = 1)

    contours, hierachy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    image_copy = image.copy()

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        cropped = image_copy[y : y + h, x : x + w]
   
        s = pytesseract.image_to_string(cropped, lang='eng', config='--psm 11, --oem 3')

    



def main():
    """main"""    


    while not  __close_app:
        global variable
        global time_duration
        global lst
        global s
        global email_ext
        global time_toweb
        global jpeg_quality
        global reg_string


        if variable==0:

            SDKVersion = MvCamera.MV_CC_GetSDKVersion()
            print("SDKVersion[0x%x]" % SDKVersion)
            deviceList = MV_CC_DEVICE_INFO_LIST()
            tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE

            # ch:枚举设备 | en:Enum device
            ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
            if ret != 0:
                print("enum devices fail! ret[0x%x]" % ret)
                sys.exit()

            if deviceList.nDeviceNum == 0:
                print("find no device!")
                sys.exit()

            print("Find %d devices!" % deviceList.nDeviceNum)

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

            nConnectionNum = 0

            if int(nConnectionNum) >= deviceList.nDeviceNum:
                print("intput error!")
                sys.exit()

            # ch:创建相机实例 | en:Creat Camera Object
            cam = MvCamera()

            # ch:选择设备并创建句柄| en:Select device and create handle
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
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                    if ret != 0:
                        print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
                else:
                    print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

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

            
          
            variable = 99    
     


        if variable == 1:

            # ch:开始取流 | en:Start grab image
            ret = cam.MV_CC_StartGrabbing()
            if ret != 0:
                print("start grabbing fail! ret[0x%x]" % ret)
                sys.exit()
        
            stOutFrame = MV_FRAME_OUT()
            memset(byref(stOutFrame), 0, sizeof(stOutFrame))

            ret = cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            time_start=time()

            if None != stOutFrame.pBufAddr and 0 == ret:
                print("get one frame: Width[%d], Height[%d], nFrameNum[%d],nFrameLen[%d]" % (
                    stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum, stOutFrame.stFrameInfo.nFrameLen))

                buf_cache = (c_ubyte * stOutFrame.stFrameInfo.nFrameLen)()
            # 图像数据拷贝
                memmove(byref(buf_cache), stOutFrame.pBufAddr, stOutFrame.stFrameInfo.nFrameLen)
                if PixelType_Gvsp_Mono8 == stOutFrame.stFrameInfo.enPixelType:
                    g_numArray = Mono_numpy(buf_cache, stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight)
                    g_numArray = g_numArray.reshape(stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth, 1)
                elif PixelType_Gvsp_RGB8_Packed == stOutFrame.stFrameInfo.enPixelType:
                    g_numArray = Color_numpy(buf_cache, stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight)
                    g_numArray = g_numArray.reshape(stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth, 3)
                else:
                    print("Not Support")
                    sys.exit()            
            
        
                cv2.imwrite('/var/snap/rexroth-solutions/common/solutions/activeConfiguration/active/Image_Mat.jpg', g_numArray, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                imgpy = cv2.imread('/var/snap/rexroth-solutions/common/solutions/activeConfiguration/active/Image_Mat.jpg')
                down_width = int(2592/img_scale)
                down_height = int(1944/img_scale)        
                down_points = (down_width, down_height)
                resized_down = cv2.resize(imgpy, down_points, interpolation = cv2.INTER_LINEAR)
        


                s = pytesseract.image_to_string(resized_down, lang='eng', config='--psm 11--oem 3')


                lst = re.findall(reg_string, s)
                time_end=time()
                time_full=time_end-time_start
    
                time_duration=round(time_full, 3)


                nRet = cam.MV_CC_FreeImageBuffer(stOutFrame)

                # ch:停止取流 | en:Stop grab image
                ret = cam.MV_CC_StopGrabbing()
                if ret != 0:
                    print ("stop grabbing fail! ret[0x%x]" % ret)
                    del data_buf
                    sys.exit()

        
                    
                variable = 99
                email_ext = lst
                time_toweb = time_duration
            
            else:
                print("no data[0x%x]" % ret)
                
            variable = 99
        

                



if __name__ == "__main__":
    sig()
    try:
        logger.info(f'First thread')
        t1 = threading.Thread(target=startApp).start()
        logger.info(f'Second thread')
        t2 = threading.Thread(target=main).start()
        logger.info(f'Third thread')
        t3 = threading.Thread(target=mbServ).start()

        
    except Exception as e:
        logger.error("Error: " + str(e))  
