import sys, os 

import maya.cmds as mc
import maya.mel as mm

from tool.utils import entityInfo2 as entityInfo
reload(entityInfo)

from tool.utils import fileUtils 
reload(fileUtils)

def saveVrayRender(dstDir, dstFile, img = 'jpg') : 

    dst = '%s/%s' % (dstDir, dstFile)

    if not os.path.exists(dstDir) : 
        os.makedirs(dstDir)
        
    # send back to maya viewport 
    mm.eval('vrend -cloneVFB;')

    # set to jpeg
    mc.setAttr ('defaultRenderGlobals.imageFormat', 8)

    # save from render view to disk
    try : 
        mc.renderWindowEditor('renderWindowPanel', edit = True, writeImage = dst)

    except : 
        mc.renderWindowEditor('renderView', edit = True, writeImage = dst)

    return dst

    # mc.confirmDialog( title = 'Complete', message = 'Image saved \n%s\n%s' % (dst, outputPath2), button=['OK'])

def saveStill(mediaType = 'still', ext = False) : 
    asset = entityInfo.info()
    # save to surface 
    mediaDir = asset.surfaceOutput(mediaType)
    currentFile = asset.fileName(ext = False)

    files = fileUtils.listFile(mediaDir)
    fileName = '%s_%02d' % (currentFile, 1)

    if files : 
        fileCount = 0 

        for each in files : 
            if currentFile in each : 
                fileCount += 1 

        fileName = '%s_%02d' % (currentFile, fileCount + 1)

    # save to surface
    result = saveVrayRender(mediaDir, fileName, img = 'jpg')
    print 'Saved to %s' % result

    if result : 
        src = '%s.jpg' % result

        if os.path.exists(src) : 
            # save to hero 
            heroDir = asset.mediaHeroName(mediaType = mediaType, returnPath = True)
            dst = '%s.jpg' % heroDir
            result2 = fileUtils.copy(src, dst)

            print 'Saved to %s' % result2


        return src