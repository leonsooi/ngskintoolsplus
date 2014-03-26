'''
Created on Mar 22, 2014

@author: Leon
'''

import maya.cmds as mc

# assign weights by nearest joint
args = {}
args['bnj'] = True
selJnts = ['joint1', 'joint2']
args['ij'] = '/'.join(selJnts)
args['intensity'] = 1.0

# must select mesh or components first
# must select layer or mll.setCurrentLayer(layerId)
mc.ngAssignWeights(**args)

selJnts = []
mc.ngAssignWeights(bnj=True, ij='/'.join(selJnts), intensity=1.0)