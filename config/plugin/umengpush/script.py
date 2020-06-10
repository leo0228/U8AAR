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

def execute(channel, pluginInfo, decompileDir, packageName):
	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{' + androidNS + '}launchMode'

	tree = ET.parse(manifestFile)
	root = tree.getroot()
	package = root.attrib.get('package')

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	key = '{'+androidNS+'}name'
	receiverNodeList = applicationNode.findall('receiver')
	
	metaNodeLst = applicationNode.findall('meta-data')
	if metaNodeLst is None:
		print('333333333333333333333333333333333333')
		return 1
	print('22222222222222222222222222222222222222222')
	print("now pluginInfo:%s", pluginInfo['UMENG_APPKEY'])
	opIdvalue = '{'+androidNS+'}value'
	
	global openId = pluginInfo['UMENG_APPKEY']
	
	for metaNode in metaNodeLst:
		name = metaNode.get(key)
		print('4444444444444444')
		print(name)
		if name == 'UMENG_APPKEY':
			print(metaNode.get(key))
			print(metaNode.get(opIdvalue))
			openId = metaNode.get(opIdvalue)
			print(openId)
			break
			
	if 'params' in pluginInfo and len(pluginInfo['params']) > 0:
		for param in pluginInfo['params']:
			name = param.get('name')
			if name == 'UMENG_CHANNEL':
				param['value'] = channel['name']
				break
				
	if receiverNodeList != None:
		for node in receiverNodeList:
			if node.attrib[key] == 'com.taobao.agoo.AgooCommondReceiver':
				intentNodeLst = node.findall('intent-filter')
				if intentNodeLst is None:
					break

				for intentNode in intentNodeLst:
					actionNodeList = intentNode.findall('action')
					if actionNodeList is None:
						break

					for actionNode in actionNodeList:
						if actionNode.attrib[key].endswith('intent.action.COMMAND'):
							newVal = openId + '.intent.action.COMMAND'
							actionNode.set(key, newVal)

	providerNodeList = applicationNode.findall('provider')

	if providerNodeList != None:
		for node in providerNodeList:
			if node.attrib[key] == 'com.umeng.message.provider.MessageProvider':
				cateNode = SubElement(node, 'category')
				cateNode.set('{' + androidNS + '}authorities', openId+'.umeng.message')
				
	tree.write(manifestFile, 'UTF-8')

	return 0

