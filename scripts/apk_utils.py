# -*- coding: utf-8 -*-
#Author:xiaohei
#CreateTime:2014-10-25
#
# All apk operations are defined here
#
#
import io
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
aapt_version= "aapt_64"

def copyLibs(game, srcDir, dstDir):
    """
        copy shared libraries
    """

    if not os.path.exists(srcDir):
        return

    if not os.path.exists(dstDir):
        os.makedirs(dstDir)

    for f in os.listdir(srcDir):
        sourcefile = os.path.join(srcDir, f)
        targetfile = os.path.join(dstDir, f)
        
        if (sourcefile.endswith(".jar")):
            continue

        if os.path.isfile(sourcefile):
            if not os.path.exists(targetfile) or os.path.getsize(targetfile) != os.path.getsize(sourcefile):
                destfilestream = open(targetfile, 'wb')
                sourcefilestream = open(sourcefile, 'rb')
                destfilestream.write(sourcefilestream.read())
                destfilestream.close()
                sourcefilestream.close()

        if os.path.isdir(sourcefile):
            copyLibs(game, sourcefile, targetfile)           

def jar2dex(srcDir, dstDir, dextool = "baksmali.jar"):
    """
        compile jar files to dex.
    """
    dexToolPath = file_utils.getFullToolPath("/lib/dx.jar")
    heapSize = config_utils.getJDKHeapSize()

    cmd = file_utils.getJavaCMD() + ' -jar -Xms%sm -Xmx%sm "%s" --dex --multi-dex --output="%s" ' % (heapSize, heapSize, dexToolPath, dstDir)

    #找到渠道接入文件转为.dex
    for f in os.listdir(srcDir):
        if f.endswith(".jar"):
            cmd = cmd + " " + os.path.join(srcDir, f)

    #将libs里的所有.jar转为.dex
    libsPath = os.path.join(srcDir, "libs")
    if os.path.exists(libsPath):
        for f in os.listdir(libsPath):
            if f.endswith(".jar"):
                cmd = cmd + " " + os.path.join(srcDir, "libs", f)

    ret = file_utils.execFormatCmd(cmd)

    return ret

def dexes2smali(dexDir, targetdir, dextool= "baksmali.jar"):

    """
        Transfer all dex in dexDir to smali
    """

    if not os.path.exists(dexDir):
        log_utils.error("the dexDir is not exists:"+dexDir)
        return 1

    files = file_utils.list_files(dexDir, [], [])
    for f in files:
        if not f.endswith(".dex"):
            continue

        dex2smali(f, targetdir, dextool)


def dex2smali(dexFile, targetdir, dextool = "baksmali.jar"):

    """
        Transfer the dex to smali.
    """

    if not os.path.exists(dexFile):
        log_utils.error("the dexfile is not exists. path:%s", dexFile)
        return 1

    if not os.path.exists(targetdir):
        os.makedirs(targetdir)

    dexFile = file_utils.getFullPath(dexFile)
    smaliTool = file_utils.getFullToolPath(dextool)
    targetdir = file_utils.getFullPath(targetdir)

    cmd = '"%s" -jar "%s" -o "%s" "%s"' % (file_utils.getJavaCMD(), smaliTool, targetdir, dexFile)

    ret = file_utils.execFormatCmd(cmd)

    return ret


def decompileApk(source, targetdir, apktool = "apktool2.jar"):
    """
        Decompile apk
    """
    apkfile = file_utils.getFullPath(source)
    targetdir = file_utils.getFullPath(targetdir)
    apktool = file_utils.getFullToolPath(apktool)
    if os.path.exists(targetdir):
        file_utils.del_file_folder(targetdir)
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)

    heapSize = config_utils.getJDKHeapSize()

    #卢-->添加–only-main-classes参数，针对有的母包assets下面也有dex文件而导致错误
    cmd = '"%s" -jar -Xms%sm -Xmx%sm "%s" -v d -b -f "%s" --only-main-classes -o "%s"' % (file_utils.getJavaCMD(), heapSize, heapSize, apktool, apkfile, targetdir)
    #cmd = '"%s" -jar -Xms%sm -Xmx%sm "%s" -v d -b -f "%s" -o "%s"' % (file_utils.getJavaCMD(), heapSize, heapSize, apktool, apkfile, targetdir)
    #cmd = '"%s" -q d -d -f "%s" "%s"' % (apktool, apkfile, targetdir)
    ret = file_utils.execFormatCmd(cmd)


    #卢-->如果母包中已经拆分出多个smali，复制到第一个smali，并删除，以便于重新计算
    smaliDir = targetdir + "/smali"
    smali2Dir = targetdir + "/smali_classes2"
    if os.path.exists(smali2Dir):
        file_utils.copy_files(smali2Dir, smaliDir)         
        file_utils.del_file_folder(smali2Dir)

    return ret


def recompileApk(sourcefolder, apkfile, apktool = "apktool2.jar"):
    """
        Recompile apk
    """
    os.chdir(file_utils.curDir)
    sourcefolder = file_utils.getFullPath(sourcefolder)
    apkfile = file_utils.getFullPath(apkfile)
    apktool = file_utils.getFullToolPath(apktool)

    ret = 1
    if os.path.exists(sourcefolder):
        heapSize = config_utils.getJDKHeapSize()
        cmd = '"%s" -jar -Xms%sm -Xmx%sm "%s" -v b -f "%s" -o "%s"' % (file_utils.getJavaCMD(), heapSize, heapSize, apktool, sourcefolder, apkfile)
        #cmd = '"%s" -q b -f "%s" "%s"' % (apktool, sourcefolder, apkfile)
        ret = file_utils.execFormatCmd(cmd)

    return ret


def generateKeystore(workDir, game, channel):

    """
        auto generate keystore file
        if user want to use auto generated keystore file, you can use this method
    """
    keytoolPath = file_utils.getJavaBinDir()+"keytool"

    keystorePath = os.path.join(workDir, 'temp_keystore')
    if not os.path.exists(keystorePath):
        os.makedirs(keystorePath)

    keystore = dict()
    keystore['keystore'] =  os.path.join(keystorePath, "temp.keystore")
    keystore['password'] = channel['name']+game['appName']
    keystore['aliaskey'] = game["appName"]+channel["name"]+time.strftime('%Y%m%d%H%M%S')
    keystore['aliaspwd'] = channel['name']+game['appName']
    keystore['sigalg'] = "SHA1withRSA"

    dname = "CN=mqttserver.ibm.com, OU=ID, O=IBM, L=Hursley, S=Hants, C=GB"

    cmd = '"%s" -genkeypair -dname "%s" -alias "%s" -keyalg "RSA" -sigalg "%s" -validity 20000 -keystore "%s" -storepass "%s" -keypass "%s" ' % (keytoolPath, dname, keystore['aliaskey'],keystore['sigalg'], keystore['keystore'], keystore['password'], keystore['aliaspwd'])
    ret = file_utils.execFormatCmd(cmd)

    if ret:
        return None

    return keystore

#由于有些玩家存在作弊的情形，所以加了xsigncode的防作弊机制，需要在此进行签名操作，
#如果无需此操作，可以去core.py修改xsigncode方法为signApk即可
def xsigncode(workDir, game, channel, apkfile):

    xignClearcmd = '%sxapk_sign clean %s ' % (file_utils.getXignDir(),apkfile)

    cleanret = file_utils.execFormatCmd(xignClearcmd)

    log_utils.info("the cleanret file is %s", cleanret)

    # xigncmd = '%sxapk_sign %s ' % (file_utils.getXignDir(),apkfile)

    # xginret = file_utils.execFormatCmd(xigncmd)

    # log_utils.info("the xginret file is %s", xginret)

    xignCorecmd = '%sxapk_sign %s core' % (file_utils.getXignDir(),apkfile)

    coreret = file_utils.execFormatCmd(xignCorecmd)

    log_utils.info("the cleanret file is %s", coreret)


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
    aapt = file_utils.getFullToolPath(aapt_version)

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


def copyRootResFiles(apkfile, decompileDir):

    apkfile = file_utils.getFullPath(apkfile)
    aapt = file_utils.getFullToolPath(aapt_version)
    decompileDir = file_utils.getFullPath(decompileDir)

    igoreFiles = ['AndroidManifest.xml','apktool.yml','smali','res','original','lib','build','assets','unknown',"smali_classes2","smali_classes3","smali_classes4","smali_classes5"]
    igoreFileFullPaths = []

    for ifile in igoreFiles:
        fullpath = os.path.join(decompileDir, ifile)
        igoreFileFullPaths.append(fullpath)


    addFiles = []

    addFiles = file_utils.list_files(decompileDir, addFiles, igoreFileFullPaths)

    if len(addFiles) <= 0:
        return

    addCmd = '"%s" add "%s"'
    for f in addFiles:
        fname = f[(len(decompileDir)+1):]
        addCmd = addCmd + ' ' + fname

    addCmd = addCmd % (aapt, apkfile)

    currPath = os.getcwd()

    os.chdir(decompileDir)
    file_utils.execFormatCmd(addCmd)
    os.chdir(currPath)

