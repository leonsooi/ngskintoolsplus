'''
Created on 31/08/2013

@author: Leon
'''

from ngSkinTools.mllInterface import MllInterface
from ngSkinToolsPlus.utilities.influenceAssociation import InfluenceAssociation

import re

class CopyLayers:
    '''
    Copy layers across mesh utility
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.layerIds = []
        self.srcMll = MllInterface
        self.destMll = MllInterface
        self.copyIds = []
        
    def setMllInterface(self, srcMll, destMll):
        self.srcMll = srcMll
        self.destMll = destMll
    
    def copyLayer(self, layerId):
        '''
        copies single layer
        
        example use:
        testCopy = CopyLayers()
        srcMll = MllInterface()
        srcMll.setCurrentMesh('pPlane1')
        destMll = MllInterface()
        destMll.setCurrentMesh('pPlane3')
        
        testCopy.setMllInterface(srcMll, destMll)
        testCopy.copyLayer(3)
        '''
        oldName = self.srcMll.getLayerName(layerId)
        newLayer = self.destMll.createLayer(self.createUniqueName(oldName))
        self.destMll.setLayerMask(newLayer, self.srcMll.getLayerMask(layerId))
        
        influenceMatcher = InfluenceAssociation(self.srcMll.listLayerInfluences(layerId, True), self.destMll.listLayerInfluences(0, False), "name")
        
        for _, influenceIndex in self.srcMll.listLayerInfluences(layerId):
            weights = self.srcMll.getInfluenceWeights(layerId, influenceIndex)
            self.destMll.setInfluenceWeights(newLayer, influenceMatcher[influenceIndex], weights)
            
        self.copyIds.append(layerId)
    
    
    # two procedures copied from DuplicateLayers class
    # for getting a unique name for the new layer
    def createLayerName(self,oldName):
        prefix=" copy"
        
        # copy already? add index
        if oldName.endswith(prefix):
            return oldName+"(2)"
        
        # indexing exists? increase value
        s=re.search('(.*)\\((\\d+)\\)$',oldName)
        if s!=None:
            return s.group(1)+"(%d)"%(int(s.group(2))+1,) 
        
        # nothing? just add default copy prefix then
        return oldName+prefix
    
    def createUniqueName(self,fromName):
        layerNames = [l[1] for l in self.destMll.listLayers()]
        result = self.createLayerName(fromName)
        while result in layerNames:
            result = self.createLayerName(result)
            
        return result