#!/usr/bin/env python
import os
import re
import sys
import pkgutil
import inspect
import time
import simplejson as json

from SceneGraph.core import log
from SceneGraph.options import SCENEGRAPH_PATH, SCENEGRAPH_CORE, SCENEGRAPH_UI, SCENEGRAPH_PLUGIN_PATH, SCENEGRAPH_ICON_PATH, SCENEGRAPH_METADATA_PATH, PACKAGE



class PluginManager(object):
    """
    Class to manage loading and unloading of plugins.

    Paths will be scanned automatically. To override external plugin paths, 
    pass the paths you want to use with the 'paths' argument, else the 
    PluginManager will scan for directories on the PYTHONPATH.

    run with PluginManager.load_plugins()
    """
    def __init__(self, paths=[], **kwargs):

        # storage for plugin data
        self._plugin_data            = dict()    

        # plugin paths & module data
        self._core_plugin_path       = SCENEGRAPH_CORE
        self._core_widget_path       = SCENEGRAPH_UI
        self._builtin_plugin_path    = SCENEGRAPH_PLUGIN_PATH

        # external paths & module
        self._external_plugin_paths  = paths

        # setup external paths
        if not self._external_plugin_paths:
            self._external_plugin_paths = self.initializeExternalPaths()
        

        self.run()

    def run(self):
          """
          Create the plugin diction
          """
          self._plugin_data = load_plugins(self.plugin_paths)
 

    def initializeExternalPaths(self):
        """
        Builds a list of external plugins paths. 

        :returns: plugin scan paths.
        :rtype: tuple 
        """
        result = ()
        ext_pp = os.getenv('SCENEGRAPH_EXTERNAL_PLUGINS')
        if ext_pp:
            for path in ext_pp.split(':'):
                result = result + (path,)
                sys.path.insert(0, os.path.dirname(path))
        return list(result)
    
    @property
    def plugin_paths(self):
        """
        Returns a list of all plugin paths, starting with core & builtin.

        :returns: plugin scan paths.
        :rtype: tuple 
        """
        result = (self._core_plugin_path, self._core_widget_path, self._builtin_plugin_path,)
        if self._external_plugin_paths:
            for path in self._external_plugin_paths:
                result = result + (path,)
        return result

    def setLogLevel(self, level):
        """
         * debugging.
        """
        log.level = level

    #- Attributes ----
    def node_types(self, plugins=[], disabled=False):
        """
        Return a list of loaded node types.

        :param list plugins: plugins to filter.
        :param bool disabled: return disabled plugins.

        :returns: list of node types (strings).
        :rtype: list
        """
        return self.get_plugins(plugins=plugins, disabled=disabled) 

    @property
    def plugin_types(self):
        """
        Returns a list of plugin types (core, builtin, etc.).

        :returns: node categories.
        :rtype: list
        """
        plugin_types = []

        for node_type, node_attrs in self._plugin_data.iteritems():
            ptype = node_attrs.get('plugin_type', None)
            
            if ptype and ptype not in plugin_types:
                plugin_types.append(ptype)

        return sorted(plugin_types) 

    @property
    def node_categories(self):
        """
        Returns a list of node categories.

        :returns: node categories.
        :rtype: list
        """
        node_categories = []

        for node_type, node_attrs in self._plugin_data.iteritems():
            category = node_attrs.get('category', None)
            
            if category and category not in node_categories:
                node_categories.append(category)

        return sorted(node_categories)   

    @property
    def node_classes(self):
        """
        Returns a list of node classes.

        :returns: node classes.
        :rtype: list
        """
        node_classes = []
        for node_type, node_attrs in self._plugin_data.iteritems():
            node_class = node_attrs.get('class', None)
            
            if node_class and node_class not in node_classes:
                node_classes.append(node_class)
        return sorted(node_classes)   
    
    #- REMOVE ------
    
    @property
    def builtin_plugin_path(self):
        """
        Return the builtin plugin path.

        :returns: current builtin plugin path.
        :rtype: str
        """
        return self._builtin_plugin_path

    @builtin_plugin_path.setter
    def builtin_plugin_path(self, path):
        """
        Set the builtin plugin path.

        :param str path: directory path.

        :returns: current builtin plugin path.
        :rtype: str
        """
        if path != self._builtin_plugin_path:
            self._builtin_plugin_path = path
        return self.builtin_plugin_path

    @property
    def core_modules(self):
        """
        Returns the core plugin module names.

        :returns: list of core plugin module names.
        :rtype: list
        """
        builtin = []
        for node_type, pattrs in self._plugin_data.iteritems():
            if pattrs.get('plugin_type') == 'core':
                builtin.append(node_type)
        return sorted(list(set(builtin)))

    @property
    def builtin_modules(self):
        """
        Returns the builtin plugin module names.
        Does not include core modules.

        :returns: list of builtin plugin module names.
        :rtype: list
        """
        builtin = []
        for node_type, pattrs in self._plugin_data.iteritems():
            if pattrs.get('plugin_type') == 'builtin':
                builtin.append(node_type)
        return sorted(list(set(builtin)))

    @property
    def external_plugin_paths(self):
        """
        Returns a list of external plugin paths.

        :returns: list of external plugin paths.
        :rtype: list
        """
        return self._external_plugin_paths    

    @property
    def external_modules(self):
        """
        Returns a list of external plugin module names.

        :returns: list of external plugin module names.
        :rtype: list
        """
        builtin = []
        for node_type, pattrs in self._plugin_data.iteritems():
            if pattrs.get('plugin_type') == 'external':
                builtin.append(node_type)
        return sorted(list(set(builtin))) 

    @property
    def valid_plugins(self):
        """
        Returns a list of valid plugins. If a plugin does not have both a Dag
        Node type and widget type, it is not considered valid.
        
        :returns: list of valid plugins.
        rtype: list
        """
        result = []
        for pname in self._plugin_data:
            pattrs = self._plugin_data.get(pname)

            enabled = pattrs.get('enabled', False)
            if not enabled:
                continue

            dag = pattrs.get('dagnode', None)
            widget = pattrs.get('widget', None)

            if dag is None or widget is None:
                continue

            if pname not in result:
                result.append(pname)
        return result   
    
    #- KEEP ----
    
    def get_plugins(self, plugins=[], disabled=False):
        """
        Return filtered plugin data.

        :param list plugins: plugin names to filter.
        :param bool disabled: show disabled plugins.

        :returns: dictionary of plugin data.
        :rtype: dict
        """
        result = dict()
        for plugin in sorted(self._plugin_data.keys()):
            if not plugins or plugin in plugins:
                plugin_attrs = self._plugin_data.get(plugin)
                if plugin_attrs.get('enabled', True) or disabled:
                    result[plugin] = plugin_attrs
        return result

    def get_dagnode(self, node_type, **kwargs):
        """
        Return the appropriate dag node type.

        :param str node_type: dag node type to return.

        :returns: dag node subclass.
        :rtype: DagNode
        """
        if node_type not in self._plugin_data:
            log.error('plugin type "%s" is not loaded.' % node_type)
            return

        dag = self._plugin_data.get(node_type).get('dagnode')
        # assign the node metadata file
        result = dag(_metadata=self._plugin_data.get(node_type).get('metadata', None), **kwargs)
        return result

    def get_widget(self, dagnode, **kwargs):
        """
        Return the appropriate node type widget. Returns the default widget
        if one is not defined.

        :param DagNode dagnode: node type.

        :returns: node widget subclass.
        :rtype: NodeWidget
        """
        if dagnode.node_type not in self._plugin_data:
            log.error('plugin "%s" is not loaded.' % dagnode.node_type)
            return

        if 'widget' not in self._plugin_data.get(dagnode.node_type):
            log.error('plugin "%s" widget not loaded.' % dagnode.node_type)
            return

        widget = self._plugin_data.get(dagnode.node_type).get('widget')
        return widget(dagnode)

    def enable(self, plugin, enabled=True):
        """
        Enable/disable plugins.
        
        :param str plugin: plugin name to toggle.
        :param bool enabled: plugin enabled state.
        
        :returns: plugin was successfully enabled/disabled.
        :rtype: bool
        """
        if not plugin in self._plugin_data:
            log.error('plugin "%s" not recognized.' % plugin)
            return False

        for plug, plugin_attrs in self._plugin_data.iteritems():
            if plug == plugin:
                log.info('setting plugin "%s" enabled: %s' % (plugin, str(enabled)))
                self._plugin_data.get(plugin).update(enabled=enabled)
                return True
        return False

    def default_name(self, plugin):
        """
        Return the DagNode's default name.

        :param str plugin: plugin name to query.

        :returns: node default name.
        :rtype: str 
        """
        if plugin in self._plugin_data:
            cls = self._plugin_data.get(plugin).get('dagnode')
            if cls:
                if hasattr(cls, 'default_name'):
                    return cls.default_name
        return
    
    #- NEEDS UPDATE ---
    
    def metadata_file(self, filename):
        """
        Returns the metadata description associated the given plugin.

        :returns: plugin source file.
        :rtype: str  
        """
        sg_core_path = os.path.join(SCENEGRAPH_CORE, 'nodes.py')
        if filename == sg_core_path:
            metadata_filename = os.path.join(SCENEGRAPH_METADATA_PATH, 'dagnode.mtd')
        else:
            basename = os.path.splitext(os.path.basename(filename))[0]
            metadata_filename = os.path.join(SCENEGRAPH_PLUGIN_PATH, '%s.mtd' % basename)

        if not os.path.exists(metadata_filename):
            raise OSError('plugin description file "%s" does not exist.' % metadata_filename)
        return metadata_filename


