#!/usr/bin/env xpython
from PyQt4 import QtGui, QtCore
from functools import partial
import re


class NodeAttributesWidget(QtGui.QWidget):

    def __init__(self, parent=None, **kwargs):
        QtGui.QWidget.__init__(self, parent)
        
        self._gui           = kwargs.get('gui', None)
        self.manager        = kwargs.get('manager')
        self._current_node  = None                              # the currently selected node
        self.gridLayout     = QtGui.QGridLayout(self)
        
    
    def setNode(self, node_item):
        """
        Set the currently focused node
        """
        if node_item:
            node_item.nodeChanged.connect(partial(self.setNode, node_item))
            
            # clear the layout
            self._clearGrid()                
            
            self.nameLabel = QtGui.QLabel(self)
            self.gridLayout.addWidget(self.nameLabel, 0, 0, 1, 1)
            self.nameEdit = QtGui.QLineEdit(self)
            self.gridLayout.addWidget(self.nameEdit, 0, 1, 1, 1)
    
            self.pathLabel = QtGui.QLabel(self)
            self.gridLayout.addWidget(self.pathLabel, 1, 0, 1, 1)
            self.pathEdit = QtGui.QLineEdit(self)
            self.gridLayout.addWidget(self.pathEdit, 1, 1, 1, 1)
    
            self.__current_row = 2
    
            self.nameLabel.setText("Name:")
            self.nameLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
            self.pathLabel.setText("Path:")
            self.pathLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
            
            self._current_node = node_item
            self.nameEdit.setText(node_item.node_name)
            self.nameEdit.textEdited.connect(self.nodeUpdatedFilter)
            self.nameEdit.editingFinished.connect(self.nodeFinalizedFilter)

            # disable this attribute if the node is root
            if node_item._is_root:
                self.nameEdit.setEnabled(False)

            self.pathEdit.setText(node_item.path())
            self.pathEdit.setEnabled(False)
                        
            for attr, val in node_item.getNodeAttributes().iteritems():
                if attr not in node_item._private:
                    attr_label = QtGui.QLabel(self)
                    self.gridLayout.addWidget(attr_label, self.__current_row, 0, 1, 1)
                    val_edit = QtGui.QLineEdit(self)
                    self.gridLayout.addWidget(val_edit, self.__current_row, 1, 1, 1)
                    
                    attr_label.setText('%s: ' % attr)
                    attr_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
                    val_edit.setText(str(val))
                    self.__current_row+=1
                    val_edit.editingFinished.connect(partial(self.updateNodeAttribute, val_edit, attr))
                
            spacerItem = QtGui.QSpacerItem(20, 178, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
            self.gridLayout.addItem(spacerItem, self.__current_row, 1, 1, 1)

    
    def updateAttributes(self):
        """
        Dynamically add attributes from a node
        """
        self.deleteGridWidget(self.__current_row, 1)

    def nodeUpdateAction(self):
        """
        Update the current node
        """
        new_name = str(self.nameEdit.text())
        if self._current_node:
            newNode = self.manager.renameNode(self._current_node.node_name, new_name)
            self.setNode(newNode)
    
    def updateNodeAttribute(self, lineEdit, attribute):
        """
        Update the node from an attribute
        """
        self._current_node.addNodeAttributes(**{attribute:str(lineEdit.text())})
        self.setNode(self._current_node)
    
    def nodeUpdatedFilter(self):
        """
        Runs when the task description (token) is updated
        """
        cur_val = re.sub('^_', '', str(self.nameEdit.text()).replace(' ', '_'))
        cur_val = re.sub('__', '_', cur_val)
        self.nameEdit.setText(cur_val)

    def nodeFinalizedFilter(self):
        """
        Runs when the task description (token) editing is finished
        """
        cur_val = str(self.nameEdit.text())
        cur_val = re.sub('^_', '', cur_val)
        cur_val = re.sub('_$', '', cur_val)        
        self.nameEdit.setText(cur_val)
        self.nodeUpdateAction()

    def _clearGrid(self):
        """
        Clear the current grid
        """
        if self.gridLayout:
            for r in range(self.gridLayout.rowCount()):
                self.deleteGridWidget(r, 0)
                self.deleteGridWidget(r, 1)

    def deleteGridWidget(self, row, column):
        """
        Remove a widget
        """
        item = self.gridLayout.itemAtPosition(row, column)
        if item is not None:
            widget = item.widget()
            if widget is not None:
                self.gridLayout.removeWidget(widget)
                widget.deleteLater()