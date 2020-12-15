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
appNS = 'http://schemas.android.com/apk/res-auto'

def execute(channel, decompileDir, packageName):
	resPath = decompileDir + "/res"
	resPath = file_utils.getFullPath(resPath)
	deleteXML(resPath)

	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{' + androidNS + '}name'
	authorities = '{'+androidNS+'}authorities'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	networkKey = '{'+androidNS+'}networkSecurityConfig'
	if networkKey not in applicationNode.attrib:
		applicationNode.set(networkKey, "@xml/network_security_config")

	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1

	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'com.xiaomi.gamecenter.sdk.utils.MiFileProvider':
			providerNode.set(authorities, packageName+'.mi_fileprovider')
		if name == 'android.support.v4.content.FileProvider':
			providerNode.set(authorities, packageName+'.fileprovider')

	tree.write(manifestFile, 'UTF-8')

	return 0

def deleteXML(res):
	for f in os.listdir(res):
		sourcefile = os.path.join(res, f)
		sourcedir = os.path.dirname(sourcefile)
		
		if ((f == 'abc_btn_colored_borderless_text_material.xml' or f == 'abc_btn_colored_text_material.xml') and sourcedir.endswith('color')):
			file_utils.del_file_folder(sourcefile)  

		if(f.startswith('abc_tint')):
			file_utils.del_file_folder(sourcefile)     
			
		if os.path.isdir(sourcefile): 
			deleteXML(sourcefile)
			  