def alignApk(apkfile, targetapkfile):

    """
        zip align the apk file
    """

    align = file_utils.getFullToolPath('zipalign')
    aligncmd = '"%s" -f 4 "%s" "%s"' % (align, apkfile, targetapkfile)

    ret = file_utils.execFormatCmd(aligncmd)

    return ret

def getPackageName(decompileDir):

    """
        Get The package attrib of application node in AndroidManifest.xml
    """

    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifestFile)
    root = tree.getroot()
    package = root.attrib.get('package')

    return package

def renamePackageName(channel, decompileDir, newPackageName, isPublic = True):

    """
        Rename package name to the new name configed in the channel
    """

    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifestFile)
    root = tree.getroot()
    package = root.attrib.get('package')

    oldPackageName = package
    tempPackageName = newPackageName

    """
    由于apk编译版本太高导致mainfest里边的有些配置识别不出来这两个值android:compileSdkVersion="28" android:compileSdkVersionCodename="9"
    所以需要删除才能正常打包这里加入删除代码
    """
    verKey = '{'+androidNS+'}compileSdkVersion'
    verNameKey = '{'+androidNS+'}compileSdkVersionCodename'

    if root.get(verKey) >=28:
        del root.attrib[verKey]
        del root.attrib[verNameKey]
    '''
    以上部分是删除代码!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    '''

    if not isPublic:
        newPackageName = oldPackageName + ".debug"

    if tempPackageName != None and len(tempPackageName) > 0:

        if tempPackageName[0:1] == '.':
            if not isPublic:
                newPackageName = oldPackageName + ".debug" + tempPackageName
            else:
                newPackageName = oldPackageName + tempPackageName
        else:
            newPackageName = tempPackageName

    if newPackageName == None or len(newPackageName) <= 0:
        newPackageName = oldPackageName

    log_utils.info("the new package name is %s", newPackageName)
    #now to check activity or service
    appNode = root.find('application')
    if appNode != None:

        #now to config icon if icon configed.
        # if 'icon' in channel and channel['icon'] != None:
        # 	iconKey = '{'+androidNS+'}icon'
        # 	iconVal = '@drawable/' + channel['icon']
        # 	appNode.set(iconKey, iconVal)

        activityLst = appNode.findall('activity')
        key = '{'+androidNS+'}name'
        if activityLst != None and len(activityLst) > 0:
            for aNode in activityLst:
                activityName = aNode.attrib[key]
                if activityName[0:1] == '.':
                    activityName = oldPackageName + activityName
                elif activityName.find('.') == -1:
                    activityName = oldPackageName + '.' + activityName
                aNode.attrib[key] = activityName

        serviceLst = appNode.findall('service')
        #key = '{'+androidNS+'}name'
        if serviceLst != None and len(serviceLst) > 0:
            for sNode in serviceLst:
                serviceName = sNode.attrib[key]
                if serviceName[0:1] == '.':
                    serviceName = oldPackageName + serviceName
                elif serviceName.find('.') == -1:
                    serviceName = oldPackageName + '.' + serviceName
                sNode.attrib[key] = serviceName

        receiverLst = appNode.findall('receiver')
        #key = '{'+androidNS+'}name'
        if receiverLst != None and len(receiverLst) > 0:
            for sNode in receiverLst:
                receiverName = sNode.attrib[key]
                if receiverName[0:1] == '.':
                    receiverName = oldPackageName + receiverName
                elif receiverName.find('.') == -1:
                    receiverName = oldPackageName + '.' + receiverName
                sNode.attrib[key] = receiverName

        providerLst = appNode.findall('provider')
        #key = '{'+androidNS+'}name'
        if providerLst != None and len(providerLst) > 0:
            for sNode in providerLst:
                providerName = sNode.attrib[key]
                if providerName[0:1] == '.':
                    providerName = oldPackageName + providerName
                elif providerName.find('.') == -1:
                    providerName = oldPackageName + '.' + providerName
                sNode.attrib[key] = providerName


    root.attrib['package'] = newPackageName
    tree.write(manifestFile, 'UTF-8')

    package = newPackageName
    return package


def copyResource(game, channel, packageName, sdkDir, decompileDir , operations, name, pluginInfo = None):

    """
        Copy sdk resources to the apk decompile dir
        Merge manifest.xml
        Merge all res xml if the xml already exists in target apk.
        copy all others resources
    """

    if operations != None:
        for child in operations:
            if child['type'] == 'mergeManifest':
                manifestFrom = file_utils.getFullPath(os.path.join(sdkDir, child['from']))
                manifestFromTemp = manifestFrom
                manifestTo = file_utils.getFullPath(os.path.join(decompileDir, child['to']))

                if 'orientation' in game:
                    if game['orientation'] == 'portrait':
                        manifestFrom = manifestFrom[:-4] + "_portrait.xml"
                    else:
                        manifestFrom = manifestFrom[:-4] + "_landscape.xml"

                    if not os.path.exists(manifestFrom):
                        manifestFrom = manifestFromTemp

                log_utils.info("The sdk manifest file is %s", manifestFrom)

                #merge into xml
                bRet = mergeManifest(channel, manifestTo, manifestFrom)
                if bRet:
                    log_utils.info("merge manifest file success.")
                else:
                    log_utils.error("merge manifest file failed.")
                    return 1

            elif child['type'] == 'copyRes':

                if child['from'] == None or child['to'] == None:
                    log_utils.error("the sdk config file error. 'copyRes' need 'from' and 'to'.sdk name:%s", name)
                    return 1

                copyFrom = file_utils.getFullPath(os.path.join(sdkDir, child['from']))
                copyTo = file_utils.getFullPath(os.path.join(decompileDir, child['to']))

                if child['to'] == 'lib':
                    copyLibs(game, copyFrom, copyTo)
                    log_utils.debug("copyFrom---->%s;copyTo----->%s;",copyFrom,copyTo)
                else:
                    copyResToApk(copyFrom, copyTo)
                    log_utils.debug("copyFrom---->%s;copyTo----->%s;",copyFrom,copyTo)

            elif child['type'] == 'script' and pluginInfo != None:
                #now only third-plugin support script
                if child['from'] == None:
                    log_utils.error("the sdk config file is error. 'script' need 'from' attrib to specify script.py")
                    return 1

                scriptName = child['from']
                log_utils.info("now to execute plugin script. name:%s", scriptName)
                doScript(channel, pluginInfo, decompileDir, packageName, sdkDir, scriptName)

    return 0

def copyChannelResources(game, channel, decompileDir):

    """
        Copy channel resources to decompile folder. for example icon resources, assets and so on.
    """
    resPath = "games/" + game['appName'] + "/channels/" + channel['id']
    resPath = file_utils.getFullPath(resPath)
    if not os.path.exists(resPath):
        log_utils.warning("the channel %s special res path is not exists. %s", channel['id'], resPath)
        return 0

    targetResPath = file_utils.getFullPath(decompileDir)

    assetsPath = os.path.join(resPath, 'assets')
    libsPath = os.path.join(resPath, 'libs')
    resourcePath = os.path.join(resPath, 'res')

    targetAssetsPath = os.path.join(decompileDir, 'assets')
    targetLibsPath = os.path.join(decompileDir, 'lib')
    targetResourcePath = os.path.join(decompileDir, 'res')


    copyResToApk(assetsPath, targetAssetsPath)
    copyResToApk(libsPath, targetLibsPath)
    copyResToApk(resourcePath, targetResourcePath)

    log_utils.info("copy channel %s special res to apk success.", channel['name'])

    return 0

def copyAppResources(game, decompileDir):
    """
        Copy game res files to apk.
    """
    resPath = "games/" + game['appName'] + "/res"
    resPath = file_utils.getFullPath(resPath)
    if not os.path.exists(resPath):
        log_utils.warning("the game %s has no extra res folder", game['appName'])
        return

    assetsPath = os.path.join(resPath, 'assets')
    libsPath = os.path.join(resPath, 'libs')
    resourcePath = os.path.join(resPath, 'res')

    targetAssetsPath = os.path.join(decompileDir, 'assets')
    targetLibsPath = os.path.join(decompileDir, 'lib')
    targetResourcePath = os.path.join(decompileDir, 'res')

    copyResToApk(assetsPath, targetAssetsPath)
    copyResToApk(libsPath, targetLibsPath)
    copyResToApk(resourcePath, targetResourcePath)


def copyAppRootResources(game, decompileDir):
    """
        Copy game root files to apk. the files will be in the root path of apk
    """
    resPath = "games/" + game['appName'] + "/root"
    resPath = file_utils.getFullPath(resPath)

    if not os.path.exists(resPath):
        log_utils.info("the game %s has no root folder", game['appName'])
        return

    targetResPath = file_utils.getFullPath(decompileDir)
    copyResToApk(resPath, targetResPath)

    return

