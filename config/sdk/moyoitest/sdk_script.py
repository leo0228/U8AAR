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
import log_utils

androidNS = 'http://schemas.android.com/apk/res/android'

def execute(channel, decompileDir, packageName):
	modifyWeiXin(channel, decompileDir, packageName)
	
	startJpush(channel, decompileDir, packageName)
	return 0
	
def modifyWeiXin(channel, decompileDir, packageName):
	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{'+androidNS+'}name'
	schemeKey = '{'+androidNS+'}scheme'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	activityNodeLst = applicationNode.findall('activity-alias')
	if activityNodeLst is None:
		return 1

	for activityNode in activityNodeLst:
		name = activityNode.get(key)
		if name == 'com.ftt.hwal2.gl.global.wxapi.WXEntryActivity':
			activityNode.set(key, packageName+'.wxapi.WXEntryActivity')
			
		elif name == 'com.ftt.hwal2.gl.global.wxapi.WXPayEntryActivity':
			activityNode.set(key, packageName+'.wxapi.WXPayEntryActivity')
			
	tree.write(manifestFile, 'UTF-8')
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
		print("providerNode name : "+ name)
		if name == 'cn.jpush.android.service.DataProvider':
			providerNode.set(authKey, packageName+'.DataProvider')
			
		elif name == 'cn.jpush.android.service.DownloadProvider':
			providerNode.set(authKey, packageName+'.DownloadProvider')
			
	for serviceNode in serviceNodeLst:
		name = serviceNode.get(key)
		if name == 'cn.jpush.android.service.DaemonService':
			intentNodes = serviceNode.findall('intent-filter')
			if intentNodes is not None and len(intentNodes) > 0:
				for intentNode in intentNodes:
					cateNode1 = SubElement(intentNode, 'category')
					cateNode1.set(key, packageName)
			
	for receiverNode in receiverNodeLst:
		name = receiverNode.get(key)
		if name == 'cn.jpush.android.service.PushReceiver':
			intentNodes = receiverNode.findall('intent-filter')
			if intentNodes is not None and len(intentNodes) > 0:
				for intentNode in intentNodes:
					actionNodes = intentNode.findall('action')
					if actionNodes is not None and len(actionNodes) > 0:
						for actionNode in actionNodes:
							name = actionNode.get(key)
							if name == 'cn.jpush.android.intent.NOTIFICATION_RECEIVED_PROXY':
								cateNode1 = SubElement(intentNode, 'category')
								cateNode1.set(key, packageName)
			
	for activityNode in activityNodeLst:
		name = activityNode.get(key)
		if name == 'cn.jpush.android.ui.PushActivity':
		
			userPerNode1 = SubElement(root, 'uses-permission')
			userPerNode1.set(key, packageName+'.permission.JPUSH_MESSAGE')
			
			perNode1 = SubElement(root, 'permission')
			perNode1.set(key, packageName+'.permission.JPUSH_MESSAGE')
			perNode1.set('{'+androidNS+'}protectionLevel', 'signature')
			
			intentNodes = activityNode.findall('intent-filter')
			if intentNodes is not None and len(intentNodes) > 0:
				for intentNode in intentNodes:
					actionNodes = intentNode.findall('action')
					if actionNodes is not None and len(actionNodes) > 0:
						for actionNode in actionNodes:
							name = actionNode.get(key)
							if name == 'cn.jpush.android.ui.PushActivity':
								cateNode1 = SubElement(intentNode, 'category')
								cateNode1.set(key, packageName)
			
		elif name == 'cn.jpush.android.ui.PopWinActivity':
			intentNodes = activityNode.findall('intent-filter')
			if intentNodes is not None and len(intentNodes) > 0:
				for intentNode in intentNodes:
					cateNode1 = SubElement(intentNode, 'category')
					cateNode1.set(key, packageName)
			
	tree.write(manifestFile, 'UTF-8')
	return 0
	