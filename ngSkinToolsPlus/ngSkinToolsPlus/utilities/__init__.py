from ngSkinTools.mllInterface import MllInterface
from ngSkinTools.importExport import LayerData, Layer, Influence
from ngSkinTools.importExport import XmlImporter
import maya.cmds as cmds

import pymel.core as pm

'''
Quick hacks just to get the job done when needed. Should be modularized properly some time...
'''

'''
USEFUL UTILITIES
'''

def soloLayer(mll, layerId):
    '''
    enabled layerId, disables the rest
    '''
    allLayers = mll.listLayers()
    
    for curLayerId, _layerName in allLayers:
        mll.setLayerEnabled(curLayerId, layerId==curLayerId)
    

def unifyMask(vertsList, mll, layerId):
    '''
    average mask weights on vertsList
    '''
    maskWts = mll.getLayerMask(layerId)
    vertsNum = len(vertsList)
    vertsWeights = [maskWts[vertId] for vertId in vertsList]
    avgWeight = sum(vertsWeights)/vertsNum
    for vertId in vertsList:
        maskWts[vertId] = avgWeight
    mll.setLayerMask(layerId, maskWts)
    
def reverseMask(mll, layerId):
    '''
    '''
    maskWts = mll.getLayerMask(layerId)
    revMaskWts = [1-wt for wt in maskWts]
    mll.setLayerMask(layerId, revMaskWts)
    
    
    
'''
utilities to print out layer data (for troubleshooting purposes, etc)
also, if the influence long names have changed
we can use this to find match influences by shortName, and update the longNames
obviously, it assumes that names are unique!
'''
def loadXmlFile(filepath):
    '''
    # example process for importing XML data
    filepath = r"C:\Users\Leon\Documents\maya\projects\Ori\scenes\ori_body_weights_v037.xml"
    xml = loadXmlFile(filepath)
    from ngSkinTools.importExport import XmlImporter
    # create layers from
    importer = XmlImporter()
    # load layer data
    data = importer.process(xml)
    '''
    f = open(filepath, 'r')
    try:
        contents = ''.join(f.readlines())
    finally:
        f.close();
    
    importer = XmlImporter()
    data = importer.process(contents)
    return data

def findUnmatchedInfluences(data, printOut=True):
    '''
    parse data and find unmatchable influences
    
    findUnmatchedInfluences(data)
    '''
    unmatched = []
    for influence in data.getAllInfluences():
        if not pm.objExists(influence):
            unmatched.append(influence.split('|')[-1])
    if printOut:
        print unmatched
    return unmatched

def matchInfluencesByNodeName(data):
    '''
    match influences by nodeName
    assumes all influence names are unique
    
    matchInfluencesByNodeName(data)
    data.saveTo('GEO:CT_body_geo')
    '''
    for layer in data.layers:
        for influence in layer.influences:
            oldLongName = influence.influenceName
            shortName = oldLongName.split('|')[-1]
            newLongName = cmds.ls(shortName, l=True)[0]
            influence.influenceName = newLongName

def editJson(jsonDict):
    for eachLayer in jsonDict["layers"]:
        print eachLayer["name"]
        for eachInf in eachLayer["influences"]:
            print eachInf["name"]
            name = eachInf["name"]
            shortName = name.split('|')[-1]
            print shortName
            replacedName = shortName.replace('CT_', 'CT_lips_')
            replacedName = shortName.replace('LT_', 'LT_lips_')
            replacedName = shortName.replace('RT_', 'RT_lips_')
            eachInf["name"] = replacedName

def editLayerData(data):
    for eachLayer in data.layers:
        print eachLayer.name
        for eachInfluence in eachLayer.influences:
            print eachInfluence.influenceName
            oldLongName = eachInfluence.influenceName
            oldShortName = oldLongName.split('|')[-1]
            print oldShortName
            newShortName = oldShortName.replace('T_', 'T_lips_')
            print newShortName
            newLongName = cmds.ls(newShortName, l=True)[0]
            print newLongName
            eachInfluence.influenceName = newLongName

def selectInfluencesInLayerData(data):
    cmds.select(cl=True)
    for eachLayer in data.layers:
        print eachLayer.name
        for eachInfluence in eachLayer.influences:
            print eachInfluence.influenceName
            cmds.select(eachInfluence.influenceName, add=True)

def retModel(jsonDict):
    model = LayerData()
    
    if jsonDict.has_key("manualInfluenceOverrides"):
        model.mirrorInfluenceAssociationOverrides = jsonDict['manualInfluenceOverrides']
    
    for layerData in jsonDict["layers"]:
        layer = Layer()
        model.addLayer(layer)        
        layer.enabled = layerData['enabled']
        layer.mask = layerData['mask']
        layer.name = layerData['name']
        layer.opacity = layerData['opacity']
        layer.influences = []

        for influenceData in layerData['influences']:
            influence = Influence()
            layer.addInfluence(influence)
            influence.weights = influenceData['weights']
            influence.logicalIndex = influenceData['index']
            influence.influenceName = influenceData['name']
    
    return model