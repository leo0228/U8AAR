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
	authorKey = '{'+androidNS+'}authorities'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	networkKey = '{'+androidNS+'}networkSecurityConfig'
	if networkKey not in applicationNode.attrib:
		applicationNode.set(networkKey, "@xml/network_security_config")
	
	proNodeLst = applicationNode.findall('provider')

	for proNode in proNodeLst:
		name = proNode.get(key)
		if name == 'com.nearme.platform.opensdk.pay.NearMeFileProvider':
			proNode.set(authorKey, packageName+'.fileProvider')	

	tree.write(manifestFile, 'UTF-8')

	return 0

