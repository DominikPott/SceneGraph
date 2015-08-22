#!/usr/bin/env python
import os
from PySide import QtCore, QtGui
from functools import partial
from SceneGraph import core
from SceneGraph.options import SCENEGRAPH_PREFS_PATH


class PluginManager(QtGui.QMainWindow):
    def __init__(self, parent=None, plugins=[]):
        QtGui.QMainWindow.__init__(self, parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.fonts          = dict()
        self.settings_file  = os.path.join(SCENEGRAPH_PREFS_PATH, 'SceneGraph.ini')
        self._valid_plugins = []

        if parent is not None:
            self.plugin_manager = parent.graph.pm
            self.qsettings = parent.qsettings
            self._valid_plugins = parent._valid_plugins

        else:
            graph = core.Graph()
            self.plugin_manager = graph.pm

            # todo: messy haxx
            from SceneGraph.ui import stylesheet
            from SceneGraph.ui import settings
            self.stylesheet = stylesheet.StyleManager(self)
            style_data = self.stylesheet.style_data()
            self.setStyleSheet(style_data)
            self.qsettings = settings.Settings(self.settings_file, QtCore.QSettings.IniFormat, parent=self)
            self.readSettings()

            if self._valid_plugins:
                for plugin in self.plugin_manager.node_types():
                    if plugin not in self._valid_plugins:
                        self.plugin_manager.node_types().get(plugin).update(enabled=False)

        self.setupFonts()
        
        self.centralwidget = QtGui.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.pluginsGroup = QtGui.QGroupBox(self.centralwidget)
        self.pluginsGroup.setObjectName("pluginsGroup")
        self.pluginsGroupLayout = QtGui.QHBoxLayout(self.pluginsGroup)
        self.pluginsGroupLayout.setSpacing(6)
        self.pluginsGroupLayout.setContentsMargins(9, 9, 9, 9)
        self.pluginsGroupLayout.setObjectName("pluginsGroupLayout")
        self.pluginsInfoLayout = QtGui.QVBoxLayout()
        self.pluginsInfoLayout.setSpacing(9)
        self.pluginsInfoLayout.setContentsMargins(9, 9, 9, 9)
        self.pluginsInfoLayout.setObjectName("pluginsInfoLayout")

        # table view
        self.pluginView = TableView(self.pluginsGroup)
        self.pluginView.setObjectName("pluginView")
        self.pluginsInfoLayout.addWidget(self.pluginView)
        self.controlsLayout = QtGui.QHBoxLayout()
        self.controlsLayout.setObjectName("controlsLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.controlsLayout.addItem(spacerItem)
        self.check_show_all = QtGui.QCheckBox(self.pluginsGroup)
        self.check_show_all.setObjectName("check_show_all")
        self.controlsLayout.addWidget(self.check_show_all)
        self.pluginsInfoLayout.addLayout(self.controlsLayout)
        self.pluginInfo = QtGui.QPlainTextEdit(self.pluginsGroup)
        self.pluginInfo.setObjectName("pluginInfo")
        self.pluginInfo.setProperty("class", "Console")
        self.pluginsInfoLayout.addWidget(self.pluginInfo)
        self.pluginsInfoLayout.setStretch(0, 1)
        self.pluginsInfoLayout.setStretch(2, 1)
        self.pluginsGroupLayout.addLayout(self.pluginsInfoLayout)
        self.pluginButtonsLayout = QtGui.QVBoxLayout()
        self.pluginButtonsLayout.setSpacing(4)
        self.pluginButtonsLayout.setObjectName("pluginButtonsLayout")
        self.button_disable = QtGui.QToolButton(self.pluginsGroup)
        self.button_disable.setMinimumSize(QtCore.QSize(75, 0))
        self.button_disable.setObjectName("button_disable")
        self.pluginButtonsLayout.addWidget(self.button_disable)
        self.button_reload = QtGui.QToolButton(self.pluginsGroup)
        self.button_reload.setMinimumSize(QtCore.QSize(75, 0))
        self.button_reload.setObjectName("button_reload")
        self.pluginButtonsLayout.addWidget(self.button_reload)
        self.button_load = QtGui.QToolButton(self.pluginsGroup)
        self.button_load.setMinimumSize(QtCore.QSize(75, 0))
        self.button_load.setObjectName("button_load")
        self.pluginButtonsLayout.addWidget(self.button_load)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.pluginButtonsLayout.addItem(spacerItem1)
        self.pluginsGroupLayout.addLayout(self.pluginButtonsLayout)
        self.verticalLayout.addWidget(self.pluginsGroup)
        self.buttonBox = QtGui.QDialogButtonBox(self.centralwidget)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 805, 25))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        # table model
        self.tableModel = PluginTableModel(parent=self)
        self.pluginView.setModel(self.tableModel)
        self.tableSelectionModel = self.pluginView.selectionModel()
        
        self.initializeUI()
        self.connectSignals()
        self.checkPlugins()

    def initializeUI(self):
        """
        Setup the main UI
        """
        self.setWindowTitle("SceneGraph Plugin Manager")
        self.pluginsGroup.setTitle("Loaded Plugins")
        self.button_disable.setText("Disable")
        self.button_reload.setText("Reload")
        self.button_load.setText("Load...")
        self.check_show_all.setText("show core plugins")

        # NYI
        self.button_load.setEnabled(False)

    def connectSignals(self):
        """
        Setup widget signals.
        """
        self.button_disable.clicked.connect(self.disabledAction)
        self.button_reload.clicked.connect(self.reloadAction)
        self.buttonBox.accepted.connect(self.acceptedAction)
        self.buttonBox.rejected.connect(self.close)
        self.check_show_all.toggled.connect(self.toggleShowAllAction)
        self.tableSelectionModel.selectionChanged.connect(self.tableSelectionChanged)
        #self.pluginView.viewport().mouseMoveEvent()

    def reloadAction(self):
        show_all = self.check_show_all.isChecked()
        self.checkPlugins(show_all)

    def toggleShowAllAction(self, val):
        self.checkPlugins(val)

    def checkPlugins(self, show_all=False):
        """
        Build the table.

        :param bool show_all: show core plugins as well as builtins.
        """
        data = []
        plugins = self.plugin_manager._plugin_data
        self.tableModel.clear()

        for pname in plugins:
            plugin_type = plugins.get(pname).get('plugin_type', None)

            # don't allow core plugins to be disabled
            if plugin_type == 'core' and not show_all:
                continue 

            pattrs = plugins.get(pname)
            dagnode = pattrs.get('dagnode', None)
            src = pattrs.get('source')
            enabled = pattrs.get('enabled')
            pclass = pattrs.get('class')
            widget = pattrs.get('widget').__name__
            category = pattrs.get('category')

            if dagnode is not None:
                dagnode=dagnode.__name__
            
            widget = pattrs.get('widget', None)
            if widget is not None:
                widget=widget.__name__

            metadata = pattrs.get('metadata', None)
            data.append([pname, plugin_type, pclass, category, dagnode, widget, enabled])

        self.tableModel.addPlugins(data)

    def selectedPlugins(self):
        """
        :returns: list of plugin attributes.
        :rtype: list
        """
        if not self.tableSelectionModel.selectedRows():
            return []
        plugins = []
        for i in self.tableSelectionModel.selectedRows():
            plugins.append(self.tableModel.plugins[i.row()])
        return plugins

    def tableSelectionChanged(self):
        """
        Runs when the selection changes.
        """
        plugins = self.selectedPlugins()

        enabled = True
        is_core = False
        if plugins:
            for plugin in plugins:
                plugin_type = plugin[self.tableModel.PLUGIN_CLASS_ROLE]
                plugin_name = plugin[self.tableModel.PLUGIN_NAME_ROLE]

                if not plugin[self.tableModel.PLUGIN_ENABLED_ROLE]:
                    enabled = False
                if plugin_type == 'core':
                    is_core = True

        button_text = 'Disable'
        if not enabled:
            button_text = 'Enable'

        self.button_disable.setText(button_text)
        self.buildPluginInfo(plugins)

        self.button_disable.setEnabled(not is_core)

    def disabledAction(self):
        indexes = self.tableSelectionModel.selectedRows()
        plugins = self.selectedPlugins()
        if plugins:
            for plugin in plugins:
                plugin_name = plugin[self.tableModel.PLUGIN_NAME_ROLE]
                enabled = bool(plugin[self.tableModel.PLUGIN_ENABLED_ROLE])

                self.plugin_manager.enable(plugin_name, not enabled)
                self.checkPlugins(self.check_show_all.isChecked())

        self.tableSelectionModel.clearSelection()

        for i in indexes:
            self.tableSelectionModel.select(i, QtGui.QItemSelectionModel.Select)

    def acceptedAction(self):
        self.writeSettings()
        self.close()

    def readSettings(self):
        """
        Read settings from disk.
        """
        self.qsettings.beginGroup("Preferences")
        # update valid plugin types
        plugins = self.qsettings.value("plugins")
        if plugins:
            if type(plugins) in [str, unicode]:
                plugins = [plugins,]
            for plugin in plugins:
                if plugin not in self._valid_plugins:
                    self._valid_plugins.append(plugin)
        self.qsettings.endGroup()

    def writeSettings(self):
        """
        Write settings to disk.
        """
        self._valid_plugins = self.plugin_manager.valid_plugins
        self.qsettings.beginGroup('Preferences')
        self.qsettings.setValue('plugins', self.plugin_manager.valid_plugins)
        self.qsettings.endGroup()

    def sizeHint(self):
        return QtCore.QSize(800, 500)

    def setupFonts(self, font='SansSerif', size=9):
        """
        Initializes the fonts attribute
        """
        self.fonts = dict()
        self.fonts["ui"] = QtGui.QFont(font)
        self.fonts["ui"].setPointSize(size)

        self.fonts["mono"] = QtGui.QFont('Monospace')
        self.fonts["mono"].setPointSize(size)

        self.fonts["disabled"] = QtGui.QFont(font)
        self.fonts["disabled"].setPointSize(size)
        self.fonts["disabled"].setItalic(True)

    def buildPluginInfo(self, plugins=[]):
        """
        Builds the plugin info for the selected plugins.
        """
        self.pluginInfo.clear()
        if not plugins:
            return

        plug_detail = "(%d plugins selected)" % len(plugins)

        if len(plugins) is 1:
            pattrs =plugins[0]

            pname = pattrs[0]  # plugin name
            pptype = pattrs[1] # plugin type


            for node_name in  self.plugin_manager._plugin_data:
                if node_name == pname:
                    node_attrs = self.plugin_manager._plugin_data.get(node_name)

                    dagnode = node_attrs.get('dagnode').__name__
                    src_file = node_attrs.get('source')
                    node_class = node_attrs.get('class')
                    plugin_type = node_attrs.get('plugin_type')
                    node_category = node_attrs.get('category')
                    widget = node_attrs.get('widget').__name__
                    
                    
                    plug_detail = """Plugin Detail:

Node:   %s
Widget: %s
Type:   %s
Class:  %s
Source: %s

""" % (dagnode, widget, plugin_type, node_class, src_file)
        
        self.pluginInfo.setPlainText(plug_detail)


