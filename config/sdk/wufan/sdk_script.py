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

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1

	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'com.papa91.pay.utils.WuFunFileProvider':
			authorities = '{'+androidNS+'}authorities'
			providerNode.set(authorities, packageName+".fileprovider")
		

	tree.write(manifestFile, 'UTF-8')

	return 0

