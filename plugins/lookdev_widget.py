#!/usr/bin/env python
from SceneGraph.ui.node_widgets import NodeWidget


class LookdevWidget(NodeWidget):
    widget_type  = 'lookdev'
    node_class   = 'container'
    def __init__(self, dagnode, parent=None):
        NodeWidget.__init__(self, dagnode, parent)