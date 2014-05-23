'''
Title: copySkinLayers (for ngSkinTools)
Author: Leon Sooi
Email: mail@leonsooi.com
Date: May 21, 2014

This script uses Maya's native "copySkinWeights" command to transfer
ngSkinLayers across meshes of different topology. This is a rather
convoluted work-around indeed, but the benefit is that we can take
advantage of already existing functionality (e.g. copy by closest point,
uvs, name, closest joint, label, etc.) 

The script assumes that you already have ngSkinTools installed. It uses
the ngSkinTools API and other UI elements from ngSkinTools.

Limitations:
- Transparency will probably not work. 
  Use "Edit -> Convert Transparency to Mask" before running script
- There are a number of warning messages, but they don't seem to
  break anything (yet...)
  
Install:
- Copy "copySkinLayers.py" into your scripts folder.
- In Maya, run the python commands:

from copySkinLayers import CopySkinLayersWindow
cslWin = CopySkinLayersWindow.getInstance()
cslWin.showWindow()
    
Use:
- Ensure both source and destination meshes are bound to skinClusters
  with necessary joints, and with skinning layers initialized
- Select source mesh, shift-select destination mesh
- Set options in the Copy Skin Layers window and click "Copy":

    Surface Association: 
        - "Closest point on surface" seems to work best
        
    Influence Association: 
        - "Name" works best if you're using the same skeleton
          (make sure you have the same joints bound to both meshes)
        - "Closest joint" works well for most cases, but may break
          if there are multiple joints on the same position.
          
    More information on copySkinWeights options:
        - http://download.autodesk.com/global/docs/maya2014/en_us/files/Skin__Edit_Smooth_Skin__Copy_Skin_Weights.htm
        - http://download.autodesk.com/global/docs/maya2014/en_us/CommandsPython/copySkinWeights.html
'''

import maya.cmds as mc

from ngSkinTools.mllInterface import MllInterface 
from ngSkinTools.ui.layerDataModel import LayerDataModel
from ngSkinTools.ui.basetoolwindow import BaseToolWindow
from ngSkinTools.ui.mainwindow import MainWindow
from ngSkinTools.ui.basetab import BaseTab
from ngSkinTools.ui.uiWrappers import DropDownField, RadioButtonField, CheckBoxField
from ngSkinTools.doclink import SkinToolsDocs
from ngSkinTools.log import LoggerFactory


#===============================================================================
# UI - similar options to Maya's copySkinWeightsOptions UI
#===============================================================================

class CopySkinLayersWindow(BaseToolWindow):
    def __init__(self, windowName):
        BaseToolWindow.__init__(self, windowName)
        self.windowTitle = 'Copy Skin Layers'
        self.sizeable = True
        self.defaultHeight = 350
        self.defaultWidth = 300
        
    @staticmethod
    def getInstance():
        return BaseToolWindow.getWindowInstance('CopySkinLayersWindow', CopySkinLayersWindow)
    
    def createWindow(self):
        BaseToolWindow.createWindow(self)
        
        self.content = CopyLayersTab()
        self.content.parentWindow = self
        self.content.createUI(self.windowName)
        
