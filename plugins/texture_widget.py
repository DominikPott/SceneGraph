#!/usr/bin/env python
from SceneGraph.ui.node_widgets import NodeWidget


class TextureWidget(NodeWidget):
    widget_type  = 'texture'
    def __init__(self, dagnode, parent=None):
        super(TextureWidget, self).__init__(dagnode, parent)
        