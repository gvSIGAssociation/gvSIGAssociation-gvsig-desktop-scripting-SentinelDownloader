# encoding: utf-8

import gvsig

import os.path

from os.path import join, dirname

from gvsig import currentView
from gvsig import currentLayer

from java.io import File

from org.gvsig.app import ApplicationLocator
from org.gvsig.andami import PluginsLocator
from org.gvsig.scripting.app.extension import ScriptingExtension
from org.gvsig.tools.swing.api import ToolsSwingLocator
  
from org.gvsig.tools import ToolsLocator

from xmlSentinelReader import SentinelSearchPanel

class SentinelDownloaderExtension(ScriptingExtension):
  def __init__(self):
    pass

  def isVisible(self):
    return True

  def isLayerValid(self, layer):
    #if layer == None:
    #  #print "### reportbypointExtension.isLayerValid: None, return False"
    #  return False
    #mode = layer.getProperty("reportbypoint.mode")
    #if mode in ("", None):
    #  # Si la capa no tiene configurado el campo a mostrar
    #  # no activamos la herramienta
    #  return False
    return True
    
  def isEnabled(self):
    #layer = currentLayer()
    #if not self.isLayerValid(layer):
    #  return False
    return True

  def execute(self,actionCommand, *args):
    actionCommand = actionCommand.lower()
    if actionCommand == "settool-sentineldownloader":
      #print "### QuickinfoExtension.execute(%s)" % repr(actionCommand)
      layer = currentLayer()
      if not self.isLayerValid(layer):
        return
      viewPanel = currentView().getWindowOfView()
      mapControl = viewPanel.getMapControl()
      sentineldownloader = SentinelSearchPanel()
      sentineldownloader.setToolMapControl(mapControl)
      sentineldownloader.showTool("Sentinel Search Panel")

def selfRegister():
  i18n = ToolsLocator.getI18nManager()
  application = ApplicationLocator.getManager()
  actionManager = PluginsLocator.getActionInfoManager()
  iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()

  quickinfo_icon = File(gvsig.getResource(__file__,"images","sentineldownloader.png")).toURI().toURL()
  iconTheme.registerDefault("scripting.sentineldownloader", "action", "tools-sentineldownloader", None, quickinfo_icon)

  reportbypoint_extension = SentinelDownloaderExtension()
  reportbypoint_action = actionManager.createAction(
    reportbypoint_extension,
    "tools-sentineldownloader",   # Action name
    "Sentinel Downloader",   # Text
    "settool-sentineldownloader", # Action command
    "tools-sentineldownloader",   # Icon name
    None,                # Accelerator
    1009000000,          # Position
    i18n.getTranslation("_Sentinel_Downloader")    # Tooltip
  )
  reportbypoint_action = actionManager.registerAction(reportbypoint_action)
  application.addMenu(reportbypoint_action, "tools/_Sentinel_Downloader")
  application.addSelectableTool(reportbypoint_action, "SentinelDownloader")

def main(*args):
  selfRegister()
  