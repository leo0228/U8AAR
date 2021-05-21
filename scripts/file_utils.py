# -*- coding: utf-8 -*-
# Author:xiaohei
# CreateTime:2014-10-25
#
# All file operations are defined here
import os
import os.path
import re
import platform
import subprocess
import inspect
import sys
import codecs
import threading
import time
import log_utils
import zipfile
import apk_utils


curDir = os.getcwd()

def list_files(src, resFiles, igoreFiles):

    if os.path.exists(src):
        if os.path.isfile(src) and src not in igoreFiles:
            resFiles.append(src)
        elif os.path.isdir(src):            
            for f in os.listdir(src):
                if f == 'aars' or f == 'assets' or f == 'icon_marks' or f == 'res' or f == 'splash':
                    continue
                if src not in igoreFiles:
                    list_files(os.path.join(src, f), resFiles, igoreFiles)

    return resFiles


def del_file_folder(src):
    if os.path.exists(src):
        if os.path.isfile(src):
            try:
                src = src.replace('\\', '/')
                os.remove(src)
            except:
                pass

        elif os.path.isdir(src):
            for item in os.listdir(src):
                itemsrc = os.path.join(src, item)
                del_file_folder(itemsrc)

            try:
                os.rmdir(src)
            except:
                pass


def copy_files(src, dest):
    if not os.path.exists(src):
        log_utils.warning("the src is not exists.path:%s", src)
        return

    if os.path.isfile(src):
        copy_file(src, dest)
        return

    for f in os.listdir(src):
        sourcefile = os.path.join(src, f)
        targetfile = os.path.join(dest, f)
        if os.path.isfile(sourcefile):
            copy_file(sourcefile, targetfile)
        else:
            copy_files(sourcefile, targetfile)


def copy_file(src, dest):
    sourcefile = getFullPath(src)
    destfile = getFullPath(dest)
    if not os.path.exists(sourcefile):
        return
    if not os.path.exists(destfile) or os.path.getsize(destfile) != os.path.getsize(sourcefile):
        destdir = os.path.dirname(destfile)
        if not os.path.exists(destdir):
            os.makedirs(destdir)
        destfilestream = open(destfile, 'wb')
        sourcefilestream = open(sourcefile, 'rb')
        destfilestream.write(sourcefilestream.read())
        destfilestream.close()
        sourcefilestream.close()

#Author:卢天骄
#解压渠道SDKaar文件到工作文件夹aars
def decomAAR(sdkDestDir):
    libsDir = os.path.join(sdkDestDir, "libs")
    if not os.path.exists(libsDir):
        os.makedirs(dstResDir) 

    for f in os.listdir(libsDir):
        if f.endswith(".aar"):

            aarsDestDir = os.path.join(sdkDestDir, "aars", f)
            aarPath = os.path.join(libsDir, f)
            #里面有support-v4                      
            if f == 'core-1.0.0.aar':
                del_file_folder(os.path.join(libsDir, f))   
                continue

            zip_file = zipfile.ZipFile(aarPath)
            for names in zip_file.namelist():
                zip_file.extract(names, aarsDestDir)
            zip_file.close()  

            #解压后删除aar文件
            del_file_folder(os.path.join(libsDir, f))

            #copy资源
            copyAARJarToLibs(aarsDestDir, sdkDestDir, str(f))    
   
            #合并 manifest
            apk_utils.mergeManifestAARToSDK(aarsDestDir, sdkDestDir)


#Author:卢天骄
#复制渠道SDKaar资源到工作文件夹
def copyAARJarToLibs(aarsDestDir, sdkDestDir, aarName):
    
    destAsstesDir = os.path.join(sdkDestDir, "assets");
    if not os.path.exists(destAsstesDir):
        os.makedirs(destAsstesDir)

    destLibsDir = os.path.join(sdkDestDir, "libs")
    if not os.path.exists(destLibsDir):
        os.makedirs(destLibsDir)

    destResDir = os.path.join(sdkDestDir, "res")
    if not os.path.exists(destResDir):
        os.makedirs(destResDir)

    for f in os.listdir(aarsDestDir):
        #分割最后一个“.” 
        name = aarName.rsplit(".", 1)[0]
        destLibsName = os.path.join(destLibsDir, name + ".jar")

        if f.endswith(".jar"):    
            copy_file(os.path.join(aarsDestDir, f), destLibsName)
                            
        if "assets" == f:           
            copy_files(os.path.join(aarsDestDir, f), destAsstesDir)

        if "jni" == f: 
            aarJniDestDir = os.path.join(aarsDestDir, f)
            for jniF in os.listdir(aarJniDestDir):                             
                if "armeabi" == jniF or "armeabi-v7a" == jniF or "x86" == jniF:
                    jniDestDir = os.path.join(destLibsDir, jniF)
                    if not os.path.exists(jniDestDir):
                        os.makedirs(jniDestDir)
                    copy_files(os.path.join(aarJniDestDir, jniF), jniDestDir)

        if "libs" == f:     
            aarLibsDestDir = os.path.join(aarsDestDir, f)
            #部分aar包中的classes.jar里面并没有class，而是在aar包中libs里面的classes.jar
            for libF in os.listdir(aarLibsDestDir):
                if libF == "classes.jar":
                    #如果SDK libs里面已经存在先删除，在复制一次
                    if os.path.exists(destLibsName):
                        del_file_folder(destLibsName)
                                 
                    copy_file(os.path.join(aarLibsDestDir, libF), destLibsName)
                else:
                    copy_file(os.path.join(aarLibsDestDir, libF), os.path.join(destLibsDir, libF))
               
        if "res" == f:
            apk_utils.copyResToApk(os.path.join(aarsDestDir, f), destResDir)


