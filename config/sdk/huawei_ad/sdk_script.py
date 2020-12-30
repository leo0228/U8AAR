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
	hostKey = '{'+androidNS+'}host'
	
	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return

	networkKey = '{'+androidNS+'}networkSecurityConfig'
	if networkKey not in applicationNode.attrib:
		applicationNode.set(networkKey, "@xml/network_security_config")

	trafficKey = '{'+androidNS+'}usesCleartextTraffic'
	if trafficKey not in applicationNode.attrib:
		applicationNode.set(trafficKey, "true")

	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return 1

	for activityNode in activityNodeLst:
		name = activityNode.get(key)
		if name == 'com.huawei.openalliance.ad.activity.PPSLauncherActivity':
			intentNodes = activityNode.findall('intent-filter')
			if intentNodes is not None and len(intentNodes) > 0:
				for intentNode in intentNodes:
					dataNodes = intentNode.findall('data')
					if dataNodes is not None and len(dataNodes) > 0:
						for dataNode in dataNodes:
							dataNode.set(hostKey, packageName)

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
		if name == 'com.huawei.updatesdk.fileprovider.UpdateSdkFileProvider':
			providerNode.set(authorityKey, packageName+".updateSdk.fileProvider")
			
	tree.write(manifestFile, 'UTF-8')

	return 0

