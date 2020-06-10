import file_utils
import os
import os.path
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

androidNS = 'http://schemas.android.com/apk/res/android'

def execute(channel, decompileDir, packageName):
	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{' + androidNS + '}name'
	authorityKey = '{'+androidNS+'}authorities'
	
	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	proNodeLst = applicationNode.findall('provider')
	if proNodeLst is None:
		return 1
	
	for proNode in proNodeLst:
		name = proNode.get(key)
		if name == 'android.support.v4.content.FileProvider':
			proNode.set(authorityKey, packageName+'.provider')
		if name == 'com.smwl.smsdk.X7Provider':
			proNode.set(authorityKey, packageName+'.x7provider')
		if name == 'com.netease.nimlib.ipc.NIMContentProvider':
			proNode.set(authorityKey, packageName+'.ipc.provider')
		if name == 'com.netease.nim.uikit.common.media.picker.model.GenericFileProvider':
			proNode.set(authorityKey, packageName+'.generic.file.provider')	
	
	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return 1

	for activityNode in activityNodeLst:
		name = activityNode.get(key)
		if name == 'com.smwl.smsdk.activity.im.YunXinToX7ActX7SDK':
			intentNodes = activityNode.findall('intent-filter')
			for intentNode in intentNodes:
				actionNodes = intentNode.findall('action')
				for actionNode in actionNodes:
					actionName = actionNode.get(key)
					if actionName == 'gamePackageName.yunXin_jumpTo_YunXinToX7Act':
						intentNode.remove(actionNode)
						actionNode = SubElement(intentNode, 'action')
						actionNode.set(key, packageName+'.yunXin_jumpTo_YunXinToX7Act')

	tree.write(manifestFile, 'UTF-8')

	return 0

