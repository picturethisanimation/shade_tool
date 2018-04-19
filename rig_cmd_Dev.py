# System modules
import sys
import os
import maya.cmds as mc
import maya.mel as mm
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def importRef() : 
	""" import reference and try to remove namespace """
	cleanSharedReferenceNode()
	
	refs = mc.ls(type = 'reference')
	skipNodes = ['_UNKNOWN_REF_NODE_', 'sharedReferenceNode']
	skipNamespaces = ['UI', 'shared']

	for each in refs : 
		try : 
			if not each in skipNodes : 
				fileName = mc.referenceQuery(each, filename = True)
				mc.file(fileName, importReference = True)

		except Exception as e : 
			print e

	namespaces = mc.namespaceInfo(listOnlyNamespaces = True)

	for each in namespaces : 
		if not each in skipNamespaces : 
			mc.namespace(force = True, mv=(':%s' % each, ':') )
			mc.namespace(removeNamespace = each)

def cleanSharedReferenceNode() : 
	refs = mc.ls(type = 'reference')

	for eachRef in refs : 
		if 'sharedReferenceNode' in eachRef : 
			mc.delete(eachRef)


def clean() : 
	""" clean _UNKNOWN_REF_NODE_  """
	cleanNodes = ['_UNKNOWN_REF_NODE_']

	for each in cleanNodes : 
		if mc.objExists(each) : 
			mc.lockNode(each, l = False)
			mc.delete(each)


def assignTmpShd() : 
	""" assign pink tmp Shade """
	from tool.utils import mayaTools 
	reload(mayaTools)

	geoGrp = 'Geo_Grp'
	# list shadingEngine
	allSg = mc.ls(type = 'shadingEngine')
	exception = ['initialParticleSE', 'initialShadingGroup']
	allSg = [a for a in allSg if not a in exception]
	shades = []
	geos = []
	deleteSgs = []

	# looping for shader
	for each in allSg : 
		shds = mc.listConnections('%s.surfaceShader' % each)
		
		if shds : 
			if not shds[0] in shades : 
				# check rig shade
				# skip check rig shade, just assign all lambert 
				# if mayaTools.checkValidShader(shds[0]) : 
				shades.append(shds[0])
				deleteSgs.append(each)
				shdGeo = mc.listConnections('%s.dagSetMembers' % each, s = True, d = False)

				if shdGeo : 
					geos = geos + shdGeo



	# delete all shader 
	mc.delete(deleteSgs)
	mc.delete(shades)

	# create tmpShade
	# tmpShd = mc.shadingNode('lambert', asShader = True, n = 'tmp_shd')
	# sg = mc.createNode('shadingEngine', n = '%sSG' % tmpShd)
	# mc.setAttr('%s.color' % tmpShd, 1, 0, 1, type = 'double3')
	# mc.connectAttr('%s.outColor' % tmpShd, '%s.surfaceShader' % sg, f = True)

	# create tmpShade (fix)
	tmpShd = mc.shadingNode('lambert', asShader = True, n = 'tmp_shd')
	sg = mc.sets(name = '%sSG' % tmpShd, renderable = True, noSurfaceShader = True, empty = True)
	mc.setAttr('%s.color' % tmpShd, 1, 0, 1, type = 'double3')
	mc.connectAttr('%s.outColor' % tmpShd, '%s.surfaceShader' % sg, f = True)

	# assign
	mc.select(geos)
	mc.sets(e = True, forceElement = sg)
	removeUnUsedShader()

 
def removeUnUsedShader() : 
	# delete unused shaders 
	shaderType = ['VRayBlendMtl', 'VRayMtl', 'lambert', 'blinn', 'VRayMtl2Sided']
	shaders = mc.ls(type = shaderType)
	removeShds = []

	for shade in shaders : 
		nodes = mc.listConnections('%s.outColor' % shade, s = False, d = True)
		print nodes

		if not nodes : 
			removeShds.append(shade)

	mc.delete(removeShds)


