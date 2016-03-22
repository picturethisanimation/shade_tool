#Import python modules
import os, sys
from functools import partial
import sqlite3
from collections import Counter

#Import GUI
from PySide import QtCore
from PySide import QtGui
from PySide import QtUiTools
from shiboken import wrapInstance

# Import Maya module
import maya.OpenMayaUI as mui
import maya.cmds as mc
import maya.mel as mm

# import pipeline modules 
from tool.utils import mayaTools, pipelineTools, fileUtils
from tool.utils import entityInfo2 as entityInfo
from tool.utils import projectInfo
from tool.utils.vray import vray_utils as vr
from tool.ptAlembic import abcUtils
reload(projectInfo)
reload(vr)
reload(entityInfo)
reload(fileUtils)
reload(pipelineTools)
reload(abcUtils)

from tool.matte import create_db as db
reload(db)

from tool.shade import save_render
reload(save_render)

moduleFile = sys.modules[__name__].__file__
moduleDir = os.path.dirname(moduleFile)
sys.path.append(moduleDir)


def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    if ptr is not  None:
        # ptr = mui.MQtUtil.mainWindow()
        return wrapInstance(long(ptr), QtGui.QMainWindow)

class MyForm(QtGui.QMainWindow):

    def __init__(self, parent=None):
        self.count = 0
        #Setup Window
        super(MyForm, self).__init__(parent)

        self.mayaUI = 'shadeToolWin'
        deleteUI(self.mayaUI)

        # read .ui directly
        loader = QtUiTools.QUiLoader()
        loader.setWorkingDirectory(moduleDir)

        f = QtCore.QFile("%s/ui.ui" % moduleDir)
        f.open(QtCore.QFile.ReadOnly)

        self.myWidget = loader.load(f, self)
        self.ui = self.myWidget

        f.close()

        self.ui.show()
        self.ui.setWindowTitle('PT Shade Tool v.1.0')

        # ===============================================

        # icons 
        self.okIcon = '%s/icons/%s' % (moduleDir, 'ok_icon.png')
        self.xIcon = '%s/icons/%s' % (moduleDir, 'x_icon.png')

        # variable 

        self.lookDevPresetPath = "P:/Library/studioPresets/lookdev/VRaySettingsNodePreset/VRaySettingsNodePreset_lookdev.mel"
        self.lightRig = 'P:/Library/studioPresets/lookdev/lightRig'
        self.turnTableCamera = 'P:/Library/studioPresets/lighting/default/camera/TT.ma'
        self.lineup = 'P:/Library/studioPresets/lookdev/lineup/frd_lineup.ma'

        self.lightRigFiles = sorted(fileUtils.listFile(self.lightRig))

        self.selLightPath = str()

        self.setUI()
        self.initSignals()


    def setUI(self) : 
        self.ui.lowPreset_pushButton.setVisible(False)
        self.setLightComboBox()

        # disable alembic test
        self.ui.hData_pushButton.setEnabled(False)
        self.ui.importAbcTest_pushButton.setEnabled(False)
        self.ui.removeAbc_pushButton.setEnabled(False)


    def initSignals(self) : 
        # tech setup 
        # dev rig
        self.ui.devRig_pushButton.clicked.connect(self.doRefDevRig)
        # assign shader 
        self.ui.connectShade_pushButton.clicked.connect(self.doConnectShade)
        # clean Node 
        self.ui.cleanNode_pushButton.clicked.connect(self.runCleanNodes)
        # sync Info 
        self.ui.syncInfo_pushButton.clicked.connect(self.doSyncInfo)

        # matteID section 
        # shade renamer
        self.ui.shadeRename_pushButton.clicked.connect(self.runShadeRenamer)
        # matteID export 
        self.ui.matteID_pushButton.clicked.connect(self.runMatteIDExport)
        # vrayDisp  
        self.ui.vrayDisp_pushButton.clicked.connect(self.doCreateVrayDisp)
        # export vray node 
        self.ui.exportVrayNode_pushButton.clicked.connect(self.doExportVrayNodes)

        # hierarchy check 
        self.ui.hData_pushButton.clicked.connect(self.doSyncHData)
        self.ui.importAbcTest_pushButton.clicked.connect(self.doTestABC)
        self.ui.removeAbc_pushButton.clicked.connect(self.doRemoveABC)

        # preset 
        self.ui.vray_pushButton.clicked.connect(self.setPreset)
        self.ui.highPreset_pushButton.clicked.connect(self.setRenderAnimationPreset)

        # import light 
        self.ui.importLight_pushButton.clicked.connect(self.runImportLight)
        self.ui.removeLight_pushButton.clicked.connect(self.runRemoveLight)
        
        # lineup 
        self.ui.lineUp_pushButton.clicked.connect(self.runImportLineup)
        self.ui.removeLineup_pushButton.clicked.connect(self.runRemoveLineup)

        # create vray proxy
        self.ui.createVrayProxy_pushButton.clicked.connect(self.runVrayProxyTool)

        # render 
        self.ui.renderTest_pushButton.clicked.connect(self.doRenderStill)

        # save still
        self.ui.saveStill_pushButton.clicked.connect(partial(self.doSaveRenderImage, 'still'))
        self.ui.saveRender2_pushButton.clicked.connect(partial(self.doSaveRenderImage, 'lineup'))
        self.ui.saveRender3_pushButton.clicked.connect(partial(self.doSaveRenderImage, 'vrayProxy'))

        # publish 
        self.ui.publish_pushButton.clicked.connect(self.runAssetPublish)



    def runShadeRenamer(self) : 
        from tool.matte import shadeNamer_app as app
        reload(app)

        myApp = app.MyApp()
        myApp.show()


    def runMatteIDExport(self) : 
        from tool.matte import matteExport_app as app
        reload(app)
        myApp = app.MyForm(app.getMayaWindow())


    def runAssetPublish(self) : 
        import maya.cmds as mc
        from tool.publish.asset import assetPublish_app as app
        reload(app)

        if mc.window('AssetPublishWin', exists = True) : 
            mc.deleteUI('AssetPublishWin')
            
        myApp = app.MyForm(app.getMayaWindow())
        myApp.show()


    def runImportLight(self, arg = None) : 
        title = 'Light Template'
        allRefs = mc.file(q = True, r = True)
        rigGrp = 'Rig:Geo_Grp'
        selLight = str(self.ui.light_comboBox.currentText())
        self.selLightPath = '%s/%s' % (self.lightRig, selLight)

        if not mc.objExists('Light_Grp') : 
            if not self.selLightPath in allRefs : 
                mc.file(self.selLightPath,r=True, uns=True, dns=True )
            
            mc.setAttr( "vraySettings.relements_usereferenced", 1)

        else : 
            self.messageBox('Warning', 'Light Rig Exists')

        if not mc.objExists('cam_grp') : 
            if not self.turnTableCamera in allRefs : 
                mc.file(self.turnTableCamera, r=True, uns=True, dns=True)

            mc.playbackOptions( min=1 ) 
            mc.playbackOptions( max=100 ) 
            mc.lookThru('turntable_cam')
            mc.setAttr('turntable_camShape.renderable', 1)
            allCams = mc.listCameras()

            for eachCam in allCams : 
                shape = mc.listRelatives(eachCam, s = True)[0]
                mc.setAttr('%s.renderable' % shape, 0)

                if eachCam == 'turntable_cam' : 
                    mc.setAttr('%s.renderable' % shape, 1)
                    mc.setAttr('%s.displayFieldChart' % shape, 1)
                    mc.setAttr('%s.displayResolution' % shape, 1)
                    mc.setAttr('%s.overscan' % shape, 1.3)
                    mc.setAttr('%s.backgroundColor' % shape, 0.5, 0.5, 0.5, type = 'double3')
                    # mc.eval('setAttr "turntable_camShape.backgroundColor" -type double3 0.5 0.5 0.5 ;')

                    if mc.objExists(rigGrp) : 
                        mc.select(rigGrp)
                        mm.eval('fitPanel -selected;')

                    mc.currentTime(9)

            self.setStatus(title, True)        

        else : 
            self.messageBox('Warning', 'Turntable Camera Exists')

    def runRemoveLight(self, arg = None) : 
        files = mc.file(q = True, r = True)
        elements = mc.ls(type = 'VRayRenderElement')

        if elements : 
            mc.delete(elements)
            
        print 'Remove Elements %s' % elements

        if self.selLightPath in files : 
            mc.file(self.selLightPath, rr=True)
            print 'remove light rig'

        else : 
            if mc.objExists('Light_Grp') : 
                path = mc.referenceQuery('Light_Grp', f = True)
                mc.file(path, rr = True)

        if self.turnTableCamera in files : 
            mc.file(self.turnTableCamera, rr=True)
            mc.lookThru('persp')
            print 'remove camera'


    def runImportLineup(self) : 
        title = 'Line up'
        allRefs = mc.file(q = True, r = True)

        if not self.lineup in allRefs : 
            result = mc.file(self.lineup, r = True, ignoreVersion = True, gl = True, loadReferenceDepth = "all", namespace = "lineup", options = "v=0")
            self.setStatus(title, True)

        else : 
            self.setStatus('%s - file exists' % title, True)


    def runRemoveLineup(self) : 
        mc.file(self.lineup, rr=True)



    def runVrayProxyTool(self) : 
        from tool.light.vrayProxyTool import vp_app as app
        reload(app)
        app.show()



    def runCleanNodes(self) : 
        title = 'Clean node'
        from tool.rig.cmd import rig_cmd
        reload(rig_cmd)

        rig_cmd.cleanNodes()
        self.setStatus(title, True)


    def doCreateVrayDisp(self) : 
        title = 'Create vrayDisp'
        rigGrps = ['*Rig_Grp', '*:Rig_Grp']

        for rigGrp in rigGrps : 
            attr = '%s.assetName' % rigGrp

            if mc.objExists(attr) : 
                assetType = mc.getAttr(attr)
                nodeName = '%s_vrayDisp' % assetType
                result = vr.createSingleVrayDisplacement(rigGrp, nodeName)

                self.setStatus(title, True)

                return True

        # set subdivs to 4
        # mc.setAttr('%s.vrayMaxSubdivs' % result, 4)



    def doExportVrayNodes(self) : 
        title = 'Export Vray Nodes'
        asset = entityInfo.info()

        returnResult = dict()
        exportPath = asset.getPath('refData')
        nodeFile = '%s/%s' % (exportPath, asset.getRefNaming('vrayNode'))
        dataFile = '%s/%s' % (exportPath, asset.getRefNaming('vrayNodeData'))

        startMTime1 = None
        startMTime2 = None
        currentMTime1 = None
        currentMTime2 = None

        if os.path.exists(nodeFile) : 
            startMTime1 = os.path.getmtime(nodeFile)

        if os.path.exists(dataFile) : 
            startMTime2 = os.path.getmtime(dataFile)

        result = pipelineTools.exportVrayNode(dataFile, nodeFile)

        dataFileResult = result[0]
        nodeFileResult = result[1]

        if dataFileResult : 
            currentMTime1 = os.path.getmtime(dataFileResult)

        if nodeFileResult : 
            currentMTime2 = os.path.getmtime(nodeFileResult)

        status = False
        status1 = False 
        status2 = False
        message = ''

        if not currentMTime1 == startMTime1 : 
            status1 = True 
            message += 'Node file export complete - '

        if not currentMTime2 == startMTime2 : 
            status2 = True
            message += 'Node data file export complete'

        if status1 and status2 : 
            status = True

        if status : 
            self.setStatus(title, True)

        trace('---- Vray Nodes Output ---')
        trace(dataFileResult)
        trace(nodeFileResult)



    def doRefDevRig(self) : 
        title = 'Ref Dev Rig'
        asset = entityInfo.info()
        # dev rig
        devFile = asset.getRefNaming('devRig')
        devPath = asset.getPath('dev')
        devRigPath = '%s/%s' % (devPath, devFile)

        allRefs = mc.file(q = True, r = True)

        if os.path.exists(devRigPath) : 
            if not devRigPath in allRefs : 
                mc.file(devRigPath, r = True, ignoreVersion = True, gl = True, loadReferenceDepth = "all", namespace = "Rig", options = "v=0")
                self.setStatus(title, True)

            else : 
                self.setStatus('%s - File exists' % title, True)

        else : 
            self.messageBox('Warning', 'File not exists %s' % devRigPath)
            self.setStatus('%s - File not exists' % title, False)


    def doConnectShade(self) : 
        title = 'connect shade'
        asset = entityInfo.info()
        edlPath = asset.dataPath(asset.uv, '%s_%s' % (asset.uv, asset.taskLOD()), data = 'edl')
        shadePath = asset.dataPath(asset.uv, '%s_%s' % (asset.uv, asset.taskLOD()), data = 'shadeFile')
        shadeFile = str()
        edlFile = str()

        edlFiles = sorted(fileUtils.listFile(edlPath))

        if edlFiles : 
            edlFile = '%s/%s' % (edlPath, edlFiles[-1])

        shadeFiles = sorted(fileUtils.listFile(shadePath))

        if shadeFiles : 
            shadeFile = '%s/%s' % (shadePath, shadeFiles[-1])

        if edlFile and shadeFile : 
            namespace = 'Rig'
            result = pipelineTools.assignShader(shadeFile, edlFile, namespace)

            self.setStatus(title, True)

        else : 
            self.messageBox('Error', 'No edl file')




    def doSyncHData(self) : 
        title = 'sync HData'
        asset = entityInfo.info()
        hDir = asset.rigDataPath('hdata')
        files = fileUtils.listFile(hDir)
        node = 'Geo_Grp'

        if files : 
            latestFile = files[-1]
            path = '%s/%s' % (hDir, latestFile)
            print 'Hdata file %s' % path

            pipelineTools.applyHierarchyData(node, path)
            result = pipelineTools.removeExcessiveGeo(node, path)
            print 'Done'

            if result : 
                self.messageBox('Warning', 'Excessive geometries')
                print result
                self.setStatus('%s - Excessive geometries' % title, True)

            else : 
                self.messageBox('Success', 'Sync hierarchy complete')
                self.setStatus('%s' % title, True)

        else : 
            self.messageBox('Error', 'No H-Data. Contact Rig department')
            self.setStatus('%s - No H-Data' % title, False)


    def doTestABC(self) : 
        title = 'Test ABC'
        asset = entityInfo.info()
        abcDir = asset.rigDataPath('abc')
        files = fileUtils.listFile(abcDir)
        obj = 'Geo_Grp'

        if files : 
            latestFile = files[-1]
            path = '%s/%s' % (abcDir, latestFile)
            print 'abc file %s' % path 

            abcUtils.importABC(obj, path, mode = 'add')
            self.messageBox('Success', 'Apply cache complete')
            self.setStatus(title, True)

        else : 
            self.messageBox('Error', 'No abc cache file. Contact Rig department')
            self.setStatus(title, False)


    def doRemoveABC(self) : 
        title = 'Remove test abc'
        abcNodes = mc.ls(type = 'AlembicNode')

        if abcNodes : 
            mc.delete(abcNodes)
            self.setStatus(title, True)



    def doSaveRenderImage(self, mode, arg = None) : 
        result = save_render.saveStill(mode)
        self.messageBox('Complete', 'Saved to %s' % result)



    def doSyncInfo(self) : 
        asset = entityInfo.info()
        rigGrps = ['Rig_Grp', 'Rig:Rig_Grp']
        assetID = self.getAssetID()
        attrs = ['assetID', 'assetType', 'assetSubType', 'assetName', 'project']
        values = [assetID, asset.type(), asset.subType(), asset.name(), asset.project()]
        geoGrps = ['Geo_Grp', 'Rig:Geo_Grp']
        refPath = asset.getPath('ref')

        pipelineTools.assignGeoInfo()

        for rigGrp in rigGrps : 
            if mc.objExists(rigGrp) : 

                i = 0 
                for each in attrs : 
                    attr = '%s.%s' % (rigGrp, each)

                    if mc.objExists(attr) : 
                        if not each == 'assetID' : 
                            mc.setAttr(attr, values[i], type = 'string')

                        else : 
                            mc.setAttr(attr, values[i])

                    i += 1 

        for geoGrp in geoGrps : 
            if mc.objExists(geoGrp) : 
                mc.setAttr('%s.%s' % (geoGrp, 'id'), assetID)
                mc.setAttr('%s.%s' % (geoGrp, 'ref'), refPath, type = 'string')

        self.setStatus('Sync info', True)
        self.messageBox('Information', 'Sync Complete')



    def getAssetID(self) : 
        from tool.utils.sg import sg_utils as sgUtils
        asset = entityInfo.info()
        filters = [['project.Project.name', 'is', asset.project()], 
                    ['sg_asset_type', 'is', asset.type()], 
                    ['sg_subtype', 'is', asset.subType()], 
                    ['code', 'is', asset.name()]]
        fields = ['id']
        result = sgUtils.sg.find_one('Asset', filters, fields)

        if result : 
            return result['id']


    def setPreset(self, arg = None) : 
        # open render setting
        mm.eval('unifiedRenderGlobalsWindow;')

        # set renderer to vray
        mc.setAttr('defaultRenderGlobals.currentRenderer', 'vray', type = 'string')


    def setRenderAnimationPreset(self, arg = None) : 
        # apply preset
        node = 'vraySettings'
        result = mayaTools.applyPreset(node, self.lookDevPresetPath, echo = False)

        # set file name prefix
        mc.setAttr('vraySettings.fileNamePrefix', "<Scene>", type='string')

        # set start end frame
        mc.setAttr('defaultRenderGlobals.animation', 1)
        # mc.setAttr('defaultRenderGlobals.startFrame', 1)
        # mc.setAttr('defaultRenderGlobals.endFrame', 100)
        # mc.playbackOptions(min = 1, max = 48)

        # mc.text('label', e = True, l = 'Step : 12')


    def doRenderStill(self, arg = None) : 
        mc.setAttr('defaultRenderGlobals.animation', 0)
        mm.eval('renderIntoNewWindow render;')


    def setLightComboBox(self) : 
        self.ui.light_comboBox.clear()

        for each in self.lightRigFiles : 
            self.ui.light_comboBox.addItem(each)


    def messageBox(self, title, description) : 
        result = QtGui.QMessageBox.question(self,title,description,QtGui.QMessageBox.Ok)

        return result


    def setStatus(self, message, status) : 
        color = [0, 0, 0]

        if status : 
            iconPath = self.okIcon 

        else : 
            iconPath = self.xIcon 

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(iconPath),QtGui.QIcon.Normal,QtGui.QIcon.Off)
        item = QtGui.QListWidgetItem(self.ui.status_listWidget)
        item.setIcon(icon)
        item.setText(message)
        item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
        size = 16

        self.ui.status_listWidget.setIconSize(QtCore.QSize(size, size))
        QtGui.QApplication.processEvents()



def deleteUI(ui) : 
    if mc.window(ui, exists = True) : 
        mc.deleteUI(ui)


def trace(message) : 
    mm.eval('trace "%s\\n";' % message)
    print '%s' % message
