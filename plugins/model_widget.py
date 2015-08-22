#!/usr/bin/env python
from SceneGraph.ui.node_widgets import NodeWidget


class ModelWidget(NodeWidget):
    widget_type  = 'model'
    def __init__(self, dagnode, parent=None):
        super(ModelWidget, self).__init__(dagnode, parent)

        