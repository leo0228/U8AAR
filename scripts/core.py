# -*- coding: utf-8 -*-
#Author:xiaohei
#CreateTime:2014-10-25
#
# The main operation entry
#
# 1、decomplie apk to smali use apktool.jar
# 2、rename the apk package name to new name configed in channel
# 3、copy all sdk resources of the channel to the target decompile dir
#    3.1、copy all none xml files to the target dir
#	 3.2、merge the sdk AndroidManifest.xml to the target apk AndroidManifest.xml
#	 3.3、merge all the sdk res xml like strings.xml, drawables.xml,styles.xml...
# 4、copy all code and resources of supported third-plugins
# 5、generate plugin info and develop info in assets folder,and write meta-data to AndroidManifest.xml
# 6、regenerate the R file
# 7、recompile the apk file
# 8、sign the apk file
# 9、zip allign the apk file

import sys
import file_utils
import apk_utils
import config_utils
import log_utils
import os
import os.path
import time


def pack(game, channel, sourcepath, isPublic):

    sourcepath = sourcepath.replace('\\', '/')
    if not os.path.exists(sourcepath):
        return 1

    appID = game['appID']
    appKey = game['appKey']
    appName = game['appName']

    channelId = channel["id"]
    channelName = channel["name"]
    sdkName = channel["sdk"]

    log_utils.info("now to package %s...", channelName)

    workDir = 'workspace/' + appName + '/' + channelName
    workDir = file_utils.getFullPath(workDir)

    file_utils.del_file_folder(workDir)
    tempApkSource = workDir + "/temp.apk"
    file_utils.copy_file(sourcepath, tempApkSource)
    decompileDir = workDir + "/decompile"
    smaliDir = decompileDir + "/smali"

    #反编译APK
    ret = apk_utils.decompileApk(tempApkSource, decompileDir)
    if ret:
        return 1

    #检查母包接入是否正确
    ret = apk_utils.checkApkForU8SDK(workDir, decompileDir)
    if ret:
        return 1

    #change xml config and so on
    newPackageName = apk_utils.renamePackageName(channel, decompileDir, channel['suffix'], isPublic)

    #copy third-plugins resources. note:The third plugins must be operated before the main sdk.
    ret = apk_utils.handleThirdPlugins(workDir, decompileDir, game, channel, newPackageName)
    if ret:
        return 1

    #copy sdk code to decompileDir
    sdkSourceDir = 'config/sdk/' + sdkName
    sdkSourceDir = file_utils.getFullPath(sdkSourceDir)
    sdkDestDir = workDir + "/sdk/" + sdkName
    file_utils.copy_files(sdkSourceDir, sdkDestDir)

    #将公共库复制到临时目录，除了moyoihw渠道
    if sdkName != 'moyoihw':
        promptDir = 'config/local/common-release.aar'
        promptDestDir = sdkDestDir + '/libs/common-release.aar';
        file_utils.copy_files(promptDir, promptDestDir)

    
    #处理需要Gradle自动下载的库
    if 'dependencies' in channel and channel['dependencies'] != None and len(channel['dependencies']) > 0:      
        #将build.gradle复制到临时目录
        localSourceDir = 'config/local/build.gradle'
        file_utils.copy_files(localSourceDir, sdkDestDir + '/build.gradle')

        #修改build.gradle
        config_utils.writeGradleDependencies(channel['dependencies'], sdkDestDir)
        
    #将SDK中所有aar文件解压，然后将里面各个类型的资源文件合并到SDK对应目录
    file_utils.decomAAR(sdkDestDir)

    ret = apk_utils.jar2dex(sdkDestDir, sdkDestDir)
    if ret:
        return 1

    ret = apk_utils.dexes2smali(sdkDestDir, smaliDir, "baksmali.jar")
    if ret:
        return 1

    #copy main sdk resources.
    ret = apk_utils.copyResource(game, channel, newPackageName, sdkDestDir, decompileDir, channel['operations'], channelName)
    if ret:
        return 1

    #auto handle icon
    apk_utils.appendChannelIconMark(game, channel, decompileDir)

    #copy channel special resources
    ret = apk_utils.copyChannelResources(game, channel, decompileDir)
    if ret:
        return 1

    #copy game root resources and res resources
    apk_utils.copyAppResources(game, decompileDir)
    apk_utils.copyAppRootResources(game, decompileDir)
    

    #generate config files for apk to run.
    apk_utils.writeDevelopInfo(game, channel, decompileDir)
    apk_utils.writePluginInfo(channel, decompileDir)
    apk_utils.writeManifestMetaInfo(channel, decompileDir)
    apk_utils.writeLogConfig(game, decompileDir)

    #if the main sdk has special logic. execute the special logic script.
    ret = apk_utils.doSDKScript(channel, decompileDir, newPackageName, sdkDestDir)
    if ret:
        return 1

    #if the game has some special logic. execute the special logic script.called post_script.py
    ret = apk_utils.doGamePostScript(game, channel, decompileDir, newPackageName)
    if ret:
        return 1

    #here to config the splash screen.
    ret = apk_utils.addSplashScreen(workDir, channel, decompileDir)
    if ret:
        return 1

    #check cpu supports
    apk_utils.checkCpuSupport(game, decompileDir)

    #modify game name if channel specified.
    apk_utils.modifyGameName(channel, decompileDir)

    #modify yml
    apk_utils.modifyYml(game, newPackageName, decompileDir)

    #generate new R.java
    ret = apk_utils.generateNewRFile(newPackageName, decompileDir, channel)
    if ret:
        return 1

    #check to split dex
    apk_utils.splitDex(workDir, decompileDir)

    targetApk = workDir + "/output.apk"
    log_utils.debug("now to recompileApk....")
    ret = apk_utils.recompileApk(decompileDir, targetApk)
    if ret:
        return 1

    apk_utils.copyRootResFiles(targetApk, decompileDir)

    if 'signApk' not in channel or channel['signApk'] != '0':
        apk_utils.xsigncode(workDir, game, channel, targetApk)
  
        apk_utils.signApk(workDir, game, channel, targetApk)
    else:
        log_utils.debug("the apk is set to unsigned.")
    
    channelNameStr = channelName.replace(' ', '')

    if isPublic:
        destApkName = apk_utils.getOutputApkName(game, channel, newPackageName, decompileDir)
    else:
        destApkName = channelNameStr + '-' + time.strftime('%Y%m%d%H') + '-debug.apk'

    destApkPath = file_utils.getFullOutputPath(appName, channelName)
    destApkPath = os.path.join(destApkPath, destApkName)
    ret = apk_utils.alignApk(targetApk, destApkPath)
    if ret:
        return 1

    log_utils.info("channel %s package success.", channelName)
    return 0