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
	host = '{'+androidNS+'}host'
	author = '{'+androidNS+'}authorities'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return 1

	for activityNode in activityNodeLst:
		name = activityNode.get(key)
		if name == 'com.anzhi.sdk.middle.manage.AgencyActivity':
			intentNodes = activityNode.findall('intent-filter')
			for intentNode in intentNodes:
				dataNodes = intentNode.findall('data')
				if dataNodes is not None and len(dataNodes) > 0:
					for dataNode in dataNodes:
						dataNode.set(host, packageName)
					
	proNodeLst = applicationNode.findall('provider')

	for proNode in proNodeLst:
		name = proNode.get(key)
		if name == 'com.anzhi.sdk.middle.manage.AnzhiFileProvider':
			proNode.set(author, packageName+'.anzhi_file_provider')				

	tree.write(manifestFile, 'UTF-8')

	return 0

