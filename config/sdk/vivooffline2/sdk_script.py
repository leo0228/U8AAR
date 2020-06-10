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

	tree = ET.parse(manifestFile)
	root = tree.getroot()

	applicationNode = root.find('application')
	if applicationNode is None:
		return 1

	activityNodeLst = applicationNode.findall('activity')
	if activityNodeLst is None:
		return 1

	receiverNodeLst = applicationNode.findall('receiver')
	if receiverNodeLst is None:
		return 1

	for receiverNode in receiverNodeLst:
		intentNodes = receiverNode.findall('intent-filter')
		if intentNodes is not None and len(intentNodes) > 0:
			for intentNode in intentNodes:
				actionNodes = intentNode.findall('action')
				if actionNodes is not None and len(actionNodes) > 0:
					for actionNode in actionNodes:
						actionName = actionNode.get(key)
						if actionName == 'com.vivo.pushclient.action.RECEIVE':
							receiverNode.set(key, 'com.u8.sdk.PushMessageReceiverImpl')

	tree.write(manifestFile, 'UTF-8')

	return 0

