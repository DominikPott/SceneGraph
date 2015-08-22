#!/usr/bin/env python
from SceneGraph.ui.node_widgets import NodeWidget


class MergeWidget(NodeWidget):
    widget_type  = 'merge'
    def __init__(self, dagnode, parent=None):
        super(MergeWidget, self).__init__(dagnode, parent)

