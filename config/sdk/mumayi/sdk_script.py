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
	authKey = '{'+androidNS+'}authorities'
	
	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	networkKey = '{'+androidNS+'}networkSecurityConfig'
	if networkKey not in applicationNode.attrib:
		applicationNode.set(networkKey, "@xml/mumayi_network_security_config")

	trafficKey = '{'+androidNS+'}usesCleartextTraffic'
	if trafficKey not in applicationNode.attrib:
		applicationNode.set(trafficKey, "true")

	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1

	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'com.mumayi.paymentmain.util.MMYFileProvider':
			providerNode.set(authKey, packageName+'.MMYFileProvider')
		

	tree.write(manifestFile, 'UTF-8')
	
	return 0
	