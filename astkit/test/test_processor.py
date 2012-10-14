import os

class DummyProcessor(object):
    pass

class TestProcessorManager(object):
    
    def _make_one(self):
        from astkit.processor import _ProcessorManager
        return _ProcessorManager()
    
    def test_new(self):
        from astkit.processor import _ProcessorManager
        assert _ProcessorManager()
    
    def test_add_processor(self):
        man = self._make_one()
        proc = DummyProcessor()
        man.add_processor(proc)
        assert proc in man._processors
    
    def test_add_and_remove_import_hook(self):
        import sys
        man = self._make_one()
        assert man.import_hook not in sys.meta_path
        man._install_import_hook()
        assert man.import_hook in sys.meta_path
        man._remove_import_hook()
        assert man.import_hook not in sys.meta_path
        
class TestImportHook(object):
    
    def teardown(self):
        import sys
        if 'astkit.test.modules.one' in sys.modules:
            del sys.modules['astkit.test.modules.one']
        
    def _make_one(self):
        from astkit.processor import _ImportHook
        return _ImportHook()
    
    def test_null_loader_for_loaded_module(self):
        from astkit.processor import _NullLoader
        hook = self._make_one()
        loader = hook.find_module('astkit')
        assert isinstance(loader, _NullLoader), loader
        
    def test_find_module_for_submodule_returns_loader(self):
        import astkit
        from astkit.processor import _ModuleLoader
        hook = self._make_one()
        path = os.path.join(astkit.__path__[0], 'test', 'modules')
        loader = hook.find_module('astkit.test.modules.one', path=[path])
        assert isinstance(loader, _ModuleLoader), loader
    
    def test_find_module_for_module_returns_loader(self):
        from astkit.processor import _ModuleLoader
        hook = self._make_one()
        loader = hook.find_module('codeop')
        assert isinstance(loader, _ModuleLoader), loader

