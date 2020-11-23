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
import log_utils
import apk_utils

androidNS = 'http://schemas.android.com/apk/res/android'

def execute(channel, decompileDir, packageName):

	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{' + androidNS + '}name'
	schemeKey = '{'+androidNS+'}scheme'
	authorityKey = '{'+androidNS+'}authorities'

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	networkKey = '{'+androidNS+'}networkSecurityConfig'
	if networkKey not in applicationNode.attrib:
		applicationNode.set(networkKey, "@xml/network_security_config")

	activityNodeList = applicationNode.findall('activity')
	hardwareKey = '{'+androidNS+'}hardwareAccelerated'
	for activityNode in activityNodeList:
		name = activityNode.get(key)
		if name == 'com.ncroquis.moyoiunityplugin.MainActivity':
			activityNode.set(hardwareKey, "true")

	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1

	for proNode in providerNodeLst:
		name = proNode.get(key)
		if name == 'com.bytedance.sdk.openadsdk.multipro.TTMultiProvider':
			proNode.set(authorityKey, packageName+'.TTMultiProvider')
		if name == 'com.bytedance.sdk.openadsdk.TTFileProvider':
			proNode.set(authorityKey, packageName+'.TTFileProvider')
		if name == 'android.support.v4.content.FileProvider':
			proNode.set(authorityKey, packageName+'.fileprovider')


	tree.write(manifestFile, 'UTF-8')

	return 0

