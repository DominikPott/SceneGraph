#!/usr/bin/env python
from SceneGraph.ui.node_widgets import NodeWidget


class LookdevWidget(NodeWidget):
    widget_type  = 'lookdev'
    def __init__(self, dagnode, parent=None):
        super(LookdevWidget, self).__init__(dagnode, parent)