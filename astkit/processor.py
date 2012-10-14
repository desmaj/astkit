""" processor.py

A collection of tools for the installation and use of generic AST processors.

More specifically, we need an import hook and a way to pipeline AST transformers
and visitors.
"""
import imp
import logging
import os
import sys

log = logging.getLogger(__name__)

from astkit import ast
from astkit.render import SourceCodeRenderer

class _ModuleLoader(object):
    
    def __init__(self, fullpath):
        self.fullpath = fullpath
    
    def _get_source(self, path):
        """ Get the source code from a file path """
        with open(path, 'r') as f:
            source = f.read()
        return source
    
    def _get_code(self, fullname):
        """ Get the instrumented code for a module
            
            Given a dotted module name, return a tuple that looks like
            (<is the module a package>, <module's code object instrumented>)
        """
        # packages are loaded from __init__.py files
        ispkg = self.fullpath.endswith('__init__.py')
        code_str = self._get_source(self.fullpath)
        code_tree = ast.parse(code_str)
        new_code_tree = _processor_manager.process(code_tree)
        log.debug(SourceCodeRenderer.render(new_code_tree))
        code = compile(new_code_tree, self.fullpath, 'exec')
        return (ispkg, code)
    
    def load_module(self, fullname):
        ispkg, code = self._get_code(fullname)
        mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
        mod.__file__ = self.fullpath
        mod.__loader__ = self
        if ispkg:
            mod.__path__ = [os.path.dirname(self.fullpath)]
        exec code in mod.__dict__
        return mod

class _NullLoader(object):
    
    def load_module(self, fullname):
        return sys,modules[fullname]

class _ImportHook(object):
    """ An implementation of an import hook per PEP 302
    """
    
    def find_module(self, fullname, path=[]):
        log.debug("find_module('%s', path=%r)",fullname, path)
        
        log.debug(sys.modules.get(fullname))
        if fullname in sys.modules:
            return _NullLoader()
        
        if not path:
            path = sys.path
        
        for directory in path:
            loader = self._loader_for_path(directory, fullname)
            if loader:
                return loader
    
    def _loader_for_path(self, directory, fullname):
        log.debug("[loader for path] directory: %s; fullname: %s",
                  directory, fullname)
        module_path = os.path.join(directory, fullname.split('.')[-1]) + ".py"
        if os.path.exists(module_path):
            log.debug("loading module from %s", module_path)
            loader = _ModuleLoader(module_path)
            return loader
        
        package_path = os.path.join(directory, fullname.split('.')[-1], '__init__.py')
        if os.path.exists(package_path):
            loader = ModuleLoader(package_path)
            return loader

class _ProcessorManager(object):
    
    def __init__(self):
        self._processors = []
        self.import_hook = _ImportHook()
    
    def add_processor(self, processor):
        if not self._processors:
            self._install_import_hook()
        self._processors.append(processor)
    
    def _install_import_hook(self):
        import sys
        sys.meta_path.append(self.import_hook)
    
    def _remove_import_hook(self):
        import sys
        sys.meta_path.remove(self.import_hook)
    
    def process(self, ast):
        for processor in self._processors:
            ast = processor.process(ast)
        return ast

_processor_manager = _ProcessorManager()
def install_processor(processor):
    _processor_manager.add_processor(processor)