#- UTILITIES ------

def load_class(classpath):
    """
    Dynamically loads a class.

    :params str classpath: full path of class to import.
    - ie: "SceneGraph.core.nodes.DagNode"

    :returns:  imported class object.
    :rtype: object
    """
    class_data = classpath.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]
    module = __import__(module_path, globals(), locals(), fromlist=[class_str])
    return getattr(module, class_str)


def parse_module_variable(module, key):
    """
    Parse a named variable from a given module.

    :param module module:  module object.
    :param str key: string variable to search for.
 
    :returns: parsed module variable value.
    :rtype: str
    """
    for cname, obj in inspect.getmembers(module):
        if cname==key:
            return obj
    return None


def load_plugins(paths, plugins=[]):
    """
    Dynamically load all plugins & widgets.

    :param verbose: verbose output
    :type verbose: bool

    :param asset_name: asset name to filter
    :type asset_name: str
    """
    imported = []
    plugin_data = dict()

    for loader, mod_name, is_pkg in pkgutil.walk_packages(paths):

        pkg = '%s.%s.%s' % (PACKAGE, os.path.split(loader.path)[-1], mod_name)

        m = loader.find_module(mod_name)
        module = m.load_module(mod_name)

        # source filename
        src_file = m.filename

        for cname, obj in inspect.getmembers(module, inspect.isclass):

            node_type = None
            node_class = None            
            category = None
            widget_type = None
            classpath = '%s.%s' % (pkg, cname)

            # widget
            if hasattr(obj, 'widget_type'):
                widget_type = obj.widget_type

                if widget_type not in plugin_data:
                    plugin_data[widget_type] = dict()

                globals()[cname] = load_class(classpath)
                plugin_data.get(widget_type).update({'widget':globals()[cname]})
                continue

            # plugins need to have two attributes: node_type & node_class
            # widgets will have an attribute "widget_type" that corresponds with
            # the dag "node_Type"
            if not hasattr(obj, 'node_type') or not hasattr(obj, 'node_class'):
                continue   


            # get node attributes
            node_type = getattr(obj, 'node_type')
            node_class = getattr(obj, 'node_class')
            node_category = getattr(obj, 'node_category')

            # plugin type (core, builtin, external)
            plugin_type = 'external'            
            if SCENEGRAPH_CORE in src_file:
                plugin_type = 'core'

            elif SCENEGRAPH_PLUGIN_PATH in src_file:
                plugin_type = 'builtin'

            # metadata file
            mtd_file = None

            # builtin metadata is in the plugin folder
            if plugin_type == 'core':
                mtd_file = os.path.join(SCENEGRAPH_METADATA_PATH, '%s.mtd' % node_type)

            if plugin_type in ['builtin', 'external']:
                mtd_file = '%s.mtd' % os.path.splitext(src_file)[0]

            # import the class into the globals dictionary
            globals()[cname]=load_class(classpath)
            if node_type not in plugin_data:
                    plugin_data[node_type] = dict()

            plugin_data.get(node_type).update({'dagnode':globals()[cname], 'metadata':None, 'source':src_file, 'enabled':True, 
                                    'plugin_type':plugin_type, 'class':node_class, 'category':node_category})


            # update metadata if the file exists.
            if os.path.exists(mtd_file):
                plugin_data.get(node_type).update(metadata=mtd_file)
            else:
                log.warning('cannot find metadata file "%s"' % mtd_file)

            if plugin_data.get(node_type).get('dagnode') is not None and plugin_data.get(node_type).get('widget') is not None:
                log.info('enabling plugin "%s"' % node_type)
                plugin_data.get(node_type).update(enabled=True)

    return plugin_data