def modifyFileContent(sourcefile, oldContent, newContent):
    
    if os.path.isdir(sourcefile):
        log_utils.warning("the source %s must be a file not a dir", sourcefile)
        return

    if not os.path.exists(sourcefile):
        log_utils.warning("the source is not exists.path:%s", sourcefile)
        return

    f = open(sourcefile, 'r+')
    data = str(f.read())
    f.close()
    bRet = False
    idx = data.find(oldContent)
    while idx != -1:
        data = data[:idx] + newContent + data[idx + len(oldContent):]
        idx = data.find(oldContent, idx + len(oldContent))
        bRet = True

    if bRet:
        fw = open(sourcefile, 'w')
        fw.write(data)
        fw.close()
        log_utils.info("modify file success.path:%s", sourcefile)
    else:
        log_utils.warning("there is no content matched in file:%s with content:%s", sourcefile, oldContent)


def getCurrDir():
    global curDir
    retPath = curDir
    if platform.system() == 'Darwin':
        retPath = sys.path[0]
        lstPath = os.path.split(retPath)
        if lstPath[1]:
            retPath = lstPath[0]

    return retPath


def getFullPath(filename):
    if os.path.isabs(filename):
        return filename
    currdir = getCurrDir()
    filename = os.path.join(currdir, filename)
    filename = filename.replace('\\', '/')
    filename = re.sub('/+', '/', filename)
    return filename

def getSplashPath():
    return getFullPath("config/splash")

def getJavaBinDir():
    if platform.system() == 'Windows':
        return getFullPath("tool/win/jre/bin/")
    else:
        return ""

#获取xigncode对应的文件夹
def getXignDir():
    if platform.system() == 'Windows':
        return getFullPath("tool/apk_signing_tools/")
    else:
        return ""

def getJavaCMD():
    return getJavaBinDir() + "java"

def getToolPath(filename):
    if platform.system() == 'Windows':
        return "tool/win/" + filename
    else:
        return "tool/mac/" + filename


def getFullToolPath(filename):
    return getFullPath(getToolPath(filename))

def getFullOutputPath(appName, channel):
    path = getFullPath('output/' + appName + '/' + channel)
    #del_file_folder(path)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def execFormatCmd(cmd):
    cmd = cmd.replace('\\', '/')
    cmd = re.sub('/+', '/', cmd)
    ret = 0

    try:
        reload(sys)
        sys.setdefaultencoding('utf-8')

        #s = subprocess.Popen(cmd, shell=True)
        s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdoutput, erroutput = s.communicate()

        if platform.system() == 'Windows':
            stdoutput = stdoutput.decode('gbk')
            erroutput = erroutput.decode('gbk')
            
        ret = s.returncode

        if ret:
            #s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            #stdoutput, erroutput = s.communicate()

            log_utils.error("*******ERROR*******")
            log_utils.error(stdoutput)
            log_utils.error(erroutput)
            log_utils.error("*******************")

            cmd = 'error::' + cmd + '  !!!exec Fail!!!  '
        else:

            #s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            #stdoutput, erroutput = s.communicate()

            log_utils.info(stdoutput)
            log_utils.info(erroutput)

            cmd = cmd + ' !!!exec success!!! '

        log_utils.info(cmd)

    except Exception as e:
        log_utils.error(e)
        return

    return ret


def execWinCommand(cmd):
    os.system(cmd)  


def execWinCommandInput(tip):
    r = os.popen("set /p s=" + tip)
    txt = r.read()
    r.close()
    return txt

def on_access_error(func, path, exc_info):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def printLogo():

    u = [
        "$$    $$",
        "$$    $$",
        "$$    $$",
        "$$    $$",
        " $$$$$$ "
    ]

    n8=[
        " $$$$$$ ",
        "$$    $$",
        " $$$$$$ ",
        "$$    $$",
        " $$$$$$ "
    ]

    s=[
        " $$$$$$ ",
        " $$     ",
        " $$$$$$ ",
        "     $$ ",
        " $$$$$$ "
    ]

    d=[
        "$$$$$$  ",
        "$     $$",
        "$     $$",
        "$     $$",
        "$$$$$$  "
    ]

    k=[
        "$$    $$",
        "$$  $$  ",
        "$$$$    ",
        "$$  $$  ",
        "$$    $$"
    ]

    print("################################################################")
    print(" ")
    for i in range(0, len(u)):
        line = "    " + u[i] + "    " + n8[i] + "    " + s[i] + "    " + d[i] + "    " + k[i]
        print(line)

    print(" ")
    print("################################################################")