def removeSets() : 
	""" remove 'Blocking_Set', 'Proxy_Set', 'Render_Set', 'Anim_Set' """
	cleanSet = ['Blocking_Set', 'Proxy_Set', 'Render_Set', 'Anim_Set']
	setGrps = mc.ls(type = 'objectSet')

	for eachSet in setGrps : 
		if eachSet in cleanSet : 
			mc.delete(eachSet)

def removeFixSets(): 
	""" remove fix sets """ 
	setGrps = mc.ls(type = 'objectSet')
	suffix = '_fixSet'
	
	for eachSet in setGrps: 
		if suffix in eachSet: 
			mc.delete(eachSet)

def removeRig() : 
	""" remove rig. Use for exporting cache rig process """
	geoGrp = 'Geo_Grp'
	rootGrp = 'SuperRoot_Grp'
	rsProxy = 'rsproxy_grp'
	rs = False
	if mc.objExists(rsProxy): 
		rs = True

	# delete constraint
	geo = mc.listRelatives(geoGrp, ad = True, f = True)
	mc.delete(geo, constraints = True)

	# if rsProxy found, unparent first
	if rs: 
		mc.parent(rsProxy, w=True)

	# delete history Geo_Grp
	geo = mc.listRelatives(geoGrp, ad = True, f = True)
	mc.delete(geo, ch = True)

	# delete Rig
	try:
		if mc.objExists(rootGrp): 
			objs = mc.listRelatives(rootGrp, ad = True, f = True)
			mc.lockNode(objs, l = False)
			mc.delete(rootGrp)
		# freeze tranformation geo grp
		clearConnections(geoGrp)
		mc.select(geoGrp, hi = True)
		geo = mc.ls(sl = True)
		mc.makeIdentity(geo, apply = True)
		mc.select(cl = True)
		
	except Exception as e:
		print 'removeRig Error : {0}'.format(e)

	if rs: 
		mc.parent(rsProxy, geoGrp)


def addRemoveVrayProxy(keep = True) : 
	print 'addRemoveVrayProxy'
	""" remove vproxy_grp from Geo_Grp. -> Use for publish Render from shade """
	targetGrp = 'vproxy_grp'
	parentGrp = 'Geo_Grp'

	objs = mc.listRelatives(parentGrp, c = True)
	print objs
	print targetGrp

	for each in objs : 
		if mc.objectType(each) == 'transform' : 
			if keep : 
				if not each == targetGrp : 
					mc.delete(each)
					print 'delete %s' % each

			else : 
				if each == targetGrp : 
					mc.delete(each)


def addRemoveRsProxy(keep = True) : 
	print 'addRemoveRsProxy'
	""" remove rsproxy_grp from Geo_Grp. -> Use for publish Render from shade """
	targetGrp = 'rsproxy_grp'
	parentGrp = 'Geo_Grp'

	objs = mc.listRelatives(parentGrp, c = True)
	print objs
	print targetGrp

	for each in objs : 
		if mc.objectType(each) == 'transform' : 
			if keep : 
				if not each == targetGrp : 
					mc.delete(each)
					print 'delete %s' % each

			else : 
				if each == targetGrp : 
					mc.delete(each)

def removeRsProxy() : 
	print 'addRemoveRsProxy'
	""" remove rsproxy_grp from Geo_Grp. -> Use for publish Render from shade """
	targetGrp = 'rsproxy_grp'
	parentGrp = '*:Geo_Grp'

	objs = mc.listRelatives(parentGrp, c = True)
	print objs
	print targetGrp

	for each in objs : 
		if mc.objectType(each) == 'transform' : 
			if each == targetGrp : 
				mc.delete(each)

def removeVrayNode() : 
	""" remove VRayDisplacement, VRayObjectProperties node """
	node1 = mc.ls(type = 'VRayDisplacement')
	node2 = mc.ls(type = 'VRayObjectProperties')
   
	if node1 : 
		mc.delete(node1)

	if node2 : 
		mc.delete(node2)

