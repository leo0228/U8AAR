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
	startJpush(channel, decompileDir, packageName)
	return 0

def startJpush(channel, decompileDir, packageName):
	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{'+androidNS+'}name'
	schemeKey = '{'+androidNS+'}scheme'
	authKey = '{'+androidNS+'}authorities'
	
	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	
	if applicationNode is None:
		return 1
	
	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1
		
	serviceNodeLst = applicationNode.findall('service')
	if serviceNodeLst is None:
		return 1
		
	receiverNodeLst = applicationNode.findall('receiver')
	if receiverNodeLst is None:
		return 1
		
	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return 1
			
	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'com.huawei.hms.update.provider.UpdateProvider':
			providerNode.set(authKey, packageName+'.hms.update.provider')
		
	for receiverNode in receiverNodeLst:
		intentNodes = receiverNode.findall('intent-filter')
		if intentNodes is not None and len(intentNodes) > 0:
			for intentNode in intentNodes:
				actionNodes = intentNode.findall('action')
				if actionNodes is not None and len(actionNodes) > 0:
					for actionNode in actionNodes:
						name = actionNode.get(key)
						if name == 'com.meizu.ups.push.intent.MESSAGE':
							receiverNode.set(key, 'com.u8.sdk.UpsReceiver')
							
		name = receiverNode.get(key)
		if name == 'com.meizu.upspushsdklib.receiver.MzUpsPushMessageReceiver':
			intentNodes = receiverNode.findall('intent-filter')
			if intentNodes is not None and len(intentNodes) > 0:
				for intentNode in intentNodes:
					cateNode1 = SubElement(intentNode, 'category')
					cateNode1.set(key, packageName)
			
	
	receiverNode1 = SubElement(applicationNode, 'receiver')
	receiverNode1.set(key, 'com.u8.sdk.PushMsgReceiver')
	intenNode1 = SubElement(receiverNode1, 'intent-filter')
	actNode11 = SubElement(intenNode1, 'action')
	actNode11.set(key, 'com.meizu.flyme.push.intent.MESSAGE')
	actNode12 = SubElement(intenNode1, 'action')
	actNode12.set(key, 'com.meizu.flyme.push.intent.REGISTER.FEEDBACK')
	actNode13 = SubElement(intenNode1, 'action')
	actNode13.set(key, 'com.meizu.flyme.push.intent.UNREGISTER.FEEDBACK')
	actNode14 = SubElement(intenNode1, 'action')
	actNode14.set(key, 'com.meizu.c2dm.intent.REGISTRATION')
	actNode15 = SubElement(intenNode1, 'action')
	actNode15.set(key, 'com.meizu.c2dm.intent.RECEIVE')
	cateNode = SubElement(intenNode1, 'category')
	cateNode.set(key, packageName)
	
	userPerNode1 = SubElement(root, 'uses-permission')
	userPerNode1.set(key, packageName+'.permission.MIPUSH_RECEIVE')
	
	perNode1 = SubElement(root, 'permission')
	perNode1.set(key, packageName+'.permission.MIPUSH_RECEIVE')
	perNode1.set('{'+androidNS+'}protectionLevel', 'signature')
	
	mzuserPerNode1 = SubElement(root, 'uses-permission')
	mzuserPerNode1.set(key, packageName+'.push.permission.MESSAGE')
	
	mzperNode1 = SubElement(root, 'permission')
	mzperNode1.set(key, packageName+'.push.permission.MESSAGE')
	mzperNode1.set('{'+androidNS+'}protectionLevel', 'signature')
	
	c2userPerNode1 = SubElement(root, 'uses-permission')
	c2userPerNode1.set(key, packageName+'.permission.C2D_MESSAGE')
	
	c2perNode1 = SubElement(root, 'permission')
	c2perNode1.set(key, packageName+'.permission.C2D_MESSAGE')
	c2perNode1.set('{'+androidNS+'}protectionLevel', 'signature')
			
	tree.write(manifestFile, 'UTF-8')
	return 0
	