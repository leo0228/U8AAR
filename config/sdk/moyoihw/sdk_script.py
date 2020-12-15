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

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	networkKey = '{'+androidNS+'}networkSecurityConfig'
	if networkKey not in applicationNode.attrib:
		applicationNode.set(networkKey, "@xml/network_security_config")

	factoryKey = '{'+androidNS+'}appComponentFactory'
	if factoryKey in applicationNode.attrib:
		del applicationNode.attrib[factoryKey]

	for child in list(applicationNode):
		for serviceChild in list(child.iter('service')):              
			key = '{' + androidNS + '}directBootAware'              
			if key in serviceChild.attrib:
				del serviceChild.attrib[key]
				continue
		for activityChild in list(child.iter('activity')):              
			key = '{' + androidNS + '}enableVrMode'              
			if key in activityChild.attrib:
				del activityChild.attrib[key]
				continue

	authorityKey = '{'+androidNS+'}authorities'

	proNodeLst = applicationNode.findall('provider')
	if proNodeLst is None:
		return 1
					
	for proNode in proNodeLst:
		name = proNode.get(authorityKey)
		if name == '${applicationId}.FacebookInitProvider':
			proNode.set(authorityKey, packageName+'.FacebookInitProvider')
		if name == '${applicationId}.MarketingInitProvider':
			proNode.set(authorityKey, packageName+'.MarketingInitProvider')
	
	tree.write(manifestFile, 'UTF-8')

	return 0
	