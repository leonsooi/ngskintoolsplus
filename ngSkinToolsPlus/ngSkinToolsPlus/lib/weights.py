'''
Created on Mar 25, 2014

@author: Leon
'''
import maya.cmds as mc
import pymel.core as pm

import utils.rigging as rt

mel = pm.language.Mel()

def smoothLayerMask(mll, layerId, intensity=1.0):
    '''
    '''
    mll.setCurrentLayer(layerId)
    mll.ngSkinLayerCmd(cpt='mask')
    
    # if intensity is larger than 1.0, use multiple iterations
    while intensity > 1.0:
        mll.ngSkinLayerCmd(paintOperation=4, paintIntensity=1.0)
        mll.ngSkinLayerCmd(paintFlood=True)
        intensity = intensity - 1.0
    
    mll.ngSkinLayerCmd(paintOperation=4, paintIntensity=intensity)
    mll.ngSkinLayerCmd(paintFlood=True)
    
    
def relaxLayerWeights(mll, layerId, expand=True, 
                      relaxSteps=33, relaxSize=0.1708, relaxAllAmount=0.5):
    '''
    relax all weights on layer
    verts closest to joints will be masked
    expand will expand the mask
    '''
    infIter = mll.listLayerInfluences(2)
    infs = list(infIter)
    mesh = mll.getTargetInfo()[0]
    mesh = pm.PyNode(mesh)
    
    # get vert closest to joints
    vertIds = []
    for inf, infId in infs:
        pos = pm.PyNode(inf).getTranslation(space='world')
        faceId = mesh.getClosestPoint(pos, space='world')[1]
        faceVertIds = mesh.f[faceId].getVertices()
        closestVertId = min(faceVertIds, key=lambda vtxId: (mesh.vtx[vtxId].getPosition() - pos).length())
        
        closestVertIds = [closestVertId]
        # expand ids if needed
        if expand:
            connectedVertices = mesh.vtx[closestVertId].connectedVertices()
            closestVertIds += [vtx.index() for vtx in connectedVertices]
        
        vertIds += closestVertIds
    
    vertCount = mll.getVertCount()
    
    # invert vertIds
    # just use strings since we're going to pass into ngSkinRelax
    vertsToRelax = [mesh.name() + '.vtx[%d]' % id_ for id_ in range(vertCount) if id_ not in vertIds]
    
    args = {}
    args['numSteps']=relaxSteps
    args['stepSize']=relaxSize
    mel.ngSkinRelax(vertsToRelax,**args)
    
    # run another relax to clean up any artefacts
    # relax all
    args = {}
    args['numSteps']=int(relaxSteps * relaxAllAmount)
    args['stepSize']=relaxSize * relaxAllAmount
    mel.ngSkinRelax(mesh.name(),**args)
    
    

def createWeightsListByPolyStrip(outerXfos, innerXfos, mesh, loops=0):
    '''
    returns weights as a float list
    innerVerts will be weighted to 1
    loops [int]: number of loops the polyStrip will have
            0 means an instant falloff from inner to outer
            1 means falloff after 50%, etc...
    '''
    polyStrip, outerVerts, innerVerts = createPolyLoftStrip('temp_weights_', outerXfos, innerXfos, loops)
    # bind polystrip to temporary jnts
    pm.select(cl=True)
    weightBnd = pm.joint(n='temp_weight_bnd')
    pm.select(cl=True)
    noWeightBnd = pm.joint(n='temp_noWeight_bnd')
    sknStrip = pm.skinCluster(weightBnd, noWeightBnd, polyStrip)
    # set weights to polystrip
    sknStrip.setWeights(innerVerts, [0], [1])
    sknStrip.setWeights(outerVerts, [1], [1])
    # create temp mesh to transfer weights to
    tempMesh = pm.duplicate(mesh)[0]
    sknMesh = pm.skinCluster(weightBnd, noWeightBnd, tempMesh)
    pm.copySkinWeights(ss=sknStrip, ds=sknMesh, ia='oneToOne', sa='closestPoint', nm=1)
    # add weights to a float list
    weightsIter = sknMesh.getWeights(tempMesh, 0)
    weightsList = list(weightsIter)
    # cleanup
    pm.delete(polyStrip, tempMesh, weightBnd, noWeightBnd)
    return weightsList
    
    
def createPolyLoftStrip(name, outerXfos, innerXfos, loops):
    '''
    name [string]
    takes two lists of transforms (as strings),
    returns poly mesh lofted between the two loops
    also returns two lists of verts (outer and inner)
    '''
    # create curves
    outerCrv = rt.makeCrvThroughObjs(outerXfos, 'temp_outer_crv', False, 3)
    mc.closeCurve(outerCrv, preserveShape=0, rpo=True)
    innerCrv = rt.makeCrvThroughObjs(innerXfos, 'temp_inner_crv', False, 3)
    mc.closeCurve(innerCrv, preserveShape=0, rpo=True)
    
    outerCrv = pm.PyNode(outerCrv)
    innerCrv = pm.PyNode(innerCrv)
    
    # rebuild crvs so they can be lofted
    maxSpans = max(outerCrv.numSpans(), innerCrv.numSpans())
    pm.rebuildCurve(outerCrv, rpo=True, spans=maxSpans, kr=2)
    pm.rebuildCurve(innerCrv, rpo=True, spans=maxSpans, kr=2)
    
    # loft crvs
    polyStrip = pm.loft(outerCrv, innerCrv, d=1, n=name+'polyStrip_geo', 
                        polygon=1, ch=0, sectionSpans=loops+1)[0]
    outerVerts = polyStrip.vtx[0:maxSpans-1]
    innerVerts = polyStrip.vtx[maxSpans:]
    
    # cleanup
    pm.delete(outerCrv, innerCrv)
    
    return polyStrip, outerVerts, innerVerts