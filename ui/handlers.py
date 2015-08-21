#!/usr/bin/env python
from PySide import QtCore

from SceneGraph import core
from SceneGraph.ui import commands


log = core.log


class SceneEventHandler(QtCore.QObject):
    def __init__(self, parent=None, view=None):
        QtCore.QObject.__init__(self, parent)
   
        self.ui             = None    # reference to the parent MainWindow
        self.graph          = None    # reference to the Graph instance
        self._initialized   = False   # indicates the current scene has been read & built

        if parent is not None:
            self.ui = parent.ui

            if not self.connectGraph(parent, view):
                log.error('cannot connect SceneEventHandler to Graph.')

    def updateStatus(self, msg, level='info'):
        """
        Update the MainWindow's status bar.

        :param str msg: message to pass.
        :param str level: severity level.
        """
        self.ui.updateStatus(msg, level=level)

    @property 
    def scene(self):
        """
        Returns the parent GraphicsScene.

        :returns: parent GraphicsScene
        :rtype: `GraphicsScene`
        """
        return self.parent()

    @property 
    def view(self):
        """
        Returns the connected GraphicsView.

        :returns: connected GraphicsView
        :rtype: `GraphicsView`
        """
        return self.ui.view

    @property 
    def undo_stack(self):
        return self.ui.undo_stack

    def connectGraph(self, scene, view):
        """
        Connect the parent scenes' Graph object.

        :param GraphicsScene scene: current QGraphicsScene scene.

        :returns: connection was successful.
        :rtype: bool
        """
        if hasattr(scene, 'graph'):            
            graph = scene.graph
            if graph.mode == 'standalone':
                self.graph = graph
                self.graph.handler = self

                view.scaleChanged.connect(self.scaleChangedEvent)

                # connect graph signals
                self.graph.nodesAdded += self.nodesAddedEvent
                self.graph.edgesAdded += self.edgesAddedEvent
                self.graph.graphUpdated += self.graphUpdated
                self.graph.graphAboutToBeSaved += self.graphAboutToBeSaved
                self.graph.graphRefreshed += self.graphAboutToBeSaved

                self.graph.graphRead += self.graphReadEvent


                self.graph.mode = 'ui'
                log.info('SceneHandler: connecting Graph...')

                # load the node widgets from disk
                #self.graph.pm.load_widgets()

                # start the autosave timer for 2min (120s x 1000)
                self.ui.autosave_timer.start(30000)
                return True
        return False

    def resetScene(self):
        """
        .. note::
            - compatibility
            - deprecated
        """
        self.scene.clear()

    def graphReadEvent(self, graph, **kwargs):
        """
        Update the scene and ui with preferences read from a scene.

        :param Graph graph: Graph instance.
        """
        self._initialized = True

        if not self.ui.ignore_scene_prefs:
            self.ui.initializePreferencesPane(**kwargs)
            self.scene.updateScenePreferences(**kwargs)
            for attr, value in kwargs.iteritems():
                if hasattr(self.ui, attr):
                    setattr(self.ui, attr, value)

    def restoreGeometry(self, **kwargs):
        """
        Retore scene geometry.

        :param tuple pos: view center position.
        :param tuple scale: view zoom level.
        """
        pos = kwargs.pop('pos', (0.0, 0.0))
        scale = kwargs.pop('scale', (1.0, 1.0))

        self.view.resetTransform()
        self.view.centerOn(*pos)
        self.view.scale(*scale)

    #- Events ----

    def evaluate(self):
        return True

    def nodesAddedEvent(self, graph, ids):
        """
        Callback method.

        :param list ids: DagNode ids.
        """
        old_snapshot = self.graph.snapshot() 
        self.scene.addNodes(ids)
        # push a snapshot to the undo stack
        new_snapshot = self.graph.snapshot()
        self.undo_stack.push(commands.SceneNodesCommand(old_snapshot, new_snapshot, self.scene, msg='nodes added'))

    def edgesAddedEvent(self, graph, edges):
        """
        Callback method.
        """
        old_snapshot = self.graph.snapshot() 
        self.scene.addEdges(edges)

        # push a snapshot to the undo stack
        new_snapshot = self.graph.snapshot()
        self.undo_stack.push(commands.SceneNodesCommand(old_snapshot, new_snapshot, self.scene, msg='edges added'))

    def scaleChangedEvent(self, scale):
        """
        Runs when the scale changes in the viewport.
        """
        sx, sy = scale
        for node in self.scene.items():
            if hasattr(node, '_view_scale'):
                node._view_scale = sx * 0.5

    def removeSceneNodes(self, nodes):
        """
        Signal Graph when the scene is updated.

        .. todo::
            - not currently used.

        :param list nodes: list of widgets.
        """
        old_snapshot = self.graph.snapshot()      
        if not nodes:
            log.error('no nodes specified.')
            return False

        #print '# DEBUG: removing scene nodes...'
        for node in nodes:
            if self.scene:
                if self.scene.is_node(node):
                    dag = node.dagnode
                    nid = dag.id
                    if self.graph.remove_node(nid):
                        log.debug('removing dag node: %s' % nid)
                    node.close()

            if self.scene.is_edge(node):
                if node.ids in self.graph.network.edges():
                    log.debug('removing edge: %s' % str(node.ids))
                    self.graph.remove_edge(*node.ids)
                node.close()

        # push a snapshot to the undo stack
        new_snapshot = self.graph.snapshot()
        self.undo_stack.push(commands.SceneNodesCommand(old_snapshot, new_snapshot, self.scene, msg='nodes deleted'))

    def getScenePreferences(self):
        """
        Get scene interface preferences from the QSettings.

        :returns: ui attributes.
        :rtype: dict
        """
        result = dict()
        for attr in self.ui.qsettings.prefs_keys():
            if hasattr(self.ui, attr):
                value = getattr(self.ui, attr)
                result[str(attr)] = value
        return result

    def graphAboutToBeSaved(self, graph):
        """
        Update the graph preferences attribute as the scene is about to be saved.

        :returns: interface preferences.
        :rtype: dict
        """
        result = self.getScenePreferences()
        self.graph.updateGraphPreferences(**result)

    def graphUpdated(self, *args):
        """
        Signal when the graph updates.
        """
        widgets_to_remove = []
        for id in self.scene.scenenodes:
            widget = self.scene.scenenodes.get(id)
            if self.scene.is_node(widget):
                if widget.id not in self.graph.network.nodes():
                    widgets_to_remove.append(widget)

            if self.scene.is_edge(widget):
                if widget.ids not in self.graph.network.edges():
                    widgets_to_remove.append(widget)

        for node in widgets_to_remove:            
            if self.scene.is_edge(node):
                src_conn = node.source_item
                dest_conn = node.dest_item
                print '# DEBUG: removing edge: ', node 
                node.close()

            if self.scene.is_node(node):
                print '# DEBUG: removing node: ', node
                node.close()

    def dagNodesUpdatedEvent(self, dagnodes):
        """
        Update dag nodes from an external UI.
        """
        if dagnodes:
            print '# DEBUG: dag nodes updated: ', [node.name for node in dagnodes]