class TableView(QtGui.QTableView):

    def __init__(self, parent=None, **kwargs):
        QtGui.QTableView.__init__(self, parent)

        # attributes
        self._last_indexes  = []              # stash the last selected indexes

        self.installEventFilter(self)
        self.verticalHeader().setDefaultSectionSize(17)
        
        self.setShowGrid(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultAlignment(QtCore.Qt.Alignment())
        self.verticalHeader().setVisible(False)

        self.fileSizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.fileSizePolicy.setHorizontalStretch(0)
        self.fileSizePolicy.setVerticalStretch(0)
        self.fileSizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(self.fileSizePolicy)

        #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtGui.QTableView.SelectRows)
        self.setIconSize(QtCore.QSize(16, 16))
        self.setShowGrid(False)
        self.setGridStyle(QtCore.Qt.NoPen)
        self.setSortingEnabled(False)
        self.verticalHeader().setDefaultSectionSize(18)  # 24
        self.verticalHeader().setMinimumSectionSize(18)  # 24

        # dnd
        self.setDragEnabled(True)
        self.setDragDropMode(QtGui.QAbstractItemView.DragOnly)

        # context Menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def getSelectedIndexes(self):
        """
        :returns: selected indexes.
        :rtype: list
        """
        return self.selectionModel().selectedIndexes()

    def getSelectedRows(self):
        """
        :returns: selected rows.
        :rtype: list
        """
        return self.selectionModel().selectedRows()

    def focusOutEvent(self, event):
        if self.selectionModel().selectedIndexes():
            for index in self.selectionModel().selectedRows():
                self._last_indexes.append(QtCore.QPersistentModelIndex(index))

        if self._last_indexes:
            for i in self._last_indexes:
                self.selectionModel().setCurrentIndex(i, QtGui.QItemSelectionModel.Select)
        event.accept()



class PluginTableModel(QtCore.QAbstractTableModel):   

    PLUGIN_NAME_ROLE        = 0    
    PLUGIN_CLASS_ROLE       = 1
    PLUGIN_DAGNODE_ROLE     = 2
    PLUGIN_TYPE_ROLE        = 3 
    PLUGIN_CATEGORY_ROLE    = 4 
    PLUGIN_WIDGET_ROLE      = 5    
    PLUGIN_ENABLED_ROLE     = 6

    def __init__(self, nodes=[], headers=['Node Type', 'Plugin Type', 'Plugin Class', 'Category', 'DagNode', 'Widget',  'Enabled'], parent=None, **kwargs):
        QtCore.QAbstractTableModel.__init__(self, parent)

        self.fonts      = parent.fonts
        self.plugins    = nodes
        self.headers    = headers

    def rowCount(self, parent):
        return len(self.plugins)

    def columnCount(self, parent):
        return len(self.headers)

    def insertRows(self, position, rows=1, index=QtCore.QModelIndex()):
        self.beginInsertRows(QtCore.QModelIndex(), position, position + rows - 1)
        #for row in range(rows):
        #    self.nodes.insert(position + row, Asset())
        self.endInsertRows()
        self.dirty = True
        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):        
        self.beginRemoveRows(parent, position, position + rows - 1)
        self.endRemoveRows()
        return True

    def insertColumns(self, position, columns, parent = QtCore.QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1) 
        self.endInsertColumns()        
        return True

    def removeColumns(self, position, columns, parent = QtCore.QModelIndex()):
        self.beginRemoveColumns(parent, position, position + columns - 1) 
        self.endRemoveColumns()        
        return True

    def clear(self):
        if len(self.plugins) == 1:
            self.removeRows(0, 1)
        else:
            self.removeRows(0, len(self.plugins)-1)
        self.plugins=[]

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        plugin = self.plugins[index.row()]
        self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        return 1

    def data(self, index, role):
        row     = index.row()
        column  = index.column()
        plugin  = self.plugins[row]

        is_enabled = plugin[self.PLUGIN_ENABLED_ROLE]


        if role == QtCore.Qt.DisplayRole:
            if column == self.PLUGIN_NAME_ROLE:
                return plugin[self.PLUGIN_NAME_ROLE]

            if column == self.PLUGIN_DAGNODE_ROLE:
                return plugin[self.PLUGIN_DAGNODE_ROLE]

            if column == self.PLUGIN_TYPE_ROLE:
                return plugin[self.PLUGIN_TYPE_ROLE]

            if column == self.PLUGIN_DAGNODE_ROLE:
                return plugin[self.PLUGIN_DAGNODE_ROLE]

            if column == self.PLUGIN_CLASS_ROLE:
                return plugin[self.PLUGIN_CLASS_ROLE]

            if column == self.PLUGIN_CATEGORY_ROLE:
                return plugin[self.PLUGIN_CATEGORY_ROLE]

            if column == self.PLUGIN_WIDGET_ROLE:
                return plugin[self.PLUGIN_WIDGET_ROLE]

            if column == self.PLUGIN_ENABLED_ROLE:
                return plugin[self.PLUGIN_ENABLED_ROLE]

        elif role == QtCore.Qt.FontRole:
            font = self.fonts.get("ui")
            if not is_enabled:
                font = self.fonts.get("disabled")
            return font

        elif role == QtCore.Qt.ForegroundRole:            
            brush = QtGui.QBrush()
            brush.setColor(QtGui.QColor(212, 212, 212))
            
            if not is_enabled:
                brush.setColor(QtGui.QColor(204, 82, 73))

            return brush

    def setHeaders(self, headers):
        self.headers=headers

    def headerData(self, section, orientation, role):  
        if role == QtCore.Qt.DisplayRole:            
            if orientation == QtCore.Qt.Horizontal:
                if int(section) <= len(self.headers)-1:
                    return self.headers[section]
                else:
                    return ''
            
    def addPlugins(self, plugins):
        """
        adds a list of tuples to the nodes value
        """
        self.insertRows(0, len(plugins)-1)
        self.plugins=plugins
        self.layoutChanged.emit()
    
    def addPlugin(self, plugin):
        """
        adds a single ndoe to the nodes value
        """
        self.insertRows(len(self.plugins)-1, len(self.plugins)-1)
        self.plugins.append(plugin)
        
    def getPlugins(self):
        return self.plugins

    def sort(self, col, order):
        """
        sort table by given column number
        """
        import operator
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        self.plugins = sorted(self.plugins, key=operator.itemgetter(col))        
        if order == QtCore.Qt.DescendingOrder:
            self.plugins.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))

