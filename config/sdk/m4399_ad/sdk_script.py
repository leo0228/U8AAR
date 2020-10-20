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
	startJpush(channel, decompileDir, packageName)
	return 0

def startJpush(channel, decompileDir, packageName):
	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{'+androidNS+'}name'
	schemeKey = '{'+androidNS+'}scheme'
	authKey = '{'+androidNS+'}authorities'
	
	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	
	if applicationNode is None:
		return 1
	
	networkKey = '{'+androidNS+'}networkSecurityConfig'
	if networkKey not in applicationNode.attrib:
		applicationNode.set(networkKey, "@xml/m4399_network_policy")
		
	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1
		
	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'cn.m4399.operate.OpeFileProvider':
			providerNode.set(authKey, packageName+".operate.FileProvider")
		if name == 'com.mintegral.msdk.base.utils.MTGFileProvider':
			providerNode.set(authKey, packageName+".mtgFileProvider")

	tree.write(manifestFile, 'UTF-8')
	return 0
	