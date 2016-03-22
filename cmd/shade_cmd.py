import sys, os 
import maya.cmds as mc
import maya.cmds as mm
from tool.utils import entityInfo2 as entityInfo 
from tool.utils import fileUtils
reload(entityInfo)

def assign() : 
    asset = entityInfo.info()
    dataPath = '%s/data' % asset.getPath('uv', 'uv_%s' % asset.taskLOD())
    edlUVPath = '%s/%s' % (dataPath, 'edl')
    shadeFilePath = '%s/%s' % (dataPath, 'shadeFile')

    dataFiles = sorted(fileUtils.listFile(edlUVPath))
    shadeFiles = sorted(fileUtils.listFile(shadeFilePath))
    namespace = 'Rig'

    if shadeFiles and dataFiles : 
        shadeFile = '%s/%s' % (shadeFilePath, shadeFiles[-1])
        edlFile = '%s/%s' % (edlUVPath, dataFiles[-1])

        if os.path.exists(shadeFile) and os.path.exists(edlFile) : 
            assignShader(shadeFile, edlFile, namespace)


def assignShader(shadeFile, edlFile, namespace):

    missGeo = ''

    mc.file(shadeFile, i=True, loadReferenceDepth="all", pr=True, options ="v=0")

    f = open(edlFile,'r')
    txt = f.read()
    f.close()

    for t in txt.split('\r\n'):
        geo = []
        if t.split(' ')[1:]:
            mc.select(cl=True)
            for face in t.split(' ')[1:]:
                if not face[:4] == '%s:' % namespace:
                    face = face.split('|')
                    face = ('|%s:' % namespace).join(face)
                    face = '%s:%s' % (namespace, face)
                try:
                    mc.select(face ,r=True)
                    geo.append(face)

                except:
                    # face
                    missGeo += '%s\n' % (face)
            if geo: 
                mc.select(geo,r=True)
                mc.hyperShade(assign=t.split(' ')[0] )  
            mc.select(cl=True)
    print '\n___________________________________\nGeo is missing.\n___________________________________\n%s' % missGeo
