#!/usr/bin/env python
from SceneGraph.ui import NodeWidget


SCENEGRAPH_WIDGET_TYPE = 'texture'


class TextureWidget(NodeWidget): 
    def __init__(self, dagnode, parent=None):
        super(TextureWidget, self).__init__(dagnode, parent)
        