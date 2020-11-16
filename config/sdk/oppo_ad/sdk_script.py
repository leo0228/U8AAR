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
		if name == 'com.opos.mobad.provider.MobAdGlobalProvider':
			proNode.set(authorKey, packageName+'.MobAdGlobalProvider')	
		if name == 'com.bytedance.sdk.openadsdk.multipro.TTMultiProvider':
			proNode.set(authorKey, packageName+'.TTMultiProvider')	
		if name == 'com.bytedance.sdk.openadsdk.TTFileProvider':
			proNode.set(authorKey, packageName+'.TTFileProvider')	
		if name == 'android.support.v4.content.FileProvider':
			proNode.set(authorKey, packageName+'.fileprovider')		
		if name == 'com.heytap.msp.mobad.api.MobFileProvider':
			proNode.set(authorKey, packageName+'.MobFileProvider')
		if name == 'com.nearme.instant.router.ui.UpdateFileProvider':
			proNode.set(authorKey, packageName+'.router.upgrade.file')		

	tree.write(manifestFile, 'UTF-8')

	return 0