#卢-->合并Manifest,aar到SDK
def mergeManifestAARToSDK(aarsDestDir, dstDir):

    """
        Merge aar AndroidManifest.xml to the sdk SdkManifest.xml
    """

    manifestFrom = file_utils.getFullPath(os.path.join(aarsDestDir, 'AndroidManifest.xml'))
    manifestTo = file_utils.getFullPath(os.path.join(dstDir, 'SDKManifest.xml'))

    if not os.path.exists(manifestTo) or not os.path.exists(manifestFrom):
        log_utils.error("the manifest file is not exists.manifestTo:%s;manifestFrom:%s", manifestTo, manifestFrom)
        return False

    ET.register_namespace('android', androidNS)
    targetTree = ET.parse(manifestTo)
    #获取xml根节点
    targetRoot = targetTree.getroot()

    ET.register_namespace('android', androidNS)
    aarTree = ET.parse(manifestFrom)
    aarRoot = aarTree.getroot()
    
    f = open(manifestTo)
    targetContent = f.read()
    f.close()


    permissionConfigNode = targetRoot.find('permissionConfig')
    for child in list(aarRoot):  
        # 子节点对应的values，uses-feature，uses-permission，permission
        key = '{' + androidNS + '}name'
        val = child.get(key)
        if val != None and len(val) > 0:
            attrIndex = targetContent.find(val)
            # values不存在添加
            if -1 == attrIndex:
                permissionConfigNode.append(child)

    aarAppNode = aarRoot.find('application')
    sdkAppConfigNode = targetRoot.find('applicationConfig')
       
    if aarAppNode != None:
        for aarChild in list(aarAppNode):     
            key = '{' + androidNS + '}name'
            val = aarChild.get(key)   
            if val != None and len(val) > 0:
                attrIndex = targetContent.find(val)
                if -1 == attrIndex:
                    sdkAppConfigNode.append(aarChild)
                               
    targetTree.write(manifestTo, 'UTF-8')

    return True

def mergeManifest(channel, targetManifest, sdkManifest):

    """
        Merge sdk SdkManifest.xml to the apk AndroidManifest.xml
    """

    if not os.path.exists(targetManifest) or not os.path.exists(sdkManifest):
        log_utils.error("the manifest file is not exists.targetManifest:%s;sdkManifest:%s", targetManifest, sdkManifest)
        return False

    ET.register_namespace('android', androidNS)
    targetTree = ET.parse(targetManifest)
    targetRoot = targetTree.getroot()

    ET.register_namespace('android', androidNS)
    sdkTree = ET.parse(sdkManifest)
    sdkRoot = sdkTree.getroot()

    f = open(targetManifest)
    targetContent = f.read()
    f.close()
    
     
    permissionConfigNode = sdkRoot.find('permissionConfig')
    if permissionConfigNode != None and len(permissionConfigNode) > 0:
        for child in list(permissionConfigNode):
            key = '{' + androidNS + '}name'
            val = child.get(key)
            if val != None and len(val) > 0:
                attrIndex = targetContent.find(val)
                if -1 == attrIndex:
                    targetRoot.append(child)

    appConfigNode = sdkRoot.find('applicationConfig')
    appNode = targetRoot.find('application')
    
    if appConfigNode != None:
        proxyApplicationName = appConfigNode.get('proxyApplication')
        if proxyApplicationName != None and len(proxyApplicationName) > 0:
            if 'U8_APPLICATION_PROXY_NAME' in channel:                
                channel['U8_APPLICATION_PROXY_NAME'] = channel['U8_APPLICATION_PROXY_NAME'] + ',' + proxyApplicationName
            else:               
                channel['U8_APPLICATION_PROXY_NAME'] = proxyApplicationName

        appKeyWord = appConfigNode.get('keyword')

        # exists = appKeyWord != None and len(appKeyWord.strip()) > 0 and targetContent.find(appKeyWord) != -1

        # if not exists:
        # remove keyword check...

        for child in list(appConfigNode): 
            appNode.append(child)
                     
    targetTree.write(targetManifest, 'UTF-8')

    return True

def copyResToApk(copyFrom, copyTo):

    """
        Copy two resource folders
    """

    if not os.path.exists(copyFrom):
        log_utils.error("the copyFrom %s is not exists.", copyFrom)
        return

    if not os.path.exists(copyTo):
        os.makedirs(copyTo)

    if os.path.isfile(copyFrom) and not mergeResXml(copyFrom, copyTo):
        file_utils.copy_file(copyFrom, copyTo)
        log_utils.debug("copyResToApk:copyFrom---->%s;copyTo----->%s;",copyFrom,copyTo)
        return
    
    #卢-->修改复制资源，并合并和删除重复资源
    for f in os.listdir(copyFrom):
        sourcefile = os.path.join(copyFrom, f)
        targetfile = os.path.join(copyTo, f)

        if(f == 'abc_action_menu_layout.xml' or f == 'abc_screen_toolbar.xml'):
            file_utils.del_file_folder(sourcefile)   
            continue

        if os.path.isfile(sourcefile):
            if not os.path.exists(copyTo):
                os.makedirs(copyTo)

            deleteSameRes(sourcefile, copyTo, 'attrs.xml')
            deleteSameRes(sourcefile, copyTo, 'colors.xml')
            deleteSameRes(sourcefile, copyTo, 'dimens.xml')
            deleteSameRes(sourcefile, copyTo, 'drawables.xml')
            deleteSameRes(sourcefile, copyTo, 'ids.xml')
            deleteSameRes(sourcefile, copyTo, 'integers.xml')
            deleteSameRes(sourcefile, copyTo, 'public.xml')
            deleteSameRes(sourcefile, copyTo, 'strings.xml')
            deleteSameRes(sourcefile, copyTo, 'styles.xml')

            if mergeResXml(sourcefile, targetfile):
                continue
            destfilestream = open(targetfile, 'wb')
            sourcefilestream = open(sourcefile, 'rb')
            destfilestream.write(sourcefilestream.read())
            destfilestream.close()
            sourcefilestream.close()

        if os.path.isdir(sourcefile):      
            copyResToApk(sourcefile, targetfile)


#卢-->修改资源合并逻辑
def mergeResXml(copyFrom, copyTo):

    """
        Merge all android res xml
    """

    if not os.path.exists(copyTo):
        return False

    fromName = os.path.basename(copyFrom)
    if not fromName.endswith('.xml'):
        return False

    if config_utils.is_py_env_2():
        f = open(copyTo)
    else:
        f = io.open(copyTo, 'r', encoding='utf-8')
    targetContent = f.read()
    f.close()

    fromTree = ET.parse(copyFrom)
    fromRoot = fromTree.getroot()
    toTree = ET.parse(copyTo)
    toRoot = toTree.getroot()                   

    for fromNode in list(fromRoot):
        val = fromNode.get('name')
        if val != None and len(val) > 0:
            #如果出现name和parent字段一样也会删除，加上name=
            #<style name="Theme.AppCompat.Light">
            #<style name="m4399ad.Dialog.NoTitleBar" parent="Theme.AppCompat.Light">
            valMatched = 'name="'+val+'"'
            attrIndex = targetContent.find(valMatched)
            if -1 == attrIndex:
                toRoot.append(fromNode)
            # else:
            #     log_utils.warning("The node %s is already exists in %s", val, copyTo)

    #删除valus.xml中的无法编译的字段
    for toNode in list(toRoot):
        for declareNode in list(toNode.iter('declare-styleable')):
            declareName = declareNode.get('name')
            if(declareName == 'ActionBar' or declareName == 'Toolbar' or declareName == 'ActionMode' 
                or declareName == 'Spinner' or declareName == 'LinearLayoutCompat' 
                or declareName == 'AlignTextView' or declareName == 'TextSeekBar'):
                toRoot.remove(declareNode)
                continue
   
    toTree.write(copyTo, 'UTF-8')
    return True

#卢-->删除来源SDK中values.xml（SDK，res/values/values.xml）和母包资源中（APK，res/values/attrs.xml）的重复值
def deleteSameRes(sourcefile, copyTo, filename):

    sourceName = os.path.basename(sourcefile)
    if not sourceName.endswith('.xml'):
        return 

    targetfile = os.path.join(copyTo, filename)
    if not os.path.exists(targetfile):
        return

    fromTree = ET.parse(sourcefile)
    fromRoot = fromTree.getroot()

    tf = open(targetfile)
    targetContent = tf.read()
    tf.close()
   
    if(filename == 'attrs.xml'):
        for child in list(fromRoot):
            for declareNode in list(child.iter('declare-styleable')):               
                for attrNode in list(declareNode.iter('attr')):
                    attrName = attrNode.get('name')
                    if attrName != None and len(attrName) > 0: 
                        attrMatched = '"'+attrName+'"'
                        attrIndex = targetContent.find(attrMatched)   
                        if -1 == attrIndex:
                            continue
                        else:
                            declareNode.remove(attrNode)                       

    else:      
        for child in list(fromRoot):
            #现在只有墨游海外需要for--continue这段代码，打包其他SDK，全选注销，Ctrl+/
            for itemNode in list(child.iter('item')):
                itemName = itemNode.get('name')
                if(itemName == 'buttonGravity' or itemName == 'subtitleTextStyle' or itemName == 'subtitleTextAppearance' 
                        or itemName == 'collapseIcon' or itemName == 'contentInsetStart' or itemName == 'contentInsetEnd' 
                        or itemName == 'contentInsetStartWithNavigation' or itemName == 'collapseContentDescription' 
                        or itemName == 'titleTextStyle' or itemName == 'titleMargin' or itemName == 'titleTextAppearance' 
                        or itemName == 'background' or itemName == 'backgroundSplit' or itemName == 'backgroundStacked' 
                        or itemName == 'displayOptions' or itemName == 'divider' or itemName == 'elevation' 
                        or itemName == 'popupTheme' or itemName == 'maxButtonHeight' or itemName == 'dividerPadding'
                        or itemName == 'showDividers' or itemName == 'closeItemLayout'):
                    child.remove(itemNode)
                    continue
            name = child.get('name')
            if name != None and len(name) > 0: 
                val = '"'+name+'"'
                index = targetContent.find(val)   
                if -1 == index:
                    continue
                else:
                    fromRoot.remove(child)               

    fromTree.write(sourcefile, 'UTF-8')

