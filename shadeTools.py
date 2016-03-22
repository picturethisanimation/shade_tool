# asset publish
#Import python modules
import sys, os
import subprocess
from datetime import datetime

from functools import partial

#Import GUI
from qtshim import QtCore, QtGui
from qtshim import Signal
from qtshim import wrapinstance

from tool.shade import ui as ui
reload(ui)

moduleDir = sys.modules[__name__].__file__

from tool.utils import pipelineTools, fileUtils, entityInfo, projectInfo
reload(pipelineTools)
reload(fileUtils)
reload(projectInfo)

from tool.utils import entityInfo2 as entityInfo
reload(entityInfo)

# logger 
from tool.utils import customLog
reload(customLog)

scriptName = 'ptShadeTools'
logger = customLog.customLog()
logger.setLevel(customLog.DEBUG)
logger.setLogName(scriptName)

#Import maya commands
import maya.cmds as mc
import maya.mel as mm
import maya.OpenMayaUI as mui


# If inside Maya open Maya GUI
def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if ptr is None:
        raise RuntimeError('No Maya window found.')
    window = wrapinstance(ptr)
    assert isinstance(window, QtGui.QMainWindow)
    return window


class MyForm(QtGui.QMainWindow):

	def __init__(self, parent=None):
		self.count = 0
		#Setup Window
		super(MyForm, self).__init__(parent)
		# QtGui.QWidget.__init__(self, parent)
		self.ui = ui.Ui_AssetPublishWin()
		self.ui.setupUi(self)
		self.setWindowTitle('PT Asset Publish v.1.0')

		# icons 
		self.logo = '%s/%s' % (os.path.dirname(moduleDir), 'icons/logo.png')
		self.logo2 = '%s/%s' % (os.path.dirname(moduleDir), 'icons/alembic_logo.png')
		self.okIcon = '%s/%s' % (os.path.dirname(moduleDir), 'icons/ok_icon.png')
		self.xIcon = '%s/%s' % (os.path.dirname(moduleDir), 'icons/x_icon.png')
		self.rdyIcon = '%s/%s' % (os.path.dirname(moduleDir), 'icons/rdy_icon.png')
		self.ipIcon = '%s/%s' % (os.path.dirname(moduleDir), 'icons/ip_icon.png')
		self.refreshIcon = '%s/%s' % (os.path.dirname(moduleDir), 'icons/refresh_icon.png')
		self.mayaIcon = '%s/%s' % (os.path.dirname(moduleDir), 'icons/maya_icon.png')
		self.iconPath = '%s/icons' % os.path.dirname(moduleDir)
		self.sgStatusIcon = {'Approved':'%s/green_icon.png' % self.iconPath, 'Pending Client':'%s/yellow_icon.png' % self.iconPath, 'Pending Internal':'%s/red_icon.png' % self.iconPath, 'Review':'%s/daily_icon.png' % self.iconPath}
		self.sgStatusMap = {'Approved':'aprv', 'Pending Client':'intapr', 'Pending Internal':'noapr', 'Review':'daily'}
		self.iconSize = 15
		self.w = 1280
		self.h = 1024