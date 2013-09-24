'''
Created on 01/09/2013

@author: Leon
'''
import pymel.core as pm

class SurfaceAssociation():
    '''
    classdocs
    '''


    def __init__(self, srcMesh, destMesh, method):
        '''
        Constructor
        '''
        
        # create dictionary with the format -
        # {vertexId on srcMesh : ((vertexId1 on destMesh, weight), (vertexId2 on destMesh, weight)...), ...}
        self.matchDict = {}
        
        # convert to PyNodes
        srcMesh = pm.PyNode(srcMesh)
        destMesh = pm.PyNode(destMesh)
        
        if method == 'closestComponent':
            self.matchByClosestComponent(srcMesh, destMesh)
            
            
    def matchByClosestComponent(self, srcMesh, destMesh):
        '''
        populate self.matchDict
        '''
        

        
        
        