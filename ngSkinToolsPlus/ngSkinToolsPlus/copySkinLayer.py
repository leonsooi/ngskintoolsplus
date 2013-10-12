import maya.cmds as mc
from ngSkinTools.mllInterface import MllInterface 

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
        
        
def getInfluenceId(mll, layerId, influenceName):
    '''
    get influenceId from name
    '''
    influences = mll.listLayerInfluences(layerId, False)
    
    for name, index in influences:
        if influenceName == name:
            return index
        

def setInfluenceWeight(skn, mesh, influenceName, weightList):
    '''
    Set weights on influence using a float list
    '''
    for vertId in range(len(weightList)):
        if weightList[vertId]:
            mc.skinPercent(skn, mesh+'.vtx[%d]'%vertId, transformValue=[influenceName, weightList[vertId]])
    

def copySkinLayerByName(srcMeshName, destMeshName, layerName, influenceAssociation='closestJoint', surfaceAssociation='closestComponent', sampleSpace=0):
    '''
    Actual work is done here. Copies an individual layer from srcMesh to destMesh
    '''  
    srcMll = MllInterface()
    destMll = MllInterface()
    
    srcMll.setCurrentMesh(srcMeshName)
    destMll.setCurrentMesh(destMeshName)
    
    _, srcSkn = srcMll.getTargetInfo()
    _, destSkn = destMll.getTargetInfo()
    
    srcMll.initLayers()
    destMll.initLayers()
    
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
    
    if origMaskWeights:
        # create tempJnt
        tempJnt = mc.joint(n='layerMaskTransfer_tempJnt')
        mc.skinCluster(srcSkn, edit=True, addInfluence=tempJnt)
        
        # also create an additional tempJnt to hold the "reversed" weights
        tempHoldJnt = mc.joint(n='layerMaskTransferHold_tempJnt')
        mc.skinCluster(srcSkn, edit=True, addInfluence=tempHoldJnt, weight=1, lockWeights=True)
        mc.skinCluster(srcSkn, inf=tempHoldJnt, e=True, lockWeights=False);
        
        # apply mask weights to tempJnt
        setInfluenceWeight(srcSkn, srcMeshName, tempJnt, origMaskWeights)
        
        # use maya's copySkinWeights command, with name as influence association
        mc.skinCluster(destSkn, edit=True, addInfluence=tempJnt)
        mc.skinCluster(destSkn, edit=True, addInfluence=tempHoldJnt)
        mc.copySkinWeights(ss=srcSkn, ds=destSkn, ia="name", sa=surfaceAssociation, spa=sampleSpace)
        
        # query and catch weights
        destMaskWeights = queryWeights(destSkn, destMeshName)[-2]
        
        # remove tempJnt
        mc.skinCluster(srcSkn, edit=True, removeInfluence=tempJnt)
        mc.skinCluster(srcSkn, edit=True, removeInfluence=tempHoldJnt)
        mc.skinCluster(destSkn, edit=True, removeInfluence=tempJnt)
        mc.skinCluster(destSkn, edit=True, removeInfluence=tempHoldJnt)
        mc.delete(tempJnt) # automatically deletes the holdJnt as well since it is a child
    else:
        # if origMaskWeights was uninitialized, just use []
        destMaskWeights = []
    
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
    # print destInfluenceWeights
    
    destLayerId = destMll.createLayer(layerName, forceEmpty=True)
    
    influenceCount = len(mc.skinCluster(destSkn, q=True, inf=True))
    
    # set influence weights
    for influenceId in range(influenceCount):
        weights = destInfluenceWeights[influenceId]
        # check if the influence has non-zero values, to reduce number of calls
        if not all(val==0 for val in weights):
            destMll.setInfluenceWeights(destLayerId, influenceId, weights)
        
    # set mask weights
    destMll.setLayerMask(destLayerId, destMaskWeights)