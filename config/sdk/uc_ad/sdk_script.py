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
	locationKey = '{'+androidNS+'}installLocation'
	taskAffinity = '{'+androidNS+'}taskAffinity'
	schemeKey = '{'+androidNS+'}scheme'
	authKey = '{'+androidNS+'}authorities'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	root.attrib[locationKey] = 'auto'

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return 1
		
	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1
	
	ucGameID = ""

	if 'params' in channel:
		params = channel['params']
		for param in params:
			if param['name'] == 'UCGameId':
				ucGameID = param['value']

	for activityNode in activityNodeLst:
		name = activityNode.get(key)
		if name == 'cn.uc.gamesdk.activity.PullupActivity':
			activityNode.set(taskAffinity, packageName+".diff")
			intentNodes = activityNode.findall('intent-filter')
			for intentNode in intentNodes:
				dataNode = intentNode.find('data')
				if dataNode is not None:
					intentNode.remove(dataNode)
				dataNode = SubElement(intentNode, 'data')
				dataNode.set(schemeKey, 'ng'+ucGameID)

	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'android.support.v4.content.FileProvider':
			providerNode.set(authKey, packageName+'.fileprovider')
		if name == 'cn.gundam.sdk.shell.content.FileProvider':
			providerNode.set(authKey, packageName+'.gamesdk.fileprovider')
		if name == 'com.mintegral.msdk.base.utils.MTGFileProvider':
			providerNode.set(authKey, packageName+'.mtgFileProvider')
		if name == 'com.uniplay.adsdk.UniPlayFileProvider':
			providerNode.set(authKey, packageName+'.joomob.fileprovider')
		if name == 'com.bytedance.sdk.openadsdk.TTFileProvider':
			providerNode.set(authKey, packageName+'.TTFileProvider')
		if name == 'com.bytedance.sdk.openadsdk.multipro.TTMultiProvider':
			providerNode.set(authKey, packageName+'.TTMultiProvider')

	tree.write(manifestFile, 'UTF-8')

	return 0