class CopyLayersTab(BaseTab):
    log = LoggerFactory.getLogger('Copy Skin Layers Tab')
    VAR_PREFIX = 'ngSkinToolsCopySkinLayersTab_'
    
    def __init__(self):
        BaseTab.__init__(self)
        
    def createUI(self, parent):
        # base layout
        
        buttons = []
        buttons.append(('Copy', self.copySkinLayers, ''))
        buttons.append(('Close', self.closeWindow, ''))
        
        self.cmdLayout = self.createCommandLayout(buttons, SkinToolsDocs.INITWEIGHTTRANSFER_INTERFACE)

        self.createSurfaceAssociationGroup()
        self.createInfluenceAssociationGroup()
        self.createOptionsGroup()
        
        self.updateLayoutEnabled()
        
    def createSurfaceAssociationGroup(self):
        group = self.createUIGroup(self.cmdLayout.innerLayout, 'Surface Association')
        
        self.createFixedTitledRow(group, 'Surface Association')
        self.controls.radioSurfaceCollection = mc.radioCollection()
        self.controls.radioClosestPoint = RadioButtonField(self.VAR_PREFIX+'closestPoint', defaultValue=1, label='Closest point on surface', 
                                                           annotation='Closest point on surface')
        self.controls.radioRaycast = RadioButtonField(self.VAR_PREFIX+'rayCast', defaultValue=0, label='Ray cast', 
                                                           annotation='Ray cast')
        self.controls.radioClosestComponent = RadioButtonField(self.VAR_PREFIX+'closestComponent', defaultValue=0, label='Closest component', 
                                                           annotation='Closest component')
        self.controls.radioUVSpace = RadioButtonField(self.VAR_PREFIX+'UVSpace', defaultValue=0, label='UV space', 
                                                           annotation='UV space')
                                                           
        self.createFixedTitledRow(group, 'Sample space')
        self.controls.sampleSpace = DropDownField(self.VAR_PREFIX+'sampleSpace')
        self.controls.sampleSpace.beginRebuildItems()
        self.controls.sampleSpace.addOption('World')
        self.controls.sampleSpace.addOption('Local')
        self.controls.sampleSpace.endRebuildItems()
    
    def createOptionsGroup(self):
        group = self.createUIGroup(self.cmdLayout.innerLayout, 'Options')
        
        self.createFixedTitledRow(group, 'Layers')
        self.controls.selLayers = DropDownField(self.VAR_PREFIX+'selLayers')
        self.controls.selLayers.beginRebuildItems()
        self.controls.selLayers.addOption('All layers in skin cluster')
        self.controls.selLayers.addOption('Selected layers in lister')
        self.controls.selLayers.endRebuildItems()
        
        self.createFixedTitledRow(group, 'Normalization')
        self.controls.normalization = DropDownField(self.VAR_PREFIX+'normalization')
        self.controls.normalization.beginRebuildItems()
        self.controls.normalization.addOption('On')
        self.controls.normalization.addOption('Off')
        self.controls.normalization.endRebuildItems()
        
    def createInfluenceAssociationGroup(self):
        '''
        '''
        group = self.createUIGroup(self.cmdLayout.innerLayout, 'Influence Association')
        
        for index in range(3):
            self.createFixedTitledRow(group, 'Influence Association %d' % (index+1))
            self.controls.__dict__['influenceAssoc%d' % (index+1)] = DropDownField(self.VAR_PREFIX+'influenceAssoc%d' % (index+1))
            self.controls.__dict__['influenceAssoc%d' % (index+1)].beginRebuildItems()
            if index:
                # 2nd and 3rd options are set to "None" by default
                self.controls.__dict__['influenceAssoc%d' % (index+1)].addOption('None')
            self.controls.__dict__['influenceAssoc%d' % (index+1)].addOption('Closest joint')
            self.controls.__dict__['influenceAssoc%d' % (index+1)].addOption('Closest bone')
            self.controls.__dict__['influenceAssoc%d' % (index+1)].addOption('One to one')
            self.controls.__dict__['influenceAssoc%d' % (index+1)].addOption('Label')
            self.controls.__dict__['influenceAssoc%d' % (index+1)].addOption('Name')
            self.controls.__dict__['influenceAssoc%d' % (index+1)].endRebuildItems()

        
    def updateLayoutEnabled(self):
        '''
        '''
    
    def copySkinLayers(self, *args):
        '''
        '''
        uv = None
        #=======================================================================
        # get layers that we want to copy
        #=======================================================================
        
        # print 'selLayers: ', self.controls.selLayers.getValue()
        if self.controls.selLayers.getValue():
            # if set to "Selected layers in lister"
            layerLister = MainWindow.getInstance().targetUI.layersUI.getSelectedLayers()
            # print 'LayerLister: ', layerLister
        else:
            # use all layers
            layerLister = []
        
        #===================================================================
        # surface association
        #===================================================================
        if self.controls.radioClosestPoint.getValue():
            surfaceAssociation = 'closestPoint'
        elif self.controls.radioRaycast.getValue():
            surfaceAssociation = 'rayCast'
        elif self.controls.radioClosestComponent.getValue():
            surfaceAssociation = 'closestComponent'
        elif self.controls.radioUVSpace.getValue():
            surfaceAssociation = 'closestPoint'
            uvSets = mc.polyUVSet(q=True, currentUVSet=True)
            if len(uvSets) > 0:
                srcSet = uvSets[0]
                destSet = uvSets[-1]
                uv = srcSet, destSet
        else:
            mc.warning('Unknown surface association')
            
        sampleSpace = self.controls.sampleSpace.getValue()
        
        #=======================================================================
        # influence association
        #=======================================================================
        associationNameMap = {'None': None,
                            'Closest joint': 'closestJoint',
                            'Closest bone': 'closestBone',
                            'One to one': 'oneToOne',
                            'Label': 'label',
                            'Name': 'name'}
        
        influenceAssociation = []
        for index in range(3):
            association = self.controls.__dict__['influenceAssoc%d' % (index+1)].getSelectedText()
            influenceAssociation.append(associationNameMap[association])
        
        normalize = 1 - self.controls.normalization.getValue()
        
        '''
        print surfaceAssociation
        print sampleSpace
        print influenceAssociation
        print layerLister
        print normalize
        '''
        
        sel = mc.ls(os=True)
        if len(sel) == 2:
            srcMeshName, destMeshName = sel[:2]
        else:
            mc.error('Select source mesh, then shift-select destination mesh.')
        
        args = [srcMeshName, destMeshName, layerLister, 
               influenceAssociation, surfaceAssociation, 
               sampleSpace, normalize]
        
        if uv:
            args.append(uv)
        
        copySkinLayers(*args)
        
        mc.select(destMeshName)
        
    def closeWindow(self, *args):
        '''
        '''
        self.parentWindow.closeWindow()

