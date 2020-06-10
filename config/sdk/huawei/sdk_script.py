import file_utils
import os
import os.path
import config_utils
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

	modifyManifest(channel, decompileDir, packageName)

	return 0

def modifyManifest(channel, decompileDir, packageName):
	manifestFile = decompileDir + "/AndroidManifest.xml"
	manifestFile = file_utils.getFullPath(manifestFile)
	ET.register_namespace('android', androidNS)
	key = '{' + androidNS + '}name'
	authorityKey = '{'+androidNS+'}authorities'
	metaValue = '{'+androidNS+'}value'
	
	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return

	providerNodeLst = applicationNode.findall('provider')
	if providerNodeLst is None:
		return 1

	for providerNode in providerNodeLst:
		name = providerNode.get(key)
		if name == 'com.huawei.hms.update.provider.UpdateProvider':
			providerNode.set(authorityKey, packageName+".hms.update.provider")
		
		if name == 'com.huawei.hms.jos.games.archive.ArchiveRemoteAccessProvider':
			providerNode.set(authorityKey, packageName+".hmssdk.jos.archive")

		if name == 'com.huawei.agconnect.core.provider.AGConnectInitializeProvider':
			providerNode.set(authorityKey, packageName+".AGCInitializeProvider")
			
	receiverNodeLst = applicationNode.findall('receiver')
	if receiverNodeLst is None:
		return 1

			
	tree.write(manifestFile, 'UTF-8')

	return 0