def copySplashToUnityResFolder(workDir, channel, decompileDir):

    splashPath = file_utils.getSplashPath()
    resPath = workDir + "/sdk/" + channel['sdk'] + "/splash/" + channel['splash'] + "/%s/u8_splash.png"
    resTargetPath = decompileDir + "/assets/bin/Data/splash.png"

    paths = ['drawable', 'drawable-hdpi', 'drawable-ldpi', 'drawable-mdpi', 'drawable-xhdpi']

    bFound = False
    for path in paths:
        imgPath = resPath % path
        if os.path.exists(imgPath):
            resPath = imgPath
            bFound = True
            break

    if not bFound:
        log_utils.error("the u8_splash is not found.path:%s", resPath)
        return 1

    if not os.path.exists(resTargetPath):
        log_utils.error("the unity splash is not exists. path:%s", resTargetPath)
        return 1

    file_utils.copy_file(resPath, resTargetPath)

    return 0


def addSplashScreen(workDir, channel, decompileDir):

    """
        if the splash attrib is not zero ,then set the splash activity
        if the splash_copy_to_unity attrib is set, then copy the splash img to unity res fold ,replace the default splash.png.

    """

    if channel['splash'] =='0':
        return 0

    if channel['splash_copy_to_unity'] == '1':
        return copySplashToUnityResFolder(workDir, channel, decompileDir)

    splashPath = file_utils.getSplashPath()
    smaliPath = splashPath + "/smali"
    smaliTargetPath = decompileDir + "/smali"

    copyResToApk(smaliPath, smaliTargetPath)

    splashLayoutPath = splashPath + "/u8_splash.xml"
    splashTargetPath = decompileDir + "/res/layout/u8_splash.xml"
    file_utils.copy_file(splashLayoutPath, splashTargetPath)

    resPath = workDir + "/sdk/" + channel['sdk'] + "/splash/" + channel['splash']
    resTargetPath = decompileDir + "/res"
    copyResToApk(resPath, resTargetPath)

    #remove original launcher activity of the game
    activityName = removeStartActivity(decompileDir)

    #append the launcher activity with the splash activity
    appendSplashActivity(decompileDir, channel['splash'])

    splashActivityPath = smaliTargetPath + "/com/u8/sdk/SplashActivity.smali"
    f = open(splashActivityPath, 'r+')
    content = str(f.read())
    f.close()

    replaceTxt = '{U8SDK_Game_Activity}'

    idx = content.find(replaceTxt)
    if idx == -1:
        log_utils.error("modify splash file failed.the {U8SDK_Game_Activity} not found in SplashActivity.smali")
        return 1

    content = content[:idx] + activityName + content[(idx + len(replaceTxt)):]
    f2 = open(splashActivityPath, 'w')
    f2.write(content)
    f2.close()

    log_utils.info("modify splash file success.")
    return 0


def removeStartActivity(decompileDir):
    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    key = '{' + androidNS + '}name'

    tree = ET.parse(manifestFile)
    root = tree.getroot()

    applicationNode = root.find('application')
    if applicationNode is None:
        return

    activityNodeLst = applicationNode.findall('activity')
    if activityNodeLst is None:
        return

    activityName = ''

    for activityNode in activityNodeLst:
        bMain = False
        intentNodeLst = activityNode.findall('intent-filter')
        if intentNodeLst is None:
            break

        for intentNode in intentNodeLst:
            bFindAction = False
            bFindCategory = False

            actionNodeLst = intentNode.findall('action')
            if actionNodeLst is None:
                break
            for actionNode in actionNodeLst:
                if actionNode.attrib[key] == 'android.intent.action.MAIN':
                    bFindAction = True
                    break

            categoryNodeLst = intentNode.findall('category')
            if categoryNodeLst is None:
                break
            for categoryNode in categoryNodeLst:
                if categoryNode.attrib[key] == 'android.intent.category.LAUNCHER':
                    bFindCategory = True
                    break

            if bFindAction and bFindCategory:
                bMain = True
                intentNode.remove(actionNode)
                intentNode.remove(categoryNode)
                break

        if bMain:
            activityName = activityNode.attrib[key]
            break

    tree.write(manifestFile, 'UTF-8')
    return activityName


def appendSplashActivity(decompileDir, splashType):
    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    key = '{' + androidNS + '}name'
    screenkey = '{' + androidNS + '}screenOrientation'
    theme = '{' + androidNS + '}theme'
    tree = ET.parse(manifestFile)
    root = tree.getroot()

    applicationNode = root.find('application')
    if applicationNode is None:
        return

    splashNode = SubElement(applicationNode, 'activity')
    splashNode.set(key, 'com.u8.sdk.SplashActivity')
    splashNode.set(theme, '@android:style/Theme.Black.NoTitleBar.Fullscreen')

    if splashType[:1] == '1':
        splashNode.set(screenkey, 'landscape')
    else:
        splashNode.set(screenkey, 'portrait')

    intentNode = SubElement(splashNode, 'intent-filter')
    actionNode = SubElement(intentNode, 'action')
    actionNode.set(key, 'android.intent.action.MAIN')
    categoryNode = SubElement(intentNode, 'category')
    categoryNode.set(key, 'android.intent.category.LAUNCHER')
    tree.write(manifestFile, 'UTF-8')

def handleThirdPlugins(workDir, decompileDir, game, channel, packageName):

    pluginsFolder = file_utils.getFullPath('config/plugin')
    gamePluginFolder = file_utils.getFullPath('games/'+game['appName']+'/plugin')
    plugins = channel.get('third-plugins')

    if plugins == None or len(plugins) <= 0:
        log_utils.info("the channel %s has no supported plugins.", channel['name'])
        return 0

    #copy all resources to temp folder.
    for plugin in plugins:
        pluginName = plugin['name']
        pluginSourceFolder = os.path.join(pluginsFolder, pluginName)
        if not os.path.exists(pluginSourceFolder):
            log_utils.warning("the plugin %s config folder is not exists", pluginName)
            continue

        pluginTargetFolder = workDir + "/plugins/" + pluginName
        file_utils.copy_files(pluginSourceFolder, pluginTargetFolder)

        gamePluginSourceFolder = os.path.join(gamePluginFolder, pluginName)
        if not os.path.exists(gamePluginSourceFolder):
            log_utils.warning("the plugin %s is not configed in the game %s", pluginName, game['appName'])
            continue

        file_utils.copy_files(gamePluginSourceFolder, pluginTargetFolder)

        if not os.path.exists(pluginSourceFolder + "/classes.dex"):
            jar2dex(pluginSourceFolder, pluginTargetFolder)


    #handle plugins
    smaliDir = os.path.join(decompileDir, "smali")
    pluginNum = 0
    for plugin in plugins:
        pluginName = plugin['name']
        pluginFolder = workDir + "/plugins/" + pluginName

        if not os.path.exists(pluginFolder):
            log_utils.warning("the plugin %s temp folder is not exists", pluginName)
            continue

        pluginDexFile = os.path.join(pluginFolder, "classes.dex")
        ret = dex2smali(pluginDexFile, smaliDir, "baksmali.jar")
        if ret:
            return 1

        ret = copyResource(game, channel, packageName, pluginFolder, decompileDir, plugin['operations'], pluginName, plugin)
        if ret:
            return 1

        pluginNum += 1

    log_utils.info("Total plugin num:%s;success handle num:%s", str(len(plugins)), str(pluginNum))


def generateNewRFile(newPackageName, decompileDir, channel):
    """
        Use all new resources to generate the new R.java, and compile it ,then copy it to the target smali dir
    """

    decompileDir = file_utils.getFullPath(decompileDir)
    tempPath = os.path.dirname(decompileDir)
    tempPath = tempPath + "/temp"
    log_utils.debug("generate R:the temp path is %s", tempPath)
    if os.path.exists(tempPath):
        file_utils.del_file_folder(tempPath)
    if not os.path.exists(tempPath):
        os.makedirs(tempPath)

    ret = checkValueResources(decompileDir)  
    if ret:
        return 1

    resPath = os.path.join(decompileDir, "res")
    targetResPath = os.path.join(tempPath, "res")
    file_utils.copy_files(resPath, targetResPath)

    genPath = os.path.join(tempPath, "gen")
    if not os.path.exists(genPath):
        os.makedirs(genPath)

    manifestPath = os.path.join(decompileDir, "AndroidManifest.xml")
    targetDexPath = os.path.join(tempPath, "classes.dex")

    ret = doGenerateR(decompileDir, targetResPath, manifestPath, genPath, targetDexPath, newPackageName)
    if ret:
        return 1

    return copyExtraR(decompileDir, channel, newPackageName)
       

