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
	authorkey = '{' + androidNS + '}authorities'
	schemeKey = '{'+androidNS+'}scheme'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	providerNodeLst = applicationNode.findall('provider')

	for providerNode in providerNodeLst:
		myStr = providerNode.get(authorkey)
		
		print 'papapapapa1' + myStr
		newStr = myStr.replace('YourPackageName', packageName)
		providerNode.set(authorkey, newStr)
		print 'papapapapa2' + myStr.replace('YourPackageName', packageName)
		
	tree.write(manifestFile, 'UTF-8')

	return 0