def removeRsNode() : 
	""" remove VRayDisplacement, VRayObjectProperties node """
	node1 = mc.ls(type = 'RedshiftMeshParameters')
	# node2 = mc.ls(type = 'VRayObjectProperties')
   
	if node1 : 
		mc.delete(node1)

def vProxy() : 
	""" use for publishing vProxy """ 
	targetGrp = 'vproxy_grp'
	parentGrp = 'Geo_Grp'
	addRemoveVrayProxy(keep = True)
	# mc.parent(parentGrp, w = True)


def rsProxy() : 
	""" use for publishing rsProxy """ 
	targetGrp = 'rsproxy_grp'
	parentGrp = 'Geo_Grp'
	addRemoveRsProxy(keep = True)


def unlockTransform(objects) : 
	""" unlock transform node """ 

	for each in objects : 
		attrs = mc.listAttr(each, k = True)
		
		if mc.objectType(each, isType = 'transform') : 
			for attr in attrs : 
				mc.setAttr('%s.%s' % (each, attr), l = False)


def clearConnections(obj) : 
	""" clear connection """ 
	mm.eval('source "C:/Program Files/Autodesk/Maya2016/scripts/startup/channelBoxCommand.mel";')
	
	mc.select(obj, hi = True)
	objs = mc.ls(sl = True)

	for each in objs : 
		if mc.objectType(each, isType = 'transform') : 
			attrs = mc.listAttr(each, k = True)

			if attrs : 
				for eachAttr in attrs : 
					attr = '%s.%s' % (each, eachAttr)
					mm.eval('CBdeleteConnection "%s";' % attr)

def emptyGeoGrp() : 
	""" delete everything in Geo_Grp """
	childs = mc.listRelatives('Geo_Grp', c = True)

	if childs : 
		mc.delete(childs)


def combineGeo() : 
	""" combind mesh in Geo_Grp """
	geoGrp = 'Geo_Grp'
	assetAttr = '%s.assetName' % geoGrp
	name = 'combineGeo'

	if mc.objExists(assetAttr) : 
		name = mc.getAttr(assetAttr)

	result = mc.polyUnite(geoGrp, ch = 0, mergeUVSets = 1, n = name)

	if mc.objExists(geoGrp) : 
		emptyGeoGrp()

	else : 
		mc.group(em = True, n = geoGrp)

	mc.parent(result, geoGrp)

	return result 


def cleanAllSets() : 
	""" delete all objectSet """
	sets = mc.ls(type = 'objectSet')    

	if sets : 
		mc.delete(sets)

def removeUnknownPlugin() : 
	try : 
		oldPlugins = mc.unknownPlugin(q=True, list=True)
		removes = []
		if oldPlugins : 
			for plugin in oldPlugins:
				mc.unknownPlugin(plugin, remove=True)
				removes.append(plugin)

		if not removes : 
			logger.info('Remove 0 plugin')

		if removes : 
			logger.info('Remove %s plugins' % len(removes))
			logger.debug(removes)

			return removes

	except Exception as e : 
		logger.debug(e)

def Nu_importAllRefs() : 
	""" import all references by Nu """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	

	pipeTools.importAllRefs()

def Nu_removeAllNameSpace() : 
	""" remove all namespaces by Nu """ 
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	

	pipeTools.removeAllNameSpace()

def Nu_parentPreConsObj() : 
	""" parent joint instead of constraint by Nu """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	

	pipeTools.parentPreConsObj()


def Nu_connectDualSkeleton() : 
	""" connect connectDualSkeleton by Nu """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	

	pipeTools.connectDualSkeleton(False, False)

def Nu_deleteAllTurtleNodes() : 
	""" remove all turtle nodes and unload Turtle.mll by Nu """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)

	pipeTools.deleteAllTurtleNodes()