#===============================================================================
# UTILITIES
#===============================================================================

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
     
     
def setInfluenceWeight(skn, mesh, influenceName, weightList):
    '''
    Set weights on influence using a float list
    '''
    for vertId in range(len(weightList)):
        if weightList[vertId]:
            mc.skinPercent(skn, mesh+'.vtx[%d]'%vertId, transformValue=[influenceName, weightList[vertId]])


def copySkinLayers(srcMeshName, destMeshName, layers, influenceAssociation, surfaceAssociation, sampleSpace, normalize, uv=None):
    '''
    layers [list] - ids of layers to be copied
    if layers is [], all layers will be copied
    '''
    srcMll = MllInterface()
    destMll = MllInterface()
    
    srcMll.setCurrentMesh(srcMeshName)
    destMll.setCurrentMesh(destMeshName)
    
    # check that selected objects are valid
    if False in (srcMll.getLayersAvailable(), destMll.getLayersAvailable()):
        mc.error("Skinning layers must be initialized on both source and destination meshes")
    
    if layers == []:
        layers = [layerId for layerId, _ in srcMll.listLayers()]
        layers.reverse()
        
    for eachLayer in layers:
        copySkinLayerById(srcMll, destMll, eachLayer, influenceAssociation, surfaceAssociation, sampleSpace, normalize, uv)
     

def copySkinLayerById(srcMll, destMll, srcLayerId, influenceAssociation, surfaceAssociation, sampleSpace, normalize, uv=None):
    '''
    Actual work is done here. Copies an individual layer from srcMll to destMll
    '''
    
    layerName = getLayerName(srcMll, srcLayerId)

    mc.progressWindow(title='Copy layer: %s' % layerName,
                      progress=0, min=0, max=6,
                      status='Get layer mask')
    
    srcMeshName, srcSkn = srcMll.getTargetInfo()
    destMeshName, destSkn = destMll.getTargetInfo()
    
    # parse args
    kwargs = {'ss': srcSkn,
              'ds': destSkn, 
              'ia': influenceAssociation, 
              'sa': surfaceAssociation,
              'spa': sampleSpace, 
              'nr': normalize,
              'nm': True}
    
    if uv:
        kwargs['uv'] = uv
    
    # check that selected objects are valid
    if False in (srcMll.getLayersAvailable(), destMll.getLayersAvailable()):
        mc.error("Skinning layers must be initialized on both source and destination meshes")
    
    # solo layer on srcMesh
    disableLayers = soloLayer(srcMll, srcLayerId)
    
    # save mask weights
    origMaskWeights = srcMll.getLayerMask(srcLayerId)
    
    # temporarily flood mask to 1, so that we can transfer all the data inside this layer
    srcMll.setLayerMask(srcLayerId, [])
    
    #===========================================================================
    # Transfer influence weights
    #===========================================================================
    mc.progressWindow(e=True, status='Get influence weights', step=1)
    
    # use maya's copySkinWeights command to transfer weights
    mc.copySkinWeights(**kwargs)
    
    # query and catch weights
    mc.progressWindow(e=True, status='Transfer influence weights', step=1)
    destInfluenceWeights = queryWeights(destSkn, destMeshName)
    
    #===========================================================================
    # Transfer mask weights
    # This is very messed up, but it's the simplest workaround I can think of...
    # Basically, we create a new joint "tempSkinLayerMaskTransferer_jnt" bound to both skins
    # This ensures that we can transfer the mask weights by joint name,
    # even if influence weights are transfered by other methods
    #===========================================================================
    
    mc.select(cl=True)
    mc.progressWindow(e=True, status='Transfer layer mask', step=1)
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
        kwargs['ia'] = 'name'
        mc.copySkinWeights(**kwargs)
        
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
    mc.progressWindow(e=True, status='Set influence weights', step=1)
    destLayerId = destMll.createLayer(layerName, forceEmpty=True)
    
    influenceCount = len(mc.skinCluster(destSkn, q=True, inf=True))
    
    layerInfluences = list(destMll.listLayerInfluences(destLayerId, False))
    if len(layerInfluences) != influenceCount:
        mc.error('SkinCluster %s has %d influences. But SkinLayer has %s influences.\
                Try rebinding this mesh.' % (destSkn, influenceCount, len(layerInfluences)))
    
    # set influence weights
    for influenceId in range(influenceCount):
        weights = destInfluenceWeights[influenceId]
        layerInfluenceId = layerInfluences[influenceId][1]
        # check if the influence has non-zero values, to reduce number of calls
        if not all(val==0 for val in weights):
            destMll.setInfluenceWeights(destLayerId, layerInfluenceId, weights)
        
    # set mask weights
    mc.progressWindow(e=True, status='Set layer mask', step=1)
    destMll.setLayerMask(destLayerId, destMaskWeights)
    
    mc.progressWindow(endProgress=True)
    
    print 'Sucessfully copied layer %s' % layerName