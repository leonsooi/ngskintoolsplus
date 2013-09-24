'''
Created on 01/09/2013

@author: Leon
'''

class InfluenceAssociation():
    '''
    classdocs
    '''

    def __init__(self, srcInfluences, destInfluences, method):
        '''
        srcInfluences and destInfluences are iterators returned
        from mll.listLayerInfluences(layerId, activeInfluences=False)
        (activeInfluences should be set to False, in case we
        need to match to influences that are currently inactive.)
        
        method - match by "name", "label", "closestJoint",
                            "closestBone", or "oneToOne"
        '''
        
        # create a dictionary with the format -
        # {influenceIndex on srcMll : influenceIndex on destMll,...}
        self.matchDict = {}
        
        if method == 'name':
            self.matchByName(srcInfluences, destInfluences)
            
    
    def matchByName(self, srcInfluences, destInfluences):
        '''
        '''
        srcDict = {}
        for influenceName, influenceIndex in srcInfluences:
            srcDict[influenceIndex] = influenceName
        
        destDict = {}
        for influenceName, influenceIndex in destInfluences:
            destDict[influenceName] = influenceIndex
        
        for influenceIndex, influenceName in srcDict.items():
            # search for the same name in destDict
            if influenceName in destDict.keys():
                # index of srcInfluence = index of destInfluence
                self.matchDict[influenceIndex] = destDict[influenceName]
                
    def __getitem__(self, srcIndex):
        return self.matchDict[srcIndex]
                