import file_utils
import apk_utils
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

	modifyActivityForSingleTop(channel, decompileDir, packageName)

	generateYSDKConfig(channel, decompileDir, packageName)

	return 0


def generateYSDKConfig(channel, decompileDir, packageName):

	qqAppID = ""
	wxAppID = ""
	offerID = ""
	ysdkUrl = ""

	cfStr = ""

	if 'params' in channel:
		params = channel['params']
		for p in params:
			if p['name'] == 'QQ_APP_ID':
				qqAppID = p['value']
			elif p['name'] == 'WX_APP_ID':
				wxAppID = p['value']
			elif p['name'] == 'OFFER_ID':
				offerID = p['value']
			elif p['name'] == 'YSDK_URL':
				ysdkUrl = p['value']

	cfStr = cfStr + "QQ_APP_ID=" + qqAppID+"\n"
	cfStr = cfStr + "WX_APP_ID=" + wxAppID+"\n"
	cfStr = cfStr + "OFFER_ID=" + offerID+"\n"
	cfStr = cfStr + "YSDK_URL=" + ysdkUrl+"\n"
	cfStr = cfStr + "YSDK_ICON_SWITCH=true\n"
	cfStr = cfStr + "YSDK_ANTIADDICTION_SWITCH=true\n"

	filepath = os.path.join(decompileDir, "assets/ysdkconf.ini")
	if os.path.exists(filepath):
		os.remove(filepath)

	f = open(filepath, 'w')
	f.write(cfStr)
	f.close()

def modifyManifest(channel, decompileDir, packageName):
	
	manifest = decompileDir + '/AndroidManifest.xml'
	ET.register_namespace('android', androidNS)
	tree = ET.parse(manifest)
	root = tree.getroot()

	key = '{' + androidNS + '}name'
	scheme = '{'+androidNS+'}scheme'
	taskAffinity = '{' + androidNS + '}taskAffinity'
	authorities = '{'+androidNS+'}authorities'
	value = '{' + androidNS + '}value'

	appNode = root.find('application')
	if appNode is None:
		return 1

	providerNodeList = appNode.findall('provider')
	if providerNodeList is None:
		return 1

	for providerNode in providerNodeList:
		providerName = providerNode.get(key)
		if providerName == 'com.tencent.ysdk.framework.YSDKInitProvider':
			providerNode.set(authorities, packageName+'.ysdk.ysdkinitprovider')

	activityAliasNodeList = appNode.findall('activity-alias')
	if activityAliasNodeList is None:
		return 1

	for activityAliasNode in activityAliasNodeList:
		name = activityAliasNode.get(key)
		if name == 'com.u8.sdk.wxapi.WXEntryActivity':
			activityAliasNode.set(key, packageName + '.wxapi.WXEntryActivity')
			break

	metaNodeList = appNode.findall('meta-data')
	if metaNodeList is None:
		return 1

	for metaNode in metaNodeList:
		name = metaNode.get(key)
		if name == 'MAIN_ACTIVITY':
			metaNode.set(value, packageName + '.MainActivity')
			break

	activityNodeList = appNode.findall('activity')
	if activityNodeList is None:
		return 1

	for activityNode in activityNodeList:
		activityName = activityNode.get(key)
		if activityName == 'com.tencent.tauth.AuthActivity':
			intentFilters = activityNode.findall('intent-filter')
			if intentFilters != None and len(intentFilters) > 0:
				for intentNode in intentFilters:		
					dataNode = intentNode.find('data')
					intentNode.remove(dataNode)
					dataNode = SubElement(intentNode, 'data')
					for child in channel['params']:
						if child['name'] == 'QQ_APP_ID':
							dataNode.set(scheme, 'tencent'+child['value'])
							break
						
		elif activityName == 'com.tencent.ysdk.module.user.impl.wx.YSDKWXEntryActivity':
			activityNode.set(taskAffinity, packageName + '.diff')
			intentFilters = activityNode.findall('intent-filter')
			if intentFilters != None and len(intentFilters) > 0:
				for intentNode in intentFilters:
					dataNode = intentNode.find('data')
					intentNode.remove(dataNode)
					dataNode = SubElement(intentNode, 'data')
					for child in channel['params']:
						if child['name'] == 'WX_APP_ID':
							dataNode.set(scheme, child['value'])
							break

		if activityName == 'com.tencent.ysdk.module.user.impl.freelogin.FreeLoginInfoActivity':
			intentFilters = activityNode.findall('intent-filter')
			if intentFilters != None and len(intentFilters) > 0:
				for intentNode in intentFilters:	
					dataNode = intentNode.find('data')
					intentNode.remove(dataNode)	
					dataNode = SubElement(intentNode, 'data')
					for child in channel['params']:
						if child['name'] == 'QQ_APP_ID':
							dataNode.set(scheme, 'tencentysdk'+child['value'])
							break

	tree.write(manifest, 'UTF-8')

	return 0

def modifyActivityForSingleTop(channel, decompileDir, packageName):
	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{' + androidNS + '}launchMode'
	keyName = '{' + androidNS + '}name'
	screenKey = '{'+androidNS+'}screenOrientation'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return

	activityName = ''

	screenOrientation = 'sensorLandscape'

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
				if actionNode.attrib[keyName] == 'android.intent.action.MAIN':
					bFindAction = True
					break

			categoryNodeLst = intentNode.findall('category')
			if categoryNodeLst is None:
				break
			for categoryNode in categoryNodeLst:
				if categoryNode.attrib[keyName] == 'android.intent.category.LAUNCHER':
					bFindCategory = True
					break

			if bFindAction and bFindCategory:
				bMain = True
				break

		if bMain:
			activityNode.set(key, "singleTop")
			screenOrientation = activityNode.get(screenKey)
			break


	activityNodes = applicationNode.findall('activity')
	if activityNodes != None and len(activityNodes) > 0:
		for activityNode in activityNodes:
			activityName = activityNode.get(keyName)
			if activityName == 'com.tencent.midas.proxyactivity.APMidasPayProxyActivity':
				if screenOrientation and len(screenOrientation) > 0:
					activityNode.set(screenKey, screenOrientation)
				else:
					activityNode.set(screenKey, 'portrait')
				break

	tree.write(manifestFile, 'UTF-8')

	return 0	


	


