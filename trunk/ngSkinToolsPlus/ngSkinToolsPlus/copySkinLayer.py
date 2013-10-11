'''
Created on 10/10/2013

@author: Leon
'''

from ngSkinTools.mllInterface import MllInterface 
import maya.cmds as mc

def soloLayer(mll, layerId):
    '''
    enabled layerId, disables the rest
    returns list of layers that are disabled, so we can undo this later
    '''
    allLayers = mll.listLayers()
    
    disableLayers = []
    
    for curLayerId, _layerName in allLayers:
        if curLayerId != layerId and mll.isLayerEnabled(curLayerId):
            # disable layer
            disableLayers.append(curLayerId)
            mll.setLayerEnabled(curLayerId, False)
            
    mll.setLayerEnabled(layerId, True)
            
    return disableLayers
        
        
def queryWeights(skn, mesh):
    '''
    returns skinCluster's weights in the format
    [[influence 0 weights], [influence 1 weights], ...]
    '''
    # The skinPercent command gives us a list of influence weights for each vertex
    # but we need to convert it into a list of vertex weights for each influence!!!
    
    influenceWeightsPerVert = []
    
    vertCount = mc.polyEvaluate(mesh, v=True)
    
    for vertId in range(vertCount):
        # query influenceWeights for this vert
        # and append to list
        influenceWeightsPerVert.append(mc.skinPercent(skn, mesh+'.vtx[%d]'%vertId, q=True, v=True))
        
    vertWeightsPerInfluence = []
    
    influenceCount = len(mc.skinCluster(skn, q=True, inf=True))
        
    for influenceId in range(influenceCount):
        vertWeightsPerInfluence.append([influenceWeights[influenceId] for influenceWeights in influenceWeightsPerVert])
        
    return vertWeightsPerInfluence

def getLayerName(mll, layerId):
    '''
    get layerName from id
    '''
    layers = mll.listLayers()
    
    for curLayerId, layerName in layers:
        if curLayerId == layerId:
            return layerName
        
def getLayerId(mll, layerName):
    '''
    get layerId from name
    '''
    layers = mll.listLayers()
    
    for layerId, curLayerName in layers:
        if curLayerName == layerName:
            return layerId
    
def copySkinLayer(srcMeshName, destMeshName, layerName, influenceAssociation='closestJoint', surfaceAssociation='closestComponent', sampleSpace=0):
    '''
    '''
    srcMll = MllInterface()
    destMll = MllInterface()
    
    srcMll.setCurrentMesh(srcMeshName)
    destMll.setCurrentMesh(destMeshName)
    
    _, srcSkn = srcMll.getTargetInfo()
    _, destSkn = destMll.getTargetInfo()
    
    # get layerId from layerName, and check that this is a valid layer
    srcLayerId = getLayerId(srcMll, layerName)
    if not srcLayerId:
        mc.error('%s is an invalid layer.' % layerName)
    
    # solo layer on srcMesh
    disableLayers = soloLayer(srcMll, srcLayerId)
    
    # save mask weights
    origMaskWeights = srcMll.getLayerMask(srcLayerId)
    
    # temporarily flood mask to 1, so that we can transfer all the data inside this layer
    srcMll.setLayerMask(srcLayerId, [])
    
    #===========================================================================
    # Transfer influence weights
    #===========================================================================
    
    # use maya's copySkinWeights command to transfer weights
    mc.copySkinWeights(ss=srcSkn, ds=destSkn, ia=influenceAssociation, sa=surfaceAssociation, spa=sampleSpace)
    
    # query and catch weights
    destInfluenceWeights = queryWeights(destSkn, destMeshName)
    
    #===========================================================================
    # Transfer mask weights
    # This is very messed up, but it's the simplest workaround I can think of...
    # Basically, we create a new joint "tempSkinLayerMaskTransferer_jnt" bound to both skins
    # This ensures that we can transfer the mask weights by joint name,
    # even if influence weights are transfered by other methods
    #===========================================================================
    
    # create tempJnt
    
    
    # apply mask weights to tempJnt
    
    
    # use maya's copySkinWeights command, with name as influence association
    
    
    # query and catch weights
    
    #===========================================================================
    # Reset original skin layer
    #===========================================================================
    
    # reset mask to original weights
    srcMll.setLayerMask(srcLayerId, origMaskWeights)
    
    # un-solo layer
    for layerId in disableLayers:
        srcMll.setLayerEnabled(layerId, True)
    
    #===========================================================================
    # Add layer to destination skin
    #===========================================================================
    print destInfluenceWeights
    
    destLayerId = destMll.createLayer(layerName, forceEmpty=True)
    
    influenceCount = len(mc.skinCluster(destSkn, q=True, inf=True))
        
    for influenceId in range(influenceCount):
        destMll.setInfluenceWeights(destLayerId, influenceId, destInfluenceWeights[influenceId])