def copyExtraR(decompileDir, channel, newPackageName):

    """
        copy the new generated R.java to sdk extra package

        first:add a new param in sdk channel config <param name="extraR" value="com.facebook" />

        for those sdk which used R.*.* directly in code.

    """

    if "extraR" not in channel:
        log_utils.debug("the sdk %s has no extraR config. don't need to generate extra R.java", channel['sdk'])
        return 0

    log_utils.debug("sdk %s need to generate extra R.java. package names:%s", channel['sdk'], channel['extraR'])        

    newPackageNames = channel['extraR'].split(",")

    decompileDir = file_utils.getFullPath(decompileDir)
    sdkPath = os.path.dirname(decompileDir) + "/sdk"
    resPath = os.path.join(sdkPath, channel['sdk']+"/res")

    tempPath = os.path.dirname(decompileDir)
    tempPath = tempPath + "/temp"
    genPath = os.path.join(tempPath, "gen")

    rPath = newPackageName.replace('.', '/')
    rPath = os.path.join(genPath, rPath)
    rPath = os.path.join(rPath, "R.java")

    if not os.path.exists(rPath):
        log_utils.error("copy extra R failed. the R.java is not exists:%s", rPath)
        return 1
   

    for k in range(len(newPackageNames)):

        packageName = newPackageNames[k]

        tempPath = os.path.join(sdkPath, 'extraTemp'+str(k))
        log_utils.debug("generate sdk R: the temp path is %s", tempPath)
        if os.path.exists(tempPath):
            file_utils.del_file_folder(tempPath)

        if not os.path.exists(tempPath):
            os.makedirs(tempPath)

        
        targetResPath = os.path.join(tempPath, "res")
        file_utils.copy_files(resPath, targetResPath)

        genPath = os.path.join(tempPath, "gen")
        if not os.path.exists(genPath):
            os.makedirs(genPath)


        trPath = packageName.replace('.', '/')
        trPath = os.path.join(genPath, trPath)
        if not os.path.exists(trPath):
            os.makedirs(trPath)

        targetRPath = os.path.join(trPath, "R.java")

        file_utils.copy_file(rPath, targetRPath)

        file_utils.modifyFileContent(targetRPath, newPackageName, packageName)

        cmd = '"%sjavac" -source 1.7 -target 1.7 -encoding UTF-8 "%s"' % (file_utils.getJavaBinDir(), targetRPath)
        ret = file_utils.execFormatCmd(cmd)
        if ret:
            return 1

        dexToolPath = file_utils.getFullToolPath("/lib/dx.jar")

        heapSize = config_utils.getJDKHeapSize()
        targetDexPath = os.path.join(tempPath, "classes.dex")
        cmd = file_utils.getJavaCMD() + ' -jar -Xmx%sm -Xms%sm "%s" --dex --output="%s" "%s"' % (heapSize, heapSize, dexToolPath, targetDexPath, genPath)

        ret = file_utils.execFormatCmd(cmd)
        if ret:
            return 1

        smaliPath = os.path.join(decompileDir, "smali")
        ret = dex2smali(targetDexPath, smaliPath, "baksmali.jar")

    return 0


def doGenerateR(decompileDir, resPath, manifestPath, genPath, targetDexPath, newPackageName):

    """
        generate R.java for the newPackageName
    """

    if not os.path.exists(resPath):
        log_utils.debug("%s not exists ", resPath)
        return 0

    aaptPath = file_utils.getFullToolPath(aapt_version)

    androidPath = file_utils.getFullToolPath("android.jar")
    cmd = '"%s" p -f -m -J "%s" -S "%s" -I "%s" -M "%s"' % (aaptPath, genPath, resPath, androidPath, manifestPath)
    ret = file_utils.execFormatCmd(cmd)
    if ret:
        return 1

    rPath = newPackageName.replace('.', '/')
    rPath = os.path.join(genPath, rPath)
    rPath = os.path.join(rPath, "R.java")

    cmd = '"%sjavac" -source 1.7 -target 1.7 -encoding UTF-8 "%s"' % (file_utils.getJavaBinDir(), rPath)
    ret = file_utils.execFormatCmd(cmd)
    if ret:
        return 1

    dexToolPath = file_utils.getFullToolPath("/lib/dx.jar")

    heapSize = config_utils.getJDKHeapSize()
    cmd = file_utils.getJavaCMD() + ' -jar -Xmx%sm -Xms%sm "%s" --dex --output="%s" "%s"' % (heapSize, heapSize, dexToolPath, targetDexPath, genPath)

    ret = file_utils.execFormatCmd(cmd)
    if ret:
        return 1

    smaliPath = os.path.join(decompileDir, "smali")
    ret = dex2smali(targetDexPath, smaliPath, "baksmali.jar")

    return ret


def writeDevelopInfo(game, channel, decompileDir):
    developConfigFile = os.path.join(decompileDir, "assets")
    if not os.path.exists(developConfigFile):
        os.makedirs(developConfigFile)

    developConfigFile = os.path.join(developConfigFile, "u8_developer_config.properties")
    config_utils.writeDeveloperProperties(game, channel, developConfigFile)


def writePluginInfo(channel, decompileDir):
    developConfigFile = os.path.join(decompileDir, "assets")
    if not os.path.exists(developConfigFile):
        os.makedirs(developConfigFile)

    developConfigFile = os.path.join(developConfigFile, "u8_plugin_config.xml")
    config_utils.writePluginConfigs(channel, developConfigFile)


def writeManifestMetaInfo(channel, decompileDir):
    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifestFile)
    root = tree.getroot()

    key = '{'+androidNS+'}name'
    val = '{'+androidNS+'}value'

    appNode = root.find('application')
    if appNode is None:
        return

    metaDataList = appNode.findall('meta-data')

    if metaDataList != None:
        for metaDataNode in metaDataList:
            keyName = metaDataNode.attrib[key]
            for child in channel['params']:
                if keyName == child['name'] and child['bWriteInManifest'] == '1':
                    log_utils.warning("the meta-data node %s repeated. remove it .", keyName)
                    appNode.remove(metaDataNode)

            if 'third-plugins' in channel and channel['third-plugins'] != None and len(channel['third-plugins']) > 0:

                for cPlugin in channel['third-plugins']:
                    if 'params' in cPlugin and cPlugin['params'] != None and len(cPlugin['params']) > 0:
                        for child in cPlugin['params']:
                            if keyName == child['name'] and child['bWriteInManifest'] == '1':
                                log_utils.warning("the meta-data node %s repeated. remove it .", keyName)
                                appNode.remove(metaDataNode)


    for child in channel['params']:
        if child['bWriteInManifest'] != None and child['bWriteInManifest'] == '1':
            metaNode = SubElement(appNode, 'meta-data')
            metaNode.set(key, child['name'])
            metaNode.set(val, child['value'])

    if 'third-plugins' in channel and channel['third-plugins'] != None and len(channel['third-plugins']) > 0:

        for cPlugin in channel['third-plugins']:
            if 'params' in cPlugin and cPlugin['params'] != None and len(cPlugin['params']) > 0:
                for child in cPlugin['params']:
                    if child['bWriteInManifest'] != None and child['bWriteInManifest'] == '1':
                        metaNode = SubElement(appNode, 'meta-data')
                        metaNode.set(key, child['name'])
                        metaNode.set(val, child['value'])

    if 'U8_APPLICATION_PROXY_NAME' in channel:
        metaNode = SubElement(appNode, 'meta-data')
        metaNode.set(key, "U8_APPLICATION_PROXY_NAME")
        metaNode.set(val, channel['U8_APPLICATION_PROXY_NAME'])        


    #log_utils.info(ET.tostring(root,encoding="us-ascii", method="text"))

    tree.write(manifestFile, 'UTF-8')

    log_utils.info("The manifestFile meta-data write successfully")


def doScript(channel, pluginInfo, decompileDir, packageName, sdkTempDir, scriptName):

    if scriptName != 'script.py':
        log_utils.error("the script file name must be script.py")
        return 1

    sdkScript = os.path.join(sdkTempDir, scriptName)

    if not os.path.exists(sdkScript):
        return 0

    sys.path.append(sdkTempDir)


    import script
    ret = script.execute(channel, pluginInfo, decompileDir, packageName)
    del sys.modules['script']
    sys.path.remove(sdkTempDir)

    return ret

def doSDKScript(channel, decompileDir, packageName, sdkTempDir):

    sdkScript = os.path.join(sdkTempDir, "sdk_script.py")

    if not os.path.exists(sdkScript):
        return 0

    sys.path.append(sdkTempDir)


    import sdk_script
    ret = sdk_script.execute(channel, decompileDir, packageName)
    del sys.modules['sdk_script']
    sys.path.remove(sdkTempDir)

    return ret

def doGamePostScript(game, channel, decompileDir, packageName):

    scriptDir = file_utils.getFullPath("games/"+game['appName']+"/scripts")

    if not os.path.exists(scriptDir):
        log_utils.info("the game post script is not exists. if you have some specail logic, you can do it in games/[yourgame]/scripts/post_script.py")
        return 0


    sdkScript = os.path.join(scriptDir, "post_script.py")

    if not os.path.exists(sdkScript):
        log_utils.info("the game post script is not exists. if you have some specail logic, you can do it in games/[yourgame]/scripts/post_script.py")
        return 0

    sys.path.append(scriptDir)

    import post_script

    log_utils.info("now to execute post_script.py of game %s ", game['appName'])
    ret = post_script.execute(game, channel, decompileDir, packageName)
    del sys.modules['post_script']
    sys.path.remove(scriptDir)

    return ret


