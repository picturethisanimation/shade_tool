import sys, os 
import maya.cmds as mc 
import maya.mel as mm
from tool.utils import entityInfo, fileUtils
reload(entityInfo)
from  tool.ptAlembic import abcImport, importShade
reload(abcImport)
reload(importShade)

def doImportABC() : 
    title = 'Test ABC'
    asset = entityInfo.info()
    abcDir = asset.rigDataPath('abc')
    files = fileUtils.listFile(abcDir)
    namespace = asset.name()
    obj = 'Geo_Grp'

    if files : 
        latestFile = files[-1]
        path = '%s/%s' % (abcDir, latestFile)
        print 'abc file %s' % path 

        abcImport.importCacheAsset(namespace, path)
        print('Success', 'Apply cache complete')
        return True

    else : 
        print('Error', 'No abc cache file. Contact Rig department')
        return False


def doImportShade() : 
    asset = entityInfo.info()
    assetName = asset.name()
    refPath = asset.getPath('ref')
    shadeName = asset.getRefNaming('shade', showExt = False)
    shadeFile = '%s/%s.ma' % (refPath, shadeName)
    shadeDataFile = '%s/%s.yml' % (refPath, shadeName)

    if os.path.exists(shadeFile) and os.path.exists(shadeDataFile) : 
        importShade.applyRefShade(assetName, shadeFile, shadeDataFile)


def doImportVrayNode() : 
    from tool.ptAlembic import vrayNode_utils as vu
    reload(vu)
    vu.doImportVrayNodes()


def runImportMatteID() : 
    from tool.matte import matteImport_app as app
    reload(app)
    myApp = app.MyForm(app.getMayaWindow())