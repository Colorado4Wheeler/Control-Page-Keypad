#! /usr/bin/env python
# -*- coding: utf-8 -*-

import indigo

import os
import sys
import time
import datetime

from eps.cache import cache
from eps import ui
from eps import dtutil
from eps import eps
import re
from datetime import timedelta
from bs4 import BeautifulSoup
import ast
import urllib2


################################################################################
# RELEASE NOTES
################################################################################

# June 24, 2016
#	- Added updateCheck
#	- Added import of timedelta, re and BeautifulSoup
#	- Added updateCheck to first action of onConcurrentThread
#	- Added menu option to check for updates
#	- Added self.pluginUrl as a startup option (points to forum thread with hidden version info)

# June 20, 2016
#   - setStateDisplay added as an EPS routine to set the state icon and text
#	- deviceStartComm modified to call setStateDisplay at the end of the routine
#	- onConcurrentThread modified to call setStateDisplay as the last statement

################################################################################
class Plugin(indigo.PluginBase):
	
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		# EPS common startup
		try:
			self.debug = pluginPrefs["debugMode"]
			pollingMode = pluginPrefs["pollingMode"]
			pollingInterval = int(pluginPrefs["pollingInterval"])
			pollingFrequency = pluginPrefs["pollingFrequency"]
			self.monitor = pluginPrefs["monitorChanges"]
		except:
			indigo.server.log ("Preference options may have changed or are corrupt,\n\tgo to Plugins -> %s -> Configure to reconfigure %s and then reload the plugin.\n\tUsing defaults for now, the plugin should operate normally." % (pluginDisplayName, pluginDisplayName), isError = True)
			self.debug = False
			pollingMode = "realTime"
			pollingInterval = 1
			pollingFrequency = "s"
			self.monitor = False
			
		# EPS common variables and classes
		self.pluginUrl = "http://forums.indigodomo.com/viewtopic.php?f=196&t=16325" #http://forums.indigodomo.com/viewtopic.php?f=196&t=16325
		eps.parent = self
		self.reload = False
		self.cache = cache (self, pluginId, pollingMode, pollingInterval, pollingFrequency)
		
		# EPS plugin specific variables and classes
		
			
	################################################################################
	# EPS ROUTINES
	################################################################################

	#
	# Base
	#
	def base (self):
		try:
			X = 1
		
		except Exception as e:
			eps.printException(e)
			
	#
	# Plugin menu: Performance options
	#
	def performanceOptions (self, valuesDict, typeId):
		self.debugLog(u"Saving performance options")
		errorsDict = indigo.Dict()
		
		# Save the performance options into plugin prefs
		self.pluginPrefs["pollingMode"] = valuesDict["pollingMode"]
		self.pluginPrefs["pollingInterval"] = valuesDict["pollingInterval"]
		self.pluginPrefs["pollingFrequency"] = valuesDict["pollingFrequency"]
		
		self.cache.setPollingOptions (valuesDict["pollingMode"], valuesDict["pollingInterval"], valuesDict["pollingFrequency"])
		
		return (True, valuesDict, errorsDict)
		
	#
	# Plugin menu: Library versions
	#
	def showLibraryVersions (self, forceDebug = False):
		s =  eps.debugHeader("LIBRARY VERSIONS")
		s += eps.debugLine (self.pluginDisplayName + " - v" + self.pluginVersion)
		s += eps.debugHeaderEx ()
		s += eps.debugLine ("Cache %s" % self.cache.version)
		s += eps.debugLine ("UI %s" % ui.libVersion(True))
		s += eps.debugLine ("DateTime %s" % dtutil.libVersion(True))
		s += eps.debugLine ("Core %s" % eps.libVersion(True))
		s += eps.debugHeaderEx ()
		
		if forceDebug:
			self.debugLog (s)
			return
			
		indigo.server.log (s)
		
	#
	# Device action: Update
	#
	def updateDevice (self, devAction):
		dev = indigo.devices[devAction.deviceId]
		
		children = self.cache.getSubDevices (dev)
		for devId in children:
			subDev = indigo.devices[int(devId)]	
			self.updateDeviceStates (dev, subDev)	
		
		return
			
	#
	# Update device
	#
	def updateDeviceStates (self, parentDev, childDev = None):
		stateChanges = self.cache.deviceUpdate (parentDev)
		
		return
		
	#
	# Add watched states
	#
	def addWatchedStates (self, subDevId = "*", deviceTypeId = "*", mainDevId = "*"):
		# The only device we currently watch is sprinklers so we know what zone came on and for how long
		if deviceTypeId == "*" or deviceTypeId == "sprinklerKeypad":
			dev = indigo.devices[int(mainDevId)]
			if eps.valueValid (dev.pluginProps, "device", True):
				devChild = indigo.devices[int(dev.pluginProps["device"])]
				subDevId = devChild.id # Must be specific for multiple choice
			
				self.cache.addWatchState ("activeZone", subDevId, "sprinklerKeypad", dev.id)
		
		#self.cache.addWatchState ("onOffState", subDevId, "epsCustomDev")
		
		#self.cache.addWatchState (848833485, "onOffState", 1089978714)
		
		#self.cache.addWatchState ("onOffState", subDevId, deviceTypeId, mainDevId) # All devices, pass vars
		#self.cache.addWatchState ("onOffState") # All devices, all subdevices, all types
		#self.cache.addWatchState ("onOffState", 848833485) # All devices, this subdevice, all types
		#self.cache.addWatchState ("onOffState", subDevId, "epslcdth") # All devices, all subdevices of this type
		#self.cache.addWatchState ("onOffState", 848833485, "*", 1089978714) # This device, this subdevice of all types
		
		return
		
	#
	# Set state display on the device
	#
	def setStateDisplay (self, dev, force = False):
		stateValue = None
		stateUIValue = ""
		stateIcon = None
		stateDecimals = -1
		
		if dev.deviceTypeId == "devtemplate":
			X = 1 # placeholder
		
		else:
			return # failsafe
				
		if stateValue is None: return # nothing to do
		
		if force == False:
			if "statedisplay.ui" in dev.states:
				if stateValue == dev.states["statedisplay"] and stateUIValue == dev.states["statedisplay.ui"]: return # nothing to do
			else:
				if stateValue == dev.states["statedisplay"]: return # nothing to do
		
		dev.updateStateImageOnServer(stateIcon)
		
		if stateDecimals > -1:
			dev.updateStateOnServer("statedisplay", value=stateValue, uiValue=stateUIValue, decimalPlaces=stateDecimals)
		else:
			dev.updateStateOnServer("statedisplay", value=stateValue, uiValue=stateUIValue)	
	
	################################################################################
	# EPS HANDLERS
	################################################################################
		
	#
	# Device menu selection changed
	#
	def onDeviceSelectionChange (self, valuesDict, typeId, devId):
		# Just here so we can refresh the states for dynamic UI
		return valuesDict
		
	#
	# Device menu selection changed (for MenuItems.xml only)
	#
	def onMenuDeviceSelectionChange (self, valuesDict, typeId):
		# Just here so we can refresh the states for dynamic UI
		return valuesDict
	
	#
	# Return folder list
	#
	def getIndigoFolders(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getIndigoFolders (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of device states to (filter is the device to query)
	#
	def getStatesForDevice(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getStatesForDevice (filter, valuesDict, typeId, targetId)
	
	#
	# Return option array of devices with filter in states (filter is the state(s) to query)
	#
	def getDevicesWithStates(self, filter="onOffState", valuesDict=None, typeId="", targetId=0):
		return ui.getDevicesWithStates (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of device plugin props to (filter is the device to query)
	#
	def getPropsForDevice(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getPropsForDevice (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of plugin devices props to (filter is the plugin(s) to query)
	#
	def getPluginDevices(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getPluginDevices (filter, valuesDict, typeId, targetId)
		
	#
	# Return custom list
	#
	def getDataList(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getDataList (filter, valuesDict, typeId, targetId)
		
	#
	# Handle ui button click
	#
	def uiButtonClicked (self, valuesDict, typeId, devId):
		return valuesDict
		
	#
	# Concurrent thread process fired
	#
	def onRunConcurrentThread (self):
		self.updateCheck(True, False)
		self.checkDeviceTimeout()
		return
		
		
	################################################################################
	# EPS ROUTINES TO BE PUT INTO THEIR OWN CLASSES / METHODS
	################################################################################
		
	
	################################################################################
	# INDIGO DEVICE EVENTS
	################################################################################
	
	#
	# Device starts communication
	#
	def deviceStartComm(self, dev):
		self.debugLog(u"%s starting communication" % dev.name)
		dev.stateListOrDisplayStateIdChanged() # Make sure any device.xml changes are incorporated
		#if self.cache is None: return
		
		if "lastreset" in dev.states:
			d = indigo.server.getTime()
			if dev.states["lastreset"] == "": dev.updateStateOnServer("lastreset", d.strftime("%Y-%m-%d"))
		
		if self.cache.deviceInCache (dev.id) == False and dev.deviceTypeId == "sprinklerKeypad":
			self.debugLog(u"%s not in cache, appears to be a new device or plugin was just started" % dev.name)
			self.cache.cacheDevices() # Failsafe
			
		self.addWatchedStates("*", dev.deviceTypeId, dev.id)		
		
		if len(dev.pluginProps) != 0: self.deviceReset (dev)
			
		#self.addWatchedStates("*", dev.deviceTypeId, dev.id) # Failsafe
		#self.cache.dictDump (self.cache.devices[dev.id])

		self.setStateDisplay(dev)
			
		return
			
	#
	# Device stops communication
	#
	def deviceStopComm(self, dev):
		self.debugLog(u"%s stopping communication" % dev.name)
		
	#
	# Device property changed
	#
	def didDeviceCommPropertyChange(self, origDev, newDev):
		self.debugLog(u"%s property changed" % origDev.name)
		return True	
	
	#
	# Device property changed
	#
	def deviceUpdated(self, origDev, newDev):
		if self.cache is None: return
		
		if eps.isNewDevice(origDev, newDev):
			self.debugLog("New device '%s' detected, restarting device communication" % newDev.name)
			self.deviceStartComm (newDev)
			return		
		
		if origDev.pluginId == self.pluginId:
			self.debugLog(u"Plugin device %s was updated" % origDev.name)
			
			# Re-cache the device and it's subdevices and states
			if eps.dictChanged (origDev, newDev):
				self.debugLog(u"Plugin device %s settings changed, rebuilding watched states" % origDev.name)
				self.cache.removeDevice (origDev.id)
				self.deviceStartComm (newDev)
			
		else:
			changedStates = self.cache.watchedStateChanged (origDev, newDev)
			if changedStates:
				self.debugLog(u"The monitored device %s had a watched state change" % origDev.name)
				
				for devId, stateChange in changedStates.iteritems():
					dev = indigo.devices[devId]
					
					if dev.deviceTypeId == "sprinklerKeypad":
						if dev.pluginProps["device"] == str(newDev.id): dev.updateStateOnServer ("device1ZoneOn", indigo.server.getTime().strftime("%Y-%m-%d %H:%M:%S"))
						if dev.pluginProps["device2"] == str(newDev.id): dev.updateStateOnServer ("device2ZoneOn", indigo.server.getTime().strftime("%Y-%m-%d %H:%M:%S"))
						if dev.pluginProps["device3"] == str(newDev.id): dev.updateStateOnServer ("device3ZoneOn", indigo.server.getTime().strftime("%Y-%m-%d %H:%M:%S"))
					
		return
		
	#
	# Device deleted
	#
	def deviceDeleted(self, dev):
		if dev.pluginId == self.pluginId:
			self.debugLog("%s was deleted" % dev.name)
			self.cache.removeDevice (dev.id)
		
	
	################################################################################
	# INDIGO DEVICE UI EVENTS
	################################################################################	
	
		
	#
	# Device pre-save event
	#
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		dev = indigo.devices[devId]
		self.debugLog(u"%s is validating device configuration UI" % dev.name)
		return (True, valuesDict)
		
	#
	# Device config button clicked event
	#
	def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId):
		dev = indigo.devices[devId]
		self.debugLog(u"%s is closing device configuration UI" % dev.name)
		
		if userCancelled == False: 
			self.debugLog(u"%s configuration UI was not cancelled" % dev.name)
			
		#self.cache.dictDump (self.cache.devices[dev.id])
			
		return
		
	#
	# Event pre-save event
	#
	def validateEventConfigUi(self, valuesDict, typeId, eventId):
		self.debugLog(u"Validating event configuration UI")
		return (True, valuesDict)
		
	#
	# Event config button clicked event
	#
	def closedEventConfigUi(self, valuesDict, userCancelled, typeId, eventId):
		self.debugLog(u"Closing event configuration UI")
		return
		
	#
	# Action pre-save event
	#
	def validateActionConfigUi(self, valuesDict, typeId, actionId):
		self.debugLog(u"Validating event configuration UI")
		return (True, valuesDict)
		
	#
	# Action config button clicked event
	#
	def closedActionConfigUi(self, valuesDict, userCancelled, typeId, actionId):
		self.debugLog(u"Closing action configuration UI")
		return
		
		
	################################################################################
	# INDIGO PLUGIN EVENTS
	################################################################################	
	
	#
	# Plugin startup
	#
	def startup(self):
		self.debugLog(u"Starting plugin")
		if self.cache is None: return
		
		if self.monitor: 
			if self.cache.pollingMode == "realTime": indigo.devices.subscribeToChanges()
		
		# Add all sub device variables that our plugin links to, reloading only on the last one
		#self.cache.addSubDeviceVar ("weathersnoop", False) # Add variable, don't reload cache
		#self.cache.addSubDeviceVar ("irrigation") # Add variable, reload cache
		
		# Not adding any sub device variables, reload the cache manually
		self.cache.cacheDevices()
		
		#self.cache.dictDump (self.cache.devices)
		
		return
		
	#	
	# Plugin shutdown
	#
	def shutdown(self):
		self.debugLog(u"Plugin shut down")	
	
	#
	# Concurrent thread
	#
	def runConcurrentThread(self):
		if self.cache is None:
			try:
				while True:
					self.sleep(1)
					if self.reload: break
			except self.StopThread:
				pass
			
			# Only happens if we break out due to a restart command
			serverPlugin = indigo.server.getPlugin(self.pluginId)
			serverPlugin.restart(waitUntilDone=False)
				
			return
		
		try:
			while True:
				if self.cache.pollingMode == "realTime" or self.cache.pollingMode == "pollDevice":
					self.onRunConcurrentThread()
					self.sleep(1)
					if self.reload: break
				else:
					self.onRunConcurrentThread()
					self.sleep(self.cache.pollingInterval)
					if self.reload: break
					
				# Only happens if we break out due to a restart command
				serverPlugin = indigo.server.getPlugin(self.pluginId)
         		serverPlugin.restart(waitUntilDone=False)
		
		except self.StopThread:
			pass	# Optionally catch the StopThread exception and do any needed cleanup.
			
			
	################################################################################
	# INDIGO DEVICE EVENTS
	################################################################################
	
	#
	# Dimmer/relay actions
	#
	def actionControlDimmerRelay(self, action, dev):
		if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "on"))
				dev.updateStateOnServer("onOffState", True)
			else:
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "on"), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "off"))
				dev.updateStateOnServer("onOffState", False)
			else:
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "off"), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.Toggle:
			newOnState = not dev.onState
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "toggle"))
				dev.updateStateOnServer("onOffState", newOnState)
			else:
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "toggle"), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.SetBrightness:
			newBrightness = action.actionValue
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "set brightness", newBrightness))
				dev.updateStateOnServer("brightnessLevel", newBrightness)
			else:
				indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "set brightness", newBrightness), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.BrightenBy:
			newBrightness = dev.brightness + action.actionValue
			if newBrightness > 100:
				newBrightness = 100
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "brighten", newBrightness))
				dev.updateStateOnServer("brightnessLevel", newBrightness)
			else:
				indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "brighten", newBrightness), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.DimBy:
			newBrightness = dev.brightness - action.actionValue
			if newBrightness < 0:
				newBrightness = 0
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "dim", newBrightness))
				dev.updateStateOnServer("brightnessLevel", newBrightness)
			else:
				indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "dim", newBrightness), isError=True)
	
	################################################################################
	# INDIGO PLUGIN UI EVENTS
	################################################################################	
	
	#
	# Plugin config pre-save event
	#
	def validatePrefsConfigUi(self, valuesDict):
		self.debugLog(u"%s is validating plugin config UI" % self.pluginDisplayName)
		return (True, valuesDict)
		
	#
	# Plugin config button clicked event
	#
	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		self.debugLog(u"%s is closing plugin config UI" % self.pluginDisplayName)
		
		if userCancelled == False:
			if "debugMode" in valuesDict:
				self.debug = valuesDict["debugMode"]
		
		return
			
	#
	# Stop concurrent thread
	#
	def stopConcurrentThread(self):
		self.debugLog(u"Plugin stopping concurrent threads")	
		self.stopThread = True
		
	#
	# Delete
	#
	def __del__(self):
		self.debugLog(u"Plugin delete")	
		indigo.PluginBase.__del__(self)
		
	
	################################################################################
	# PLUGIN SPECIFIC ROUTINES
	################################################################################	
	
	#
	# Check for device timeout and reset
	#
	def checkDeviceTimeout (self):
		try:
			for dev in indigo.devices.iter(self.pluginId):
				if eps.valueValid (dev.states, "resetTime", True):
					d = datetime.datetime.strptime (dev.states["resetTime"], "%Y-%m-%d %H:%M:%S")
					diff = dtutil.DateDiff ("seconds", d, indigo.server.getTime())
					if diff < 0: 
						# Don't waste processing time if it's already cleared
						ui = " "
						if dev.deviceTypeId == "dimmerKeypad": ui = eps.getDictValue (dev.pluginProps, "brightnessUI", " ")
						if dev.deviceTypeId == "sprinklerKeypad": 
							ui = eps.getDictValue (dev.pluginProps, "deviceUI", " ")
							
							# If only one device, don't ever prompt for a device
							if eps.valueValid (dev.pluginProps, "device2", True) == False and eps.valueValid (dev.pluginProps, "device3", True) == False:
								ui = eps.getDictValue (dev.pluginProps, "zone1SelectedUI", " ")
						
						if ui == "": ui = " "
						
						if dev.states["keyCache"] != "" or dev.states["keyCache.ui"] != ui: 
							self.debugLog("Device '%s' timeout reached, resetting device" % dev.name)
							self.deviceReset (dev)
					
				else:
					# It's blank, set it now
					dev.updateStateOnServer ("resetTime", indigo.server.getTime().strftime("%Y-%m-%d %H:%M:%S"))
					
				if dev.deviceTypeId == "securityKeypad" and dev.states["lockOutActive"]:
					d = datetime.datetime.strptime (dev.states["lockOut"], "%Y-%m-%d %H:%M:%S")
					diff = dtutil.DateDiff ("seconds", d, indigo.server.getTime())
					if diff >= 0: 
						ui = dtutil.secondsToClock (diff, "mm:ss")
						dev.updateStateOnServer ("statedisplay", "LOCKED " + ui)
					else:
						dev.updateStateOnServer ("lockOutActive", False)
						dev.updateStateOnServer ("statedisplay", "Ready")
						
			
		except Exception as e:
			eps.printException(e)
				
		return
		
	#
	# Set the device timeout
	#
	def setDeviceTimeout (self, dev, seconds):
		try:
			d = indigo.server.getTime()
			d = dtutil.DateAdd ("seconds", seconds, d)
			dev.updateStateOnServer ("resetTime", d.strftime("%Y-%m-%d %H:%M:%S"))
		
		except Exception as e:
			eps.printException(e)
		
	
	#
	# Device action: Delete character (backspace)
	#
	def delCharacter (self, devAction):
		try:
			dev = indigo.devices[devAction.deviceId]
			if dev.states["keyCache"] == "": return
			
			cache = dev.states["keyCache"]
			ui = dev.states["keyCache.ui"]
			
			cache = cache[:-1]
			ui = ui[:-1]
			
			if ui == "": 
				ui = ""
				self.deviceReset (dev)
				return
			
			dev.updateStateOnServer ("keyCache", cache, uiValue=ui)
			
			
		except Exception as e:
			eps.printException(e)
			
	#
	# Device action: Send character
	#
	def sendCharacter (self, devAction):
		try:
			dev = indigo.devices[devAction.deviceId]
			
			if dev.deviceTypeId == "securityKeypad": self.sendCharacter_Security(dev, devAction.props["key"])
			if dev.deviceTypeId == "dimmerKeypad": self.sendCharacter_Dimmer(dev, devAction)
			if dev.deviceTypeId == "sprinklerKeypad": self.sendCharacter_Sprinkler (dev, devAction)
		
		except Exception as e:
			eps.printException(e)
			
	#
	# Device action: Next field - 1.1
	#
	def nextField (self, devAction):
		try:
			dev = indigo.devices[devAction.deviceId]
			
			# In case they use this command on a non-compatible device, redirect
			if dev.deviceTypeId == "securityKeypad": self.sendCharacter (devAction)
			if dev.deviceTypeId == "dimmerKeypad": self.sendCharacter (devAction)
			
			if dev.deviceTypeId == "sprinklerKeypad": 
				# Next indicates they are switching zones
				zoneNum = 0
				for i in range (1, 9):
					if dev.states["onZone" + str(i)]:
						zoneNum = i
						break
				
				if zoneNum == 1 and eps.valueValid (dev.pluginProps, "device2", True) == False and eps.valueValid (dev.pluginProps, "device3", True) == False:
					# Failsafe in case they didn't enter a duration for zone 1 and cause the timer to start for 2 minutes
					self.setDeviceTimeout(dev, 120)
				
				self.saveSchedule (dev)
						
				if zoneNum > 0:
					zoneNum = zoneNum + 1
					if zoneNum > 8: zoneNum = 1
					
					self.debugLog("Change to zone %i" % zoneNum)
					self.setSprinklerZone (dev, zoneNum)
		
			
		except Exception as e:
			eps.printException(e)
			
	#
	# Save current cache into sprinkler schedule
	#
	def saveSchedule (self, dev):
		try:
			# Next indicates they are switching zones
			zoneNum = 0
			for i in range (1, 9):
				if dev.states["onZone" + str(i)]:
					zoneNum = i
					break
					
			# Set the duration of this zone before we switch zones
			deviceNumber = 0
			for y in range (1, 3):
				if dev.states["onDevice" + str(y)]:
					deviceNumber = y
					break

			cache = dev.states["keyCache"] # so we can save this zone duration
			if cache == "": cache = "0"
			cache = int(cache)
			
			schedule = ast.literal_eval(dev.states["device" + str(deviceNumber) + "Schedule"])	
			self.debugLog ("Old schedule is %s" % unicode(schedule))
			newSchedule = schedule
			newSchedule[zoneNum - 1] = cache
			
			# Save the new schedule
			self.debugLog ("New schedule is %s" % unicode(newSchedule))
			dev.updateStateOnServer ("device" + str(deviceNumber) + "Schedule", unicode(newSchedule))
			dev.updateStateOnServer ("keyCache", "", uiValue=" ") # Clear the cache for the next zone
			
		except Exception as e:
			eps.printException(e)
			
	#
	# Device action: Cancel - 1.1
	#
	def cancelCode (self, devAction):
		try:
			dev = indigo.devices[devAction.deviceId]
			self.deviceReset (dev)
			
		except Exception as e:
			eps.printException(e)
	
	#
	# Sprinkler character
	#
	def sendCharacter_Sprinkler (self, dev, devAction):
		try:
			cache = dev.states["keyCache"] + devAction.props["key"]
			
			# Catch special phrases so we don't error out
			for i in range (1, 9):
				deviceNum = 0
				zoneNum = 0
				
				if cache.lower() == "#dev" + str(i): deviceNum = i
				if cache.lower() == "#zone" + str(i): deviceNum = i
				
				if deviceNum <> 0:
					self.setSprinklerDevice (dev, deviceNum)
					return
					
				if zoneNum <> 0:
					for y in range (1, 9):
						if y != i: dev.updateStateOnServer ("onZone" + str(i), False)
						
					dev.updateStateOnServer ("onZone" + str(i), True)
					self.setStatusMessage (dev, "zone" + str(i) + "SelectedUI")
					return
			
			# If we got here then we got an entry, determine if it's for a device, a zone or a duration
			isDevice = True
			
			for i in range (1, 4):
				if dev.states["onDevice" + str(i)]: 
					isDevice = False
					break
					
			# If no device then our entry is a device selection
			if isDevice:
				self.debugLog("No device is currently active, setting device")
				if int(cache) > 3: cache = "3" # can't select more than device 3
				self.setSprinklerDevice (dev, int(cache))
				return
			
			if eps.valueValid (dev.pluginProps, "device2", True) == False and eps.valueValid (dev.pluginProps, "device3", True) == False:
				# If only a single device then we need to set the timeout for two minutes like when we select a device
				self.setDeviceTimeout(dev, 120)
			
			# Since when we select a device it automatically selects zone 1 it's a duration	
			ui = cache
			dev.updateStateOnServer ("keyCache", cache, uiValue=ui)
						
			
		except Exception as e:
			eps.printException(e)
			
	
	#
	# Select sprinkler zone
	#
	def setSprinklerZone (self, dev, n):
		try:
			# Figure out which device we are on
			deviceNumber = 0
			for y in range (1, 3):
				if dev.states["onDevice" + str(y)]:
					deviceNumber = y
					break
				
			# Turn off all zones but this one
			for y in range (1, 9):
				if y != n: 
					self.debugLog("Turning off zone %i" % y)
					dev.updateStateOnServer ("onZone" + str(y), False)
				else:
					self.debugLog("Turning on zone %i" % y)
					dev.updateStateOnServer ("onZone" + str(y), True)
		
			# Set the status message to this zone
			schedule = ast.literal_eval(dev.states["device" + str(deviceNumber) + "Schedule"])	
			
			if schedule[n -1] != 0:
				# There is a schedule, flash the zone number for two seconds and then the duration
				dev.updateStateOnServer ("onZone" + str(n), True)
				self.setStatusMessage (dev, "zone" + str(n) + "SelectedUI", 0) 
				self.sleep(2) # give them two seconds to see the message that we changed devices
				dev.updateStateOnServer ("keyCache", str(schedule[n-1]), uiValue=str(schedule[n-1]))
			else:
				# No schedule, show the zone number
				self.setStatusMessage (dev, "zone" + str(n) + "SelectedUI", 0) 
				dev.updateStateOnServer ("keyCache", "", uiValue=dev.states["keyCache.ui"]) # so first key press clears the message
		
		except Exception as e:
			eps.printException(e)
			
	#
	# Select sprinkler device
	#
	def setSprinklerDevice (self, dev, n):
		try:
			# Turn off all devices but this one
			for y in range (1, 4):
				if y != n: dev.updateStateOnServer ("onDevice" + str(y), False)
				
			# Turn off all zones except zone 1 since we changed devices
			for y in range (1, 9):
				if y == 1: 
					dev.updateStateOnServer ("onZone" + str(y), True)
				else:
					dev.updateStateOnServer ("onZone" + str(y), False)
			
			# Let them know we changed devices
			dev.updateStateOnServer ("onDevice" + str(n), True)
			self.setStatusMessage (dev, "device" + str(n) + "SelectedUI", 10) 
			self.sleep(2) # give them two seconds to see the message that we changed devices
			
			# Prompt for the zone 1 time
			self.setStatusMessage (dev, "zone1SelectedUI", 120) # two minute timeout to complete schedule
			dev.updateStateOnServer ("keyCache", "", uiValue=dev.states["keyCache.ui"]) # so first key press clears the message
			
		except Exception as e:
			eps.printException(e)
	
	#
	# Dimmer character
	#
	def sendCharacter_Dimmer (self, dev, devAction):
		try:
			if eps.valueValid (devAction.props, "devicelist", True):
				self.debugLog ("Setting action based devices on %s" % dev.name)
				devlist = []
				
				for s in devAction.props["devicelist"]:
					devlist.append(s)
				
				dev.updateStateOnServer ("deviceList", unicode(devlist))
				return
		
			cache = dev.states["keyCache"] + devAction.props["key"]
			if int(cache) > 100: cache = "100"
			
			ui = cache
			n = int(eps.getDictValue(dev.pluginProps, "resetTime", 10))
			self.setDeviceTimeout (dev, n)
			
			dev.updateStateOnServer ("keyCache", cache, uiValue=ui)
			
			if len(cache) == 3: self.processCache (dev) # 3 characters is the most
		
		except Exception as e:
			eps.printException(e)
	
	#
	# Security character
	#
	def sendCharacter_Security (self, dev, key):
		try:
			
			
			# Make sure we aren't locked out
			if eps.valueValid (dev.states, "lockOut", True):
				d = datetime.datetime.strptime (dev.states["lockOut"], "%Y-%m-%d %H:%M:%S")
				diff = dtutil.DateDiff ("seconds", d, indigo.server.getTime())
				if diff >= 0: 
					indigo.server.log("Attempted to enter code on device %s but that device is in failed code lockout for %i more seconds" % (dev.name, diff), isError=True)
					msg = "L.OUT"
					secs = 5
					if secs > diff: secs = diff
					
					ui = eps.getDictValue (dev.pluginProps, "lockoutUI", "L.OUT")
					dev.updateStateOnServer ("keyCache", dev.states["keyCache"], uiValue=ui)
					self.setDeviceTimeout (dev, secs)
					
					return
					
				else:
					dev.updateStateOnServer ("lockOutActive", False)
					
			self.debugLog ("Keypad button %s pressed, adding to characters" % key)
		
			cache = dev.states["keyCache"] + key
			ui = ""
		
			n = int(eps.getDictValue(dev.pluginProps, "resetTime", 10))
			if dev.pluginProps["codeCharacter"] != "" and dev.pluginProps["codeCharacter"] != " ":
				for s in cache:
					ui += dev.pluginProps["codeCharacter"]
					
				self.setDeviceTimeout (dev, n)
				
			else:
				self.setDeviceTimeout (dev, n)
				ui = cache
		
			dev.updateStateOnServer ("keyCache", cache, uiValue=ui)
				
			self.processCache (dev)

		
		except Exception as e:
			eps.printException(e)
			
		
		return
		
	#
	# Device action: Send code complete
	#
	def sendComplete (self, devAction):
		try:
			dev = indigo.devices[devAction.deviceId]
		
			if dev.deviceTypeId == "securityKeypad":
				self.debugLog ("Sending %s as the final complete security code" % dev.states["keyCache"])
				self.processCache (dev, True)
				
			if dev.deviceTypeId == "dimmerKeypad":
				self.debugLog ("Sending %s as the brightness" % dev.states["keyCache"])
				self.processCache (dev)
				
			if dev.deviceTypeId == "sprinklerKeypad":
				msg = dev.states["device1Schedule"] + " | " + dev.states["device2Schedule"] + " | " + dev.states["device3Schedule"] 
				self.debugLog ("Sending %s as the sprinkler schedule(s)" % msg)
				self.processCache (dev)
		
		except Exception as e:
			eps.printException(e)
				
		return
		
	#
	# Process the code stored in cache
	#
	def processCache (self, dev, force = False):
		try:
			currentCode = dev.states["keyCache"]
			if currentCode == " ": currentCode = ""
			
			if dev.deviceTypeId == "securityKeypad":
				if dev.pluginProps["actionCode1"] != "" and currentCode == dev.pluginProps["actionCode1"]:
					self.debugLog("Automatically executing action 1")
					self.setStatusMessage (dev, "action1UI")
					self.runAction (dev, "action1")
					
				elif dev.pluginProps["actionCode2"] != "" and currentCode == dev.pluginProps["actionCode2"]:
					self.debugLog("Automatically executing action 2")
					self.setStatusMessage (dev, "action2UI")
					self.runAction (dev, "action2")
					
				elif dev.pluginProps["autoAcceptChars"] != "" and dev.pluginProps["autoAcceptChars"] != "0" and len(currentCode) >= int(dev.pluginProps["autoAcceptChars"]): 
					self.processCode(dev, currentCode)
					return
					
				elif force: 
					self.processCode(dev, currentCode)
					return
					
			elif dev.deviceTypeId == "dimmerKeypad":
				indigo.server.log("Setting brightness now")
				
				if eps.valueValid (dev.states, "deviceList", True):
					if dev.states["deviceList"] != "[]":
						# They sent devices
						devs = ast.literal_eval(dev.states["deviceList"])	
						
						if dev.pluginProps["deviceMethod"] == "replace":
							self.setBrightness (devs, dev, currentCode)

						elif dev.pluginProps["deviceMethod"] == "append":	
							self.setBrightness (devs, dev, currentCode)
							self.setBrightness (dev.pluginProps["devicelist"], dev, currentCode)	

						elif dev.pluginProps["deviceMethod"] == "ignore":	
							self.setBrightness (dev.pluginProps["devicelist"], dev, currentCode)	
								
					else:
						# Use the devices configure in props
						self.debugLog("Device list is empty")
						self.setBrightness (dev.pluginProps["devicelist"], dev, currentCode)	
						
				self.setStatusMessage (dev, "completedUI")
				
				return
				
			elif dev.deviceTypeId == "sprinklerKeypad":
				self.saveSchedule (dev)
				
				for i in range (1, 4):
					idx = str(i)
					if i == 1: idx = ""
									
					if eps.valueValid (dev.pluginProps, "device" + idx, True):
						devEx = indigo.devices[int(dev.pluginProps["device" + idx])]
						if idx == "": idx = "1"
						schedule = ast.literal_eval(dev.states["device" + idx + "Schedule"])
					
						self.runSprinklerSchedule (dev, devEx, schedule, i)
					
				self.setStatusMessage (dev, "completedUI")
				
				return	
			
		except Exception as e:
			eps.printException(e)
			
	#
	# Run a sprinkler schedule
	#
	def runSprinklerSchedule (self, dev, devEx, schedule, deviceNum):
		try:
			deviceNum = str(deviceNum)
			
			if devEx.states["activeZone"] != 0:
				self.debugLog("Sprinkler device %s is running, stopping it" % devEx.name)
				if dev.pluginProps["runningAction"] == "replace":
					 indigo.sprinkler.stop(devEx.id)
				
				if dev.pluginProps["runningAction"] == "add":
					runDict = devEx.zoneScheduledDurations
					if len(runDict) == 0: runDict = devEx.zoneMaxDurations # they aren't running a schedule
				
					d = indigo.server.getTime()
					start = datetime.datetime.strptime (dev.states["device" + deviceNum + "ZoneOn"], "%Y-%m-%d %H:%M:%S")
					diff = dtutil.DateDiff ("minutes", d, start)
					
					self.debugLog("Running zone has been running for %s minutes" % str(diff))
					
					if len(runDict) > 0:
						for i in range (0, 8): 
							if i > (devEx.states["activeZone"] - 1): schedule[i] = runDict[i] + schedule[i]
							if i == (devEx.states["activeZone"] - 1):	schedule[i] = schedule[i] + (runDict[i] - diff)
						
					indigo.sprinkler.stop(devEx.id)
			
			self.debugLog("Turning on %s with schedule %s" % (devEx.name, unicode(schedule)))
			indigo.sprinkler.run(devEx.id, schedule=schedule)
			
					
		except Exception as e:
			eps.printException(e)
	
	#
	# Loop through devices and set brightness
	#
	def setBrightness (self, devlist, dev, currentCode):
		for devId in devlist:
			devChild = indigo.devices[int(devId)]
			
			if eps.valueValid (devChild.states, "brightnessLevel") == False:
				indigo.server.log ("Cannot set the brightness on %s because it is not a dimmer" % devChild.name, isError=True)
				continue
				
			cur = devChild.states["brightnessLevel"]
			new = int(currentCode)
			
			if new == 0:
				indigo.dimmer.turnOff(devChild.id)
			elif new == 100:
				indigo.dimmer.turnOn(devChild.id)
			else:				
				indigo.dimmer.setBrightness(devChild.id, value=new)
			
	#
	# Process completed code
	#
	def processCode (self, dev, code):
		try:
			self.debugLog("Processing code %s" % code)
			
			if code != dev.pluginProps["securityCode"]:
				attempts = dev.states["currentAttempts"] + 1
				indigo.server.log("Incorrect code of %s entered on %s, attempt %i" % (code, dev.name, attempts), isError=True)
				
				if dev.pluginProps["failAttempts"] != "":
					if attempts >= int(dev.pluginProps["failAttempts"]):
						indigo.server.log("Too many failed attempts on %s" % dev.name, isError=True)
						self.runAction (dev, "fail")
						dev.updateStateOnServer ("currentAttempts", 0)
						self.setStatusMessage (dev, "failUI")
						d = indigo.server.getTime()
						d = dtutil.DateAdd ("seconds", int(eps.getDictValue (dev.pluginProps, "failLockout", 30)), d)
						dev.updateStateOnServer ("lockOut", d.strftime("%Y-%m-%d %H:%M:%S"))
						dev.updateStateOnServer ("lockOutActive", True)
						
					else:				
						dev.updateStateOnServer ("currentAttempts", attempts)
						#
						self.setStatusMessage (dev, "incorrectUI", 60)
						dev.updateStateOnServer ("keyCache", "", uiValue=dev.states["keyCache.ui"]) # so first key press clears the message
						dev.updateStateOnServer ("statedisplay", "Bad Code #%i" % attempts)
						self.runAction (dev, "incorrect")
			
			else:
				self.setStatusMessage (dev, "successUI")
				self.runAction (dev)
				
							
			#dev.updateStateOnServer ("keyCache", "", uiValue=ui) # Clear the code
			X=1	
		
		except Exception as e:
			eps.printException(e)
	
	#
	# Set final status message on device
	#
	def setStatusMessage (self, dev, key, seconds=3):
		try:
			ui = eps.getDictValue (dev.pluginProps, key, " ")
			self.debugLog ("Setting status message on %s to '%s'" % (dev.name, ui))
			dev.updateStateOnServer ("keyCache", dev.states["keyCache"], uiValue=ui)
			if seconds > 0: self.setDeviceTimeout (dev, seconds)
		
		except Exception as e:
			eps.printException(e)
				
	#
	# Reset the device
	#
	def deviceReset (self, dev):
		try:
			self.debugLog ("Resetting %s" % dev.name)
			
			if dev.deviceTypeId == "securityKeypad":
				dev.updateStateOnServer ("keyCache", "", uiValue=" ") # Clear the code
				dev.updateStateOnServer ("currentAttempts", 0) # Clear attempts
				
				if dev.states["lockOutActive"] == False: dev.updateStateOnServer ("statedisplay", "Ready")
				
			if dev.deviceTypeId == "dimmerKeypad":
				ui = eps.getDictValue (dev.pluginProps, "brightnessUI", " ")
				dev.updateStateOnServer ("keyCache", "", uiValue=ui) # Clear the code
				#dev.updateStateOnServer ("deviceList", "[]") # Clear the additional devices
		
				dev.updateStateOnServer ("statedisplay", "Ready")
				
			if dev.deviceTypeId == "sprinklerKeypad":
				# Reset devices 2-3 since 1 has already been handled
				for i in range (2, 4): 
					dev.updateStateOnServer ("onDevice" + str(i), False)
					dev.updateStateOnServer ("device" + str(i) + "Schedule", "[0,0,0,0,0,0,0,0]")
					
				for i in range (1, 9): dev.updateStateOnServer ("onZone" + str(i), False)
								
				ui = eps.getDictValue (dev.pluginProps, "deviceUI", " ")
				
				# If only one device, always reset for device 1
				if eps.valueValid (dev.pluginProps, "device2", True) == False and eps.valueValid (dev.pluginProps, "device3", True) == False:
					ui = eps.getDictValue (dev.pluginProps, "zone1SelectedUI", " ")
					dev.updateStateOnServer ("onDevice1", True)
					dev.updateStateOnServer ("onZone1", True) # since there is no device selection that will auto select it
				else:
					dev.updateStateOnServer ("onDevice1", False)
									
				dev.updateStateOnServer ("keyCache", "", uiValue=ui) # Clear the code
				dev.updateStateOnServer ("device1Schedule", "[0,0,0,0,0,0,0,0]")
				
				dev.updateStateOnServer ("statedisplay", "Ready")
		
		except Exception as e:
			eps.printException(e)
			
			
	#
	# Run action
	#
	def runAction (self, dev, prefix="success"):
		try:
			if dev.ownerProps[prefix + "Type"] == "action" and dev.ownerProps[prefix + "Action"] != "": indigo.actionGroup.execute(int(dev.ownerProps[prefix + "Action"]))
			if dev.ownerProps[prefix + "Type"] == "device" and dev.ownerProps[prefix + "Device"] != "": 
				if dev.ownerProps[prefix + "DeviceAction"] == "on": indigo.device.turnOn(int(dev.ownerProps[prefix + "Device"]))
				if dev.ownerProps[prefix + "DeviceAction"] == "off": indigo.device.turnOff(int(dev.ownerProps[prefix + "Device"]))
				if dev.ownerProps[prefix + "DeviceAction"] == "toggle": indigo.device.toggle(int(dev.ownerProps[prefix + "Device"]))
			if dev.ownerProps[prefix + "Type"] == "variable" and dev.ownerProps[prefix + "Variable"] != "": indigo.variable.updateValue(int(dev.ownerProps[prefix + "Variable"]), value=dev.ownerProps[prefix + "successVariableValue"])
			if dev.ownerProps[prefix + "Type"] == "schedule" and dev.ownerProps[prefix + "ScheduleAction"] != "": 
				if dev.ownerProps[prefix + "ScheduleAction"] == "enable": indigo.actionGroup.execute(int(dev.ownerProps[prefix + "Schedule"]))
				if dev.ownerProps[prefix + "ScheduleAction"] == "disable": indigo.actionGroup.execute(int(dev.ownerProps[prefix + "Schedule"]))
						
		except Exception as e:
			eps.printException(e)
	
	
	################################################################################
	# SUPPORT DEBUG ROUTINE
	################################################################################	
	
	#
	# Plugin menu: Support log
	#
	def supportLog (self):
		self.showLibraryVersions ()
		
		s = eps.debugHeader("SUPPORT LOG")
		
		# Get plugin prefs
		s += eps.debugHeader ("PLUGIN PREFRENCES", "=")
		for k, v in self.pluginPrefs.iteritems():
			s += eps.debugLine(k + " = " + unicode(v), "=")
			
		s += eps.debugHeaderEx ("=")
		
		# Report on cache
		s += eps.debugHeader ("DEVICE CACHE", "=")
		
		for devId, devProps in self.cache.devices.iteritems():
			s += eps.debugHeaderEx ("*")
			s += eps.debugLine(devProps["name"] + ": " + str(devId) + " - " + devProps["deviceTypeId"], "*")
			s += eps.debugHeaderEx ("*")
			
			s += eps.debugHeaderEx ("-")
			s += eps.debugLine("SUBDEVICES", "-")
			s += eps.debugHeaderEx ("-")
			
			for subDevId, subDevProps in devProps["subDevices"].iteritems():
				s += eps.debugHeaderEx ("+")
				s += eps.debugLine(subDevProps["name"] + ": " + str(devId) + " - " + subDevProps["deviceTypeId"] + " (Var: " + subDevProps["varName"] + ")", "+")
				s += eps.debugHeaderEx ("+")
				
				s += eps.debugLine("WATCHING STATES:", "+")
				
				for z in subDevProps["watchStates"]:
					s += eps.debugLine("     " + z, "+")
					
				s += eps.debugHeaderEx ("+")
					
				s += eps.debugLine("WATCHING PROPERTIES:", "+")
				
				for z in subDevProps["watchProperties"]:
					s += eps.debugLine("     " + z, "+")
					
				if subDevId in indigo.devices:
					d = indigo.devices[subDevId]
					if d.pluginId != self.pluginId:
						s += eps.debugHeaderEx ("!")
						s += eps.debugLine(d.name + ": " + str(d.id) + " - " + d.deviceTypeId, "!")
						s += eps.debugHeaderEx ("!")
					
						s += eps.debugHeaderEx ("-")
						s += eps.debugLine("PREFERENCES", "-")
						s += eps.debugHeaderEx ("-")
			
						for k, v in d.pluginProps.iteritems():
							s += eps.debugLine(k + " = " + unicode(v), "-")
				
						s += eps.debugHeaderEx ("-")
						s += eps.debugLine("STATES", "-")
						s += eps.debugHeaderEx ("-")
			
						for k, v in d.states.iteritems():
							s += eps.debugLine(k + " = " + unicode(v), "-")
						
						s += eps.debugHeaderEx ("-")
						s += eps.debugLine("RAW DUMP", "-")
						s += eps.debugHeaderEx ("-")
						s += unicode(d) + "\n"
				
						s += eps.debugHeaderEx ("-")
					else:
						s += eps.debugHeaderEx ("!")
						s += eps.debugLine("Plugin Device Already Summarized", "+")
						s += eps.debugHeaderEx ("!")
				else:
					s += eps.debugHeaderEx ("!")
					s += eps.debugLine("!!!!!!!!!!!!!!! DEVICE DOES NOT EXIST IN INDIGO !!!!!!!!!!!!!!!", "+")
					s += eps.debugHeaderEx ("!")
				
			s += eps.debugHeaderEx ("-")
		
		
		s += eps.debugHeaderEx ("=")
		
		# Loop through all devices for this plugin and report
		s += eps.debugHeader ("PLUGIN DEVICES", "=")
		
		for dev in indigo.devices.iter(self.pluginId):
			s += eps.debugHeaderEx ("*")
			s += eps.debugLine(dev.name + ": " + str(dev.id) + " - " + dev.deviceTypeId, "*")
			s += eps.debugHeaderEx ("*")
			
			s += eps.debugHeaderEx ("-")
			s += eps.debugLine("PREFERENCES", "-")
			s += eps.debugHeaderEx ("-")
			
			for k, v in dev.pluginProps.iteritems():
				s += eps.debugLine(k + " = " + unicode(v), "-")
				
			s += eps.debugHeaderEx ("-")
			s += eps.debugLine("STATES", "-")
			s += eps.debugHeaderEx ("-")
			
			for k, v in dev.states.iteritems():
				s += eps.debugLine(k + " = " + unicode(v), "-")
				
			s += eps.debugHeaderEx ("-")
			
		s += eps.debugHeaderEx ("=")
		
		
		
		
		indigo.server.log(s)

	################################################################################
	# UPDATE CHECKS
	################################################################################

	def updateCheck (self, onlyNewer = False, force = True):
		try:
			try:
				if self.pluginUrl == "": 
					if force: indigo.server.log ("This plugin currently does not check for newer versions", isError = True)
					return
			except:
				# Normal if pluginUrl hasn't been defined
				if force: indigo.server.log ("This plugin currently does not check for newer versions", isError = True)
				return
			
			d = indigo.server.getTime()
			
			if eps.valueValid (self.pluginPrefs, "latestVersion") == False: self.pluginPrefs["latestVersion"] = False
			
			if force == False and eps.valueValid (self.pluginPrefs, "lastUpdateCheck", True):
				last = datetime.datetime.strptime (self.pluginPrefs["lastUpdateCheck"], "%Y-%m-%d %H:%M:%S")
				lastCheck = dtutil.DateDiff ("hours", d, last)
								
				if self.pluginPrefs["latestVersion"]:
					if lastCheck < 72: 
						return # if last check has us at the latest then only check once every 3 days
				else:
					if lastCheck < 2: 
						return # only check every four hours in case they don't see it in the log
			
			self.debugLog("Checking for updates")
			
			page = urllib2.urlopen(self.pluginUrl)
			soup = BeautifulSoup(page)
		
			versions = soup.find(string=re.compile("\#Version\|"))
			versionData = unicode(versions)
		
			versionInfo = versionData.split("#Version|")
			newVersion = float(versionInfo[1][:-1])
		
			if newVersion > float(self.pluginVersion):
				self.pluginPrefs["latestVersion"] = False
				indigo.server.log ("Version %s of %s is available, you are currently using %s." % (str(round(newVersion,2)), self.pluginDisplayName, str(round(float(self.pluginVersion), 2))), isError=True)
			
			else:
				self.pluginPrefs["latestVersion"] = True
				if onlyNewer == False: indigo.server.log("%s version %s is the most current version of the plugin" % (self.pluginDisplayName, str(round(float(self.pluginVersion), 2))))
				
			self.pluginPrefs["lastUpdateCheck"] = d.strftime("%Y-%m-%d %H:%M:%S")
			
				
		except Exception as e:
			eps.printException(e)
		
	################################################################################
	# LEGACY MIGRATED ROUTINES
	################################################################################
	


	

	