def checkValueResources(decompileDir):
    
    resDir = os.path.join(decompileDir, "res")
    if not os.path.exists(resDir):
        return 0

    #check drawable resource
    ldpiPath = file_utils.getFullPath(resDir + '/drawable-ldpi')
    mdpiPath = file_utils.getFullPath(resDir + '/drawable-mdpi')
    hdpiPath = file_utils.getFullPath(resDir + '/drawable-hdpi')
    xhdpiPath = file_utils.getFullPath(resDir + '/drawable-xhdpi')
    xxhdpiPath = file_utils.getFullPath(resDir + '/drawable-xxhdpi')
    xxxhdpiPath = file_utils.getFullPath(resDir + '/drawable-xxxhdpi')

    removeDuplicateDrawableRes(ldpiPath+"-v4", ldpiPath)
    removeDuplicateDrawableRes(mdpiPath+"-v4", mdpiPath)
    removeDuplicateDrawableRes(hdpiPath+"-v4", hdpiPath)
    removeDuplicateDrawableRes(xhdpiPath+"-v4", xhdpiPath)
    removeDuplicateDrawableRes(xxhdpiPath+"-v4", xxhdpiPath)
    removeDuplicateDrawableRes(xxxhdpiPath+"-v4", xxxhdpiPath)

    return 0

def removeDuplicateDrawableRes(path1, path2):

    if not os.path.exists(path1) or not os.path.exists(path2):
        return

    duplicatedFiles = []

    for f1 in os.listdir(path1):
        for f2 in os.listdir(path2):
            if f1 == f2:
                # log_utils.warning("%s duplicated,need delete", os.path.join(path2, f2))
                duplicatedFiles.append(os.path.join(path2, f2))
                break

    for d in duplicatedFiles:
        file_utils.del_file_folder(d)


def isTargetResFile(resFile, tagName):

    """
        resFile contain tagName?
        use this to check the resFile whether or not strings.xml, colors.xml, dimens.xml...
    """

    if os.path.splitext(resFile)[1] != '.xml':
        return False

    if not os.path.exists(resFile):
        return False


    resTree = ET.parse(resFile)
    root = resTree.getroot()

    if root.tag != 'resources':
        return False

    for node in list(root):
        if node.tag == tagName:
            return True
        else:
            return False


def checkValueResourcesDeplecated(decompileDir):

    valXmls = ['values.xml', 'strings.xml', 'styles.xml', 'colors.xml','dimens.xml', 'ids.xml','attrs.xml','integers.xml','arrays.xml','bools.xml','drawables.xml','public.xml']

    resDir = decompileDir + '/res/values'
    existsStrs = {}
    stringsXml = resDir + '/strings.xml'
    if os.path.exists(stringsXml):
        stringTree = ET.parse(stringsXml)
        root = stringTree.getroot()
        for node in list(root):
            stringItem = {}
            name = node.attrib.get('name')
            val = node.text
            stringItem['file'] = stringsXml
            stringItem['name'] = name
            stringItem['value'] = val
            existsStrs[name] = stringItem

    existsColors = {}
    colorsXml = resDir + 'colors.xml'
    if os.path.exists(colorsXml):
        colorTree = ET.parse(colorsXml)
        root = colorTree.getroot()
        for node in list(root):
            colorItem = {}
            name = node.attrib.get('name')
            val = node.text.lower()
            colorItem['file'] = colorsXml
            colorItem['name'] = name
            colorItem['value'] = val
            existsColors[name] = colorItem


    valueFiles = {}
    for filename in os.listdir(resDir):
        if filename in valXmls:
            continue

        srcFile = os.path.join(resDir,filename)
        if os.path.splitext(srcFile)[1] != '.xml':
            continue
        tree = ET.parse(srcFile)
        root = tree.getroot()
        if root.tag != 'resources':
            continue

        for node in list(root):
            dictRes = None
            if node.tag == 'string':
                dictRes = existsStrs
            elif node.tag == 'color':
                dictRes = existsColors
            else:
                continue

            name = node.attrib.get('name')
            val = node.text

            if name is None:
                continue

            resItem = dictRes.get(name)
            if resItem is not None:
                resVal = resItem.get('value')
                log_utils.warning("node %s duplicated!!! the val is %s;the newVal is %s", name, val, resVal)
                root.remove(node)

            else:
                valItem = {}
                valItem['file'] = srcFile
                valItem['name'] = name
                valItem['value'] = val
                dictRes[name] = valItem

        valueFiles[srcFile] = tree

    for valFile in valueFiles.keys():
        valueFiles[valFile].write(valFile, 'UTF-8')


    #check drawable resource
    ldpiPath = file_utils.getFullPath(decompileDir + '/res/drawable-ldpi')
    mdpiPath = file_utils.getFullPath(decompileDir + '/res/drawable-mdpi')
    hdpiPath = file_utils.getFullPath(decompileDir + '/res/drawable-hdpi')
    xhdpiPath = file_utils.getFullPath(decompileDir + '/res/drawable-xhdpi')
    xxhdpiPath = file_utils.getFullPath(decompileDir + '/res/drawable-xxhdpi')
    xxxhdpiPath = file_utils.getFullPath(decompileDir + '/res/drawable-xxxhdpi')

    removeDuplicateDrawableRes(ldpiPath+"-v4", ldpiPath)
    removeDuplicateDrawableRes(mdpiPath+"-v4", mdpiPath)
    removeDuplicateDrawableRes(hdpiPath+"-v4", hdpiPath)
    removeDuplicateDrawableRes(xhdpiPath+"-v4", xhdpiPath)
    removeDuplicateDrawableRes(xxhdpiPath+"-v4", xxhdpiPath)
    removeDuplicateDrawableRes(xxxhdpiPath+"-v4", xxxhdpiPath)

    return 0


def getAppIconName(decompileDir):

    """
        从AndroidManifest.xml中获取游戏图标的名称
    """

    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifestFile)
    root = tree.getroot()
    
    applicationNode = root.find('application')
    if applicationNode is None:
        return "ic_launcher"

    key = '{'+androidNS+'}icon'
    iconName = applicationNode.get(key)

    if iconName is None:
        return "ic_launcher"

#    name = iconName[10:]

    name = iconName.split("@")[1].split("/")
	 
    return name


