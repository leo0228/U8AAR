import file_utils
import os
import os.path
import config_utils
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
import os
import os.path
import zipfile
import re
import subprocess
import platform
from xml.dom import minidom
import codecs
import sys
import shutil
import time
from PIL import Image
import image_utils
import log_utils
import smali_utils

androidNS = 'http://schemas.android.com/apk/res/android'

def xsigncode(workDir, game, channel, apkfile):

    xignClearcmd = '"%sxapk_sign clean" "%s" ' % (file_utils.getXignDir(),apkfile)

    file_utils.execFormatCmd(xignClearcmd)

    xigncmd = '"%sxapk_sign" "%s" ' % (file_utils.getXignDir(),apkfile)

    file_utils.execFormatCmd(xigncmd)

    signApk(workDir, game, channel, apkfile)



def signApk(workDir, game, channel, apkfile):
    """
        Sign apk
    """

    keystore = config_utils.getKeystore(game["appName"], channel["id"])

    #如果你想每次打包自动生成一个keystore文件，那么可以启用下面这句代码
    #keystore = generateKeystore(workDir, game, channel)

    log_utils.info("the keystore file is %s", keystore['keystore'])
    signApkInternal(apkfile, keystore['keystore'], keystore['password'], keystore['aliaskey'], keystore['aliaspwd'], keystore['sigalg'])


def signApkInternal(apkfile, keystore, password, alias, aliaspwd, sigalg):

    apkfile = file_utils.getFullPath(apkfile)
    keystore = file_utils.getFullPath(keystore)
    aapt = file_utils.getFullToolPath("aapt")

    if not os.path.exists(keystore):
        log_utils.error("the keystore file is not exists. %s", keystore)
        return 1

    listcmd = '%s list %s' % (aapt, apkfile)

    output = os.popen(listcmd).read()
    for filename in output.split('\n'):
        if filename.find('META_INF') == 0:
            rmcmd = '"%s" remove "%s" "%s"' % (aapt, apkfile, filename)
            file_utils.execFormatCmd(rmcmd)


    if sigalg is None:
        sigalg = "SHA1withRSA"

    signcmd = '"%sjarsigner" -digestalg SHA1 -sigalg %s -keystore "%s" -storepass "%s" -keypass "%s" "%s" "%s" ' % (file_utils.getJavaBinDir(),sigalg,
            keystore, password, aliaspwd, apkfile, alias)

    ret = file_utils.execFormatCmd(signcmd)

    return ret