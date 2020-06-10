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

	perNode = SubElement(applicationNode, 'uses-permission')
	perNode.set(key, packageName+'.permission.PROCESS_PUSH_MSG')
	
	perNode = SubElement(applicationNode, 'permission')
	perNode.set(key, packageName+'.permission.PROCESS_PUSH_MSG')
	perNode.set('{' + androidNS + '}protectionLevel', 'signatureOrSystem')
	
	appid = ""
	cpid = ""

	if 'params' in channel:
		params = channel['params']
		for param in params:
			if param['name'] == 'com.huawei.hms.client.appid':
				appid = param['value']
			elif param['name'] == 'com.huawei.hms.client.cpid':
				cpid = param['value']

	metaNodeLst = applicationNode.findall('meta-data')
	if metaNodeLst is None:
		return 1
		
	for metaNode in metaNodeLst:
		name = metaNode.get(key)
		if name == 'com.huawei.hms.client.appid':
			metaNode.set(metaValue, "appid="+appid)
			
		if name == 'com.huawei.hms.client.cpid':
			metaNode.set(metaValue, "cpid="+cpid)
	
	
	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1

	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'com.huawei.hms.update.provider.UpdateProvider':
			providerNode.set(authorityKey, packageName+".hms.update.provider")
			
		if name == 'com.huawei.updatesdk.fileprovider.UpdateSdkFileProvider':
			providerNode.set(authorityKey, packageName+".updateSdk.fileProvider")
			break
			
	receiverNodeLst = applicationNode.findall('receiver')
	if receiverNodeLst is None:
		return 1

	for receiverNode in receiverNodeLst:
		name = receiverNode.get(key)
		if name == 'HuaweiPushRevicer1':
			receiverNode.set(key, 'com.u8.sdk.HuaweiPushRevicer')
		elif name == 'HuaweiPushRevicer2':
			receiverNode.set(key, 'com.u8.sdk.HuaweiPushRevicer')
			receiverNode.set('{' + androidNS + '}permission', packageName+'.permission.PROCESS_PUSH_MSG')
			
	tree.write(manifestFile, 'UTF-8')

	return 0

