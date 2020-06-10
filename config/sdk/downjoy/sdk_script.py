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
	key = '{'+androidNS+'}name'
	schemeKey = '{'+androidNS+'}scheme'
	
	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	#applicationNode.set('{'+androidNS+'}networkSecurityConfig', '@xml/network_security_config')

	perNode = SubElement(applicationNode, 'uses-library')
	perNode.set(key, 'org.apache.http.legacy')
	perNode.set('{' + androidNS + '}required', 'false')

	perNode = SubElement(applicationNode, 'meta-data')
	perNode.set(key, 'android.max_aspect')
	perNode.set('{' + androidNS + '}value', '2.1')

	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return 1

	for activityNode in activityNodeLst:
		name = activityNode.get(key)
		if name == 'com.downjoy.activity.SdkActivity':
			intentNodes = activityNode.findall('intent-filter')
			if intentNodes is not None and len(intentNodes) > 0:
				for intentNode in intentNodes:
					dataNodes = intentNode.findall('data')
					if dataNodes is not None and len(dataNodes) > 0:
						for dataNode in dataNodes:
							scheme = dataNode.get(schemeKey)
							if scheme.startswith('dcnngsdk'):
								intentNode.remove(dataNode)
								for child in channel['params']:
									if child['name'] == 'APP_ID':
										dataNode1 = SubElement(intentNode, 'data')
										dataNode1.set(schemeKey, 'dcnngsdk'+child['value'])

	providerNodeLst = applicationNode.findall('provider')

	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'com.qihoo360.replugin.component.process.ProcessPitProviderPersist':
			providerNode.set('{'+androidNS+'}authorities', packageName+'.loader.p.main')
		elif name == 'com.qihoo360.replugin.component.provider.PluginPitProviderPersist':
			providerNode.set('{'+androidNS+'}authorities', packageName+".Plugin.NP.PSP")	
		elif name == 'com.qihoo360.mobilesafe.svcmanager.ServiceProvider':
			providerNode.set('{'+androidNS+'}authorities', packageName+".svcmanager")	
		elif name == 'android.support.v4.content.FileProvider':
			providerNode.set('{'+androidNS+'}authorities', packageName+".android7.fileprovider")

	tree.write(manifestFile, 'UTF-8')
	
	return 0
	