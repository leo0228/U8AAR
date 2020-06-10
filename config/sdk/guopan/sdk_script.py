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
	schemeKey = '{'+androidNS+'}scheme'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1
		
	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return 1

	for provider in providerNodeLst:
		name = provider.get(key)
		if name == 'com.flamingo.sdk.plugin.proxy.StubContentProvider':
			provider.set('{'+androidNS+'}authorities', packageName+'.StubContentProvider')
			break
			
	for activityNode in activityNodeLst:
		name = activityNode.get(key)
		if name == 'com.flamingo.sdk.view.GPSplashActivity':
			intentNodes = activityNode.findall('intent-filter')
			if intentNodes is not None and len(intentNodes) > 0:
				for intentNode in intentNodes:
					actionNodes = intentNode.findall('action')
					cateNodes = intentNode.findall('category')
					if actionNodes is not None and len(actionNodes) > 0:
						for actionNode in actionNodes:
							actionName = actionNode.get(key)
							if actionName == 'android.intent.action.MAIN':
								intentNode.remove(actionNode)
								actionNode = SubElement(intentNode, 'action')
								actionNode.set(key, 'com.flamingo.sdk.MAIN')

	tree.write(manifestFile, 'UTF-8')

	return 0

