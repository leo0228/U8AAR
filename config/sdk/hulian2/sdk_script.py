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

androidNS = 'http://schemas.android.com/apk/res/android'

def execute(channel, decompileDir, packageName):

	modifyManifest(channel, decompileDir, packageName)

	return 0

def modifyManifest(channel, decompileDir, packageName):
	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{' + androidNS + '}name'
	authorityKey = '{'+androidNS+'}authorities'
	metaValue = '{'+androidNS+'}value'
	
	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return

	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1

	receiverNodeLst = applicationNode.findall('receiver')
	if receiverNodeLst is None:
		return 1

	appid = ""
	cpid = ""

	if 'params' in channel:
		params = channel['params']
		for param in params:
			if param['name'] == 'com.huawei.hms.client.appid':
				appid = param['value']
			elif param['name'] == 'com.huawei.hms.client.cpid':
				cpid = param['value']
				break
				
	metaNodeLst = applicationNode.findall('meta-data')
	if metaNodeLst is None:
		return 1
		
	for metaNode in metaNodeLst:
		name = metaNode.get(key)
		if name == 'com.huawei.hms.client.appid':
			metaNode.set(metaValue, "appid="+appid)
			
		if name == 'com.huawei.hms.client.cpid':
			metaNode.set(metaValue, "cpid="+cpid)
			break
		
	activityName = ''
	
	for providerNode in providerNodeLst:

		name = providerNode.get(key)
		if name == 'com.huawei.hms.update.provider.UpdateProvider':
			providerNode.set(authorityKey, packageName+".hms.update.provider")
			
		if name == 'com.huawei.updatesdk.fileprovider.UpdateSdkFileProvider':
			providerNode.set(authorityKey, packageName+".updateSdk.fileProvider")
			
	for receiverNode in receiverNodeLst:
		intentNodes = receiverNode.findall('intent-filter')
		if intentNodes is not None and len(intentNodes) > 0:
			for intentNode in intentNodes:
				actionNodes = intentNode.findall('action')
				if actionNodes is not None and len(actionNodes) > 0:
					for actionNode in actionNodes:
						actionName = actionNode.get(key)
						if actionName == 'com.huawei.android.push.intent.REGISTRATION':
							receiverNode.set(key, 'com.u8.sdk.HuaweiPushRevicer')
							break
	tree.write(manifestFile, 'UTF-8')

	return activityName