def Nu_deleteExtraDefaultRenderLayer():
	""" remove extra defaultRenderLayer by Nu """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	
	pipeTools.deleteExtraDefaultRenderLayer()

def Nu_deleteAllUnknownNodes():
	""" remove all unknown nodes by Nu """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	
	pipeTools.deleteAllUnknownNodes()

def Nu_turnOffSmoothMeshPreview():
	""" turn off smooth mesh preview by Nu """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	
	pipeTools.turnOffSmoothMeshPreview_All()

def Nu_turnOffScaleCompensate():
	""" turn off joint scale compensate by Nu """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	
	pipeTools.turnOffScaleCompensate_All()

def Nu_removeUnusedInfluence_All():
	""" remove unused joint influences on all skinCluster nodes """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	pipeTools.removeUnusedInfluence_All()

def Nu_removeExtraCamera():
	""" try to remove non-default cameras """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	pipeTools.removeExtraCamera()

def Nu_removeAllSequencerNodes():
	""" try to remove all sequencer nodes """
	sysPath = 'O:/studioTools/maya/python/tool/rig/nuTools/pipeline'
	if not sysPath in sys.path : 
		sys.path.append(sysPath)

	import pipeTools
	reload(pipeTools)
	pipeTools.removeAllSequencerNodes()

def cleanNodes() : 
	""" clean node cleanDefaultRenderLayer, cleanTurtleRender, cleanUnKnownNode """
	from tool.utils import mayaTools 
	reload(mayaTools)

	mayaTools.cleanDefaultRenderLayer()
	mayaTools.cleanTurtleRender()
	mayaTools.cleanUnKnownNode()



def exportAssetShade() : 
	from tool.ptAlembic import exportShade as es
	reload(es)
	es.doShadeExport()
	print 'Export shade / data shade'

def exportAssetRSShade() : 
	from tool.ptAlembic import exportShade as es
	reload(es)
	es.doShadeExportRS()
	print 'Export shade / data shade'

def hideRigDetails() :
	"""hide unneccessary rig nodes before publish by Ken's requests."""
	detailNodes = mc.ls(['jnt_grp', 'ikh_grp', 'skin_grp', 'proxySkin_grp', 'Util_Grp'])
	mc.hide(detailNodes)

def deleteNonDefaultCamera():
	"""delete all camera except the default ones."""
	defaultCam = ['front', 'persp', 'side', 'top']
	nonDefCam = [cam for cam in mc.listCameras() if cam not in defaultCam]
	
	mc.delete(nonDefCam)

def setRsProxyDisplayPercent():
	"""set rsProxy displayPercent attribute to 1 percent""" 
	listNodes = mc.ls(type='RedshiftProxyMesh')
	for node in listNodes:
		mc.setAttr('%s.displayPercent' %node, 1)

def exportBuildShade():
	""" Export shader with attr ptAssign >> assetName_SHDBUILD.ma"""
	logger.info('exportBuildShade--------------------')
	from tool.shade.shadeDataManage import exportShade
	reload(exportShade)
	app = exportShade.Export()
	result = app.doExport()
	logger.info('result : {0}'.format(result))

def exportRenderShade():
	""" Export shader with attr ptAssign >> assetName_SHDRS.ma"""
	currentFile = mc.file(q=True,sn=True)
	logger.info('exportRenderShade--------------------')
	from tool.shade.shadeDataManage import shadeDataManager
	reload(shadeDataManager)

	app = shadeDataManager.ShadeManager()
	app.reLocalPath()
	app.covertRsTexture()
	result1 = app.reToRstexbin()
	logger.info('result1 : {0}'.format(result1))

	from tool.shade.shadeDataManage import exportShade
	reload(exportShade)
	app = exportShade.Export()
	result2 = app.doExport(shadeType='render')

	logger.info('result2 : {0}'.format(result2))
	mc.file(currentFile,o=True,f=True)