def appendChannelIconMark(game, channel, decompileDir):

    """
        自动给游戏图标加上渠道SDK的角标
        没有角标，生成没有角标的ICON
    """

    gameIconPath = 'games/' + game['appName'] + '/icon/icon.png'
    gameIconPath = file_utils.getFullPath(gameIconPath)
    if not os.path.exists(gameIconPath):
        log_utils.error("the game %s icon is not exists:%s",game['appName'], gameIconPath)
        return 1

    useMark = True

    if 'icon' not in channel:
        log_utils.warning("the channel %s of game %s do not config icon in config.xml,no icon mark.", channel['name'], game['appName'])

        useMark = False
        #这里直接返回，如果不设置icon配置，不再自动处理缩放图标。
        return 1
	log_utils.warning("the channel %s of game %s do not config icon in config.xml,no icon mark. so cant fuck game", channel['name'], game['appName'])

    rlImg = Image.open(gameIconPath)

    twoVal = getAppIconName(decompileDir)
    iconPath = twoVal[0]
    gameIconName = twoVal[1] + '.png'
	
    if useMark:
        #如果有角标，则添加角标
        markType = channel['icon']
        markName = 'right-bottom'
        if markType == 'rb':
            markName = 'right-bottom'
        elif markType == 'rt':
            markName = 'right-top'
        elif markType == 'lt':
            markName = 'left-top'
        elif markType == 'lb':
            markName = 'left-bottom'

        markPath = 'config/sdk/' + channel['sdk'] + '/icon_marks/' + markName + '.png'

        if not os.path.exists(markPath):
            log_utils.warning("the icon mark %s is not exists of sdk %s.no icon mark.", markPath, channel['name'])
        else:
            markIcon = Image.open(markPath)
            rlImg = image_utils.appendIconMark(rlImg, markIcon, (0, 0))
            if rlImg:
                log_utils.info("icon appendIconMark successfully")
            
    ldpiSize = (36, 36)
    mdpiSize = (48, 48)
    hdpiSize = (72, 72)
    xhdpiSize = (96, 96)
    xxhdpiSize = (144,144)
    xxxhdpiSize = (192, 192)

    xxxhdpiIcon = rlImg.resize(xxxhdpiSize, Image.ANTIALIAS)
    xxhdpiIcon = rlImg.resize(xxhdpiSize, Image.ANTIALIAS)    
    xhdpiIcon = rlImg.resize(xhdpiSize, Image.ANTIALIAS)   
    hdpiIcon = rlImg.resize(hdpiSize, Image.ANTIALIAS) 
    mdpiIcon = rlImg.resize(mdpiSize, Image.ANTIALIAS)        
    ldpiIcon = rlImg.resize(ldpiSize, Image.ANTIALIAS)

    ldpiPath = file_utils.getFullPath(decompileDir + '/res/'+iconPath+'-ldpi')
    mdpiPath = file_utils.getFullPath(decompileDir + '/res/'+iconPath+'-mdpi')
    hdpiPath = file_utils.getFullPath(decompileDir + '/res/'+iconPath+'-hdpi')
    xhdpiPath = file_utils.getFullPath(decompileDir + '/res/'+iconPath+'-xhdpi')
    xxhdpiPath = file_utils.getFullPath(decompileDir + '/res/'+iconPath+'-xxhdpi')
    xxxhdpiPath = file_utils.getFullPath(decompileDir + '/res/'+iconPath+'-xxxhdpi')

    # drawable-hdpi 或者 mipmap-hdpi 不存在就创建
    if not os.path.exists(ldpiPath):
        os.makedirs(ldpiPath)
    if not os.path.exists(mdpiPath):
        os.makedirs(mdpiPath)
    if not os.path.exists(hdpiPath):
        os.makedirs(hdpiPath)
    if not os.path.exists(xhdpiPath):
        os.makedirs(xhdpiPath)
    if not os.path.exists(xxhdpiPath):
        os.makedirs(xxhdpiPath)
    if not os.path.exists(xxxhdpiPath):
        os.makedirs(xxxhdpiPath)

    #如果drawable-hdpi-v4 或者 mipmap-hdpi-v4中存在icon图标先删除
    ldPngFile = ldpiPath+"-v4"+'/'+gameIconName
    if os.path.exists(ldPngFile):
        os.remove(ldPngFile)
    mdPngFile = mdpiPath+"-v4"+'/'+gameIconName
    if os.path.exists(mdPngFile):
        os.remove(mdPngFile)
    hdPngFile = hdpiPath+"-v4"+'/'+gameIconName
    if os.path.exists(hdPngFile):
        os.remove(hdPngFile)
    xhPngFile = xhdpiPath+"-v4"+'/'+gameIconName
    if os.path.exists(xhPngFile):
        os.remove(xhPngFile)
    xxhPngFile = xxhdpiPath+"-v4"+'/'+gameIconName
    if os.path.exists(xxhPngFile):
        os.remove(xxhPngFile)
    xxxhPngFile = xxxhdpiPath+"-v4"+'/'+gameIconName
    if os.path.exists(xxxhPngFile):
        os.remove(xxxhPngFile)

    #把生成后的带角标的icon保存在drawable-hdpi-v4 或者 mipmap-hdpi-v4中
    #ldpiIcon.save(os.path.join(ldpiPath, gameIconName), 'PNG')
    if os.path.exists(ldpiPath+"-v4"):
        ldpiIcon.save(os.path.join(ldpiPath+"-v4", gameIconName), 'PNG')
    #mdpiIcon.save(os.path.join(mdpiPath, gameIconName), 'PNG')
    if os.path.exists(mdpiPath+"-v4"):
        mdpiIcon.save(os.path.join(mdpiPath+"-v4", gameIconName), 'PNG')    
    #hdpiIcon.save(os.path.join(hdpiPath, gameIconName), 'PNG')
    if os.path.exists(hdpiPath+"-v4"):
        hdpiIcon.save(os.path.join(hdpiPath+"-v4", gameIconName), 'PNG')  
    #xhdpiIcon.save(os.path.join(xhdpiPath, gameIconName), 'PNG')
    if os.path.exists(xhdpiPath+"-v4"):
        xhdpiIcon.save(os.path.join(xhdpiPath+"-v4", gameIconName), 'PNG')  
    #xxhdpiIcon.save(os.path.join(xxhdpiPath, gameIconName), 'PNG')
    if os.path.exists(xxhdpiPath+"-v4"):
        xxhdpiIcon.save(os.path.join(xxhdpiPath+"-v4", gameIconName), 'PNG')  
    #xxxhdpiIcon.save(os.path.join(xxxhdpiPath, gameIconName), 'PNG')
    if os.path.exists(xxxhdpiPath+"-v4"):
        xxxhdpiIcon.save(os.path.join(xxxhdpiPath+"-v4", gameIconName), 'PNG')  
    log_utils.info("icon save successfully")

    return 0


def checkCpuSupport(game, decompileDir):
    print("now to check cpu support...")

    isfilter = ("cpuSupport" in game) and len(game["cpuSupport"]) > 0

    filters = None
    if isfilter:
        filters = game["cpuSupport"].split('|')
        print(filters)

        for f in os.listdir(os.path.join(decompileDir, 'lib')):
            if f not in filters:
                file_utils.del_file_folder(os.path.join(decompileDir, 'lib/'+f))
  

    #make sure so in armeabi and armeabi-v7a is same
    armeabiPath = os.path.join(decompileDir, 'lib/armeabi')                  
    armeabiv7aPath = os.path.join(decompileDir, 'lib/armeabi-v7a')    

    if os.path.exists(armeabiPath) and os.path.exists(armeabiv7aPath):

        for f in os.listdir(armeabiPath):
            fv7 = os.path.join(armeabiv7aPath, f)
            if not os.path.exists(fv7):
                shutil.copy2(os.path.join(armeabiPath, f), fv7)

        for fv7 in os.listdir(armeabiv7aPath):
            f = os.path.join(armeabiPath, fv7)
            if not os.path.exists(f):
                shutil.copy2(os.path.join(armeabiv7aPath, fv7), f)


def modifyGameName(channel, decompileDir):

    """
        修改当前渠道的游戏名称,如果某个渠道的游戏名称特殊，可以配置gameName来指定。默认就是母包中游戏的名称
    """

    log_utils.info("now to modify game name ....")
    if 'gameName' not in channel:
        log_utils.info("now no game name modify")
        return

    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifestFile)
    root = tree.getroot()   

    labelKey = '{'+androidNS+'}label'
    applicationNode = root.find('application')
    applicationNode.set(labelKey, channel['gameName'])

    log_utils.info("the new game name is " + channel['gameName'])
    tree.write(manifestFile, 'UTF-8')


def checkApkForU8SDK(workDir, decompileDir):
    """
        检查母包中接入U8SDK抽象层是否正确
        不正确，则自动修正
    """
    ret = 0
    log_utils.info("now to check the u8.apk is correct?")

    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifestFile)
    root = tree.getroot()   

    key = '{'+androidNS+'}name'
    applicationNode = root.find('application')

    name = applicationNode.get(key)
    if not name or name != "com.u8.sdk.U8Application":
        log_utils.error("the android:name in application element must be 'com.u8.sdk.U8Application'. now change it to com.u8.sdk.U8Application, but maybe something will be wrong .")
        applicationNode.set(key, 'com.u8.sdk.U8Application')
        tree.write(manifestFile, 'UTF-8')

    
    smaliName = file_utils.getFullPath(decompileDir + "/smali/com/u8/sdk/U8SDK.smali")
    if not os.path.exists(smaliName):
        log_utils.error("the u8sdk2.jar is not packaged to the u8.apk. now merge it. but maybe something will be wrong .")

        u8sdkJarPath = file_utils.getFullPath('config/local/u8sdk2.jar')
        if not os.path.exists(u8sdkJarPath):
            log_utils.error("the u8sdk2.jar is not in config/local path. check failed")
            return 1

        targetPath = file_utils.getFullPath(workDir + "/local")
        if not os.path.exists(targetPath):
            os.makedirs(targetPath)

        file_utils.copy_file(u8sdkJarPath, targetPath+"/u8sdk2.jar")

        jar2dex(targetPath, targetPath)

        smaliPath = file_utils.getFullPath(decompileDir + "/smali")
        ret = dex2smali(targetPath + '/classes.dex', smaliPath)

    log_utils.info("check u8.apk successfully")

    return ret


def splitDex(workDir, decompileDir):
    """
        如果函数上限超过限制，自动拆分smali，以便生成多个dex文件
    """

    log_utils.info("now to check split dex ... ")
    
    smaliPath = decompileDir + "/smali"

    multidexFilePath = file_utils.getFullPath(smaliPath + "/android/support/multidex/MultiDex.smali")
    if not os.path.exists(multidexFilePath):
        #android-support-multidex.jar不存在，从local下面拷贝，并编译
        dexJar = file_utils.getFullPath('config/local/android-support-multidex.jar')
        if not os.path.exists(dexJar):
            log_utils.error("the method num expired of dex, but no android-support-multidex.jar in u8.apk or in local folder")
            return

        targetPath = file_utils.getFullPath(workDir + "/local")
        if not os.path.exists(targetPath):
            os.makedirs(targetPath) 

        file_utils.copy_file(dexJar, targetPath+"/android-support-multidex.jar")  

        jar2dex(targetPath, targetPath)
        smaliPath = file_utils.getFullPath(decompileDir + "/smali")
        ret = dex2smali(targetPath + '/classes.dex', smaliPath)        
    
    allFiles = []
    allFiles = file_utils.list_files(decompileDir, allFiles, [])    

    maxFuncNum = 65535
    currFucNum = 0
    totalFucNum = 0

    currDexIndex = 1

    allRefs = []

    #保证U8SDK等类在第一个classex.dex文件中
    for f in allFiles:
        f = f.replace("\\", "/")
        if "/com/u8/sdk" in f or "/android/support/multidex" in f:
            currFucNum = currFucNum + smali_utils.get_smali_method_count(f, allRefs)

    totalFucNum = currFucNum
    for f in allFiles:

        f = f.replace("\\", "/")
        if not f.endswith(".smali"):
            continue

        if "/com/u8/sdk" in f or "/android/support/multidex" in f:
            continue

        thisFucNum = smali_utils.get_smali_method_count(f, allRefs)
        totalFucNum = totalFucNum + thisFucNum
        if currFucNum + thisFucNum >= maxFuncNum:
            currFucNum = thisFucNum
            currDexIndex = currDexIndex + 1
            newDexPath = os.path.join(decompileDir, "smali_classes"+str(currDexIndex))
            os.makedirs(newDexPath)           
            
        else:
            currFucNum = currFucNum + thisFucNum

        if currDexIndex > 1:        
            targetPath = f[0:len(decompileDir)] + "/smali_classes"+str(currDexIndex) + f[len(smaliPath):]
            file_utils.copy_file(f, targetPath)
            file_utils.del_file_folder(f)

       
    log_utils.info("the total func num:"+str(totalFucNum))
    log_utils.info("split dex success. the classes.dex num:"+str(currDexIndex))


def writeLogConfig(game, decompileDir):
    """
        将日志参数写入到meta-data中
    """

    if 'log' not in game:
        log_utils.warning("the log config is not in games.xml of game: %s" ,game['appName'])
        return

    manifestFile = decompileDir + "/AndroidManifest.xml"
    manifestFile = file_utils.getFullPath(manifestFile)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifestFile)
    root = tree.getroot()   

    key = '{'+androidNS+'}name'
    val = '{'+androidNS+'}value'
    appNode = root.find('application')

    metaDataList = appNode.findall('meta-data')

    if metaDataList and len(metaDataList) > 0:

        for metaDataNode in metaDataList:
            keyName = metaDataNode.attrib[key]
            for lKey in game['log']:
                if keyName == lKey:
                    log_utils.warning("the meta-data node %s repeated. remove it .", keyName)
                    appNode.remove(metaDataNode)

    log_utils.info("-----------log config--------------")

    for lKey in game['log']:
        metaNode = SubElement(appNode, 'meta-data')
        metaNode.set(key, lKey)
        metaNode.set(val, game['log'][lKey])  
        log_utils.info("%s = %s", lKey, game['log'][lKey])       

    tree.write(manifestFile, 'UTF-8')

    log_utils.info("-----------log config--------------\n")


def getCompressRegx(game):

    """
        如果游戏有部分文件或者后缀名文件，在apktool重新打包的时候，没有被压缩，
        可以配置在打包工具/games/当前游戏/compress.txt文件中，加上需要压缩的文件或者文件后缀

    """

    result = list()
    compressFilePath = file_utils.getFullPath("games/"+game['appName']+"/compress.txt")
    if not os.path.exists(compressFilePath):
        log_utils.debug("no need handle special compress. the compress.txt file is not exists:%s", compressFilePath)
        return result

    f = open(compressFilePath, 'r')
    lines = f.readlines()
    f.close()

    for line in lines:
        if line.startswith("."):
            result.append(line[1:].strip())
        else:
            result.append(line.strip())

    return result


def modifyYml(game, packageName, decompileDir):
    """
        修改apktool.yml 文件中的versionName,versionCode,minSdkVersion,targetSdkVersion
    """
    ymlPath = file_utils.getFullPath(decompileDir+"/apktool.yml")
    if not os.path.exists(ymlPath):
        log_utils.warning("the apktool.yml is not exists in "+decompileDir)
        return

    versionCode = None
    versionName = None
    if 'versionCode' in game:
        versionCode = game['versionCode']

    if 'versionName' in game:
        versionName = game['versionName']

    minSdkVersion = None
    targetSdkVersion = None
    maxSdkVersion = None

    if 'minSdkVersion' in game:
        minSdkVersion = game['minSdkVersion']

    if 'targetSdkVersion' in game:
        targetSdkVersion = game['targetSdkVersion']

    if 'maxSdkVersion' in game:
        maxSdkVersion = game['maxSdkVersion']

#    isSDKConfiged = (minSdkVersion is not None) and (targetSdkVersion is not None) and (maxSdkVersion is not None)
    isSDKConfiged = (minSdkVersion is not None) and (targetSdkVersion is not None)

    log_utils.info("the minSdkVersion targetSdkVersion maxSdkVersion must configed all or configed zero")

    ymlFile = open(ymlPath, 'r')
    lines = ymlFile.readlines()
    ymlFile.close()

    handlingCompress = False
    compressRegx = getCompressRegx(game)

    newLines = []
    for line in lines:
        if 'versionCode' in line and versionCode is not None:
            newLines.append("  versionCode: '" + versionCode + "'\n")
            handlingCompress = False
        elif 'versionName' in line and versionName is not None:
            newLines.append("  versionName: " + versionName + "\n")
            handlingCompress = False
        elif 'sdkInfo' in line and isSDKConfiged:
            handlingCompress = False
            continue
        elif 'minSdkVersion' in line and isSDKConfiged:
            handlingCompress = False
            continue
        elif 'targetSdkVersion' in line and isSDKConfiged:
            handlingCompress = False
            continue
#        elif 'maxSdkVersion' in line and isSDKConfiged:
#            handlingCompress = False
#            continue
        elif 'renameManifestPackage' in line and ('null' not in line):
            newLines.append("  renameManifestPackage: " + packageName + "\n")
            handlingCompress = False
        elif 'doNotCompress:' in line:
            handlingCompress = True
            newLines.append(line)
        elif handlingCompress and line.startswith('-'):
            currLine = line[1:].strip()
            matchs = [c for c in compressRegx if c == currLine]
            if len(matchs) <= 0:
                newLines.append(line)

        else:
            handlingCompress = False
            newLines.append(line)

    if isSDKConfiged:
        newLines.append('sdkInfo:\n')
        newLines.append("  minSdkVersion: '"+minSdkVersion + "'\n")
        newLines.append("  targetSdkVersion: '"+targetSdkVersion + "'\n")
#        newLines.append("  maxSdkVersion: '"+maxSdkVersion + "'\n")

    content = ''
    for line in newLines:
        content = content + line

    ymlFile = open(ymlPath, 'w')
    ymlFile.write(content)
    ymlFile.close()


def getOutputApkName(game, channel, packageName, decompileDir):
    """
        获取输出的最终apk包名
    """

    channelName = channel['name']
    channelName = channelName.replace(' ', '')
    if "outputApkName" not in game:
        apkName = channelName + '-' + time.strftime('%Y%m%d%H')
        if 'signApk' in channel and channel['signApk'] == '0':  
            apkName = apkName + '_unsigned'

        return apkName + '.apk'

    formatStr = game['outputApkName']
    log_utils.debug("the output apk format string is " + formatStr)

    formatStr = formatStr.replace('{bundleID}', packageName)
    formatStr = formatStr.replace('{time}', time.strftime('%Y%m%d%H%M%S'))
    formatStr = formatStr.replace('{channelID}', channel['id'])
    formatStr = formatStr.replace('{channelName}', channelName)
    formatStr = formatStr.replace('{appName}', game['appName'])
    formatStr = formatStr.replace('{appID}', game['appID'])

    versionCode = getVersionCode(game, decompileDir)
    versionName = getVersionName(game, decompileDir)
    log_utils.debug("the versionCode is "+versionCode +";versionName is "+versionName)

    formatStr = formatStr.replace('{versionCode}', versionCode)
    formatStr = formatStr.replace('{versionName}', versionName)

    apkName = formatStr
    if 'signApk' in channel and channel['signApk'] == '0':
        fname , fext = os.path.splitext(formatStr)
        apkName = fname + '_unsigned' + fext

    return apkName


def getVersionCode(game, decompileDir):
    """
        获取AndroidManifest.xml中设置的versionCode
    """

    if "versionCode" in game:

        return game['versionCode']

    ymlPath = file_utils.getFullPath(decompileDir+"/apktool.yml")
    if not os.path.exists(ymlPath):
        log_utils.warning("the apktool.yml is not exists in "+decompileDir)
        return "0"

    ymlFile = open(ymlPath, 'r')
    lines = ymlFile.readlines()
    ymlFile.close()

    for line in lines:
        if 'versionCode' in line:
            #versionCode: '15'
            return line.replace('versionCode:', '').strip().replace("'", "")

    return "0"

def getVersionName(game, decompileDir):
    """
        获取AndroidManifest.xml中设置的versionName
    """

    if "versionName" in game:

        return game['versionName']

    ymlPath = file_utils.getFullPath(decompileDir+"/apktool.yml")
    if not os.path.exists(ymlPath):
        log_utils.warning("the apktool.yml is not exists in "+decompileDir)
        return "0"

    ymlFile = open(ymlPath, 'r')
    lines = ymlFile.readlines()
    ymlFile.close()

    for line in lines:
        if 'versionName' in line:
            #versionCode: '15'
            return line.replace('versionName:', '').strip().replace("'", "")

    return "0"


















