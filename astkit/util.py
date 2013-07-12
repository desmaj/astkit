import inspect

from astkit import ast

class ASTClassTree(dict):
    
    @classmethod
    def create(cls):
        tree = cls(object)
        for name in dir(ast):
            item = getattr(ast, name)
            
            if (inspect.isclass(item) and issubclass(item, ast.AST)):
                tree.insert(item)
        return tree
    
    def __init__(self, root):
        self._root = root
    
    def contains(self, key):
        if key == self._root:
            return True
        
        elif key in self:
            return True
        
        else:
            for node in self:
                if self[node].contains(key):
                    return True
    
    def find(self, key):
        if key == self._root:
            return self
        
        elif key in self:
            return self[key]
        
        else:
            for node in self:
                child = self[node]
                if child.contains(key):
                    return child.find(key)
    
    def insert(self, item):
        lineage = inspect.getmro(item)
        parent = lineage[1]
        subtree = self.__class__(item)
        
        if self.contains(item):
            return self.find(item)
        
        elif self.contains(parent):
            self.find(parent)[item] = subtree
            
        else:
            self.insert(parent)[item] = subtree
        
        return subtree
    
    def leaves(self):
        if not self:
            return [self._root]
        
        else:
            _leaves = []
            for key in self:
                _leaves += self[key].leaves()
            return _leaves
    
    def __str__(self):
        lines = [str(self._root) + " " + str(len(self))]
        for key in sorted(self, key=lambda item: item.__name__):
            lines += ["    " + line
                      for line in str(self[key]).splitlines()]
        return "\n".join(lines)

if __name__ == '__main__':
    # The snippet below will do something similar using a builtin function,
    # which sounds nice. I like what I've got here, though, so I'll stick
    # with it for now.
    # 
    # import pprint
    # 
    # classes = [item
    #            for item in [getattr(ast, name) for name in dir(ast)]
    #            if inspect.isclass(item) and issubclass(item, ast.AST)]
    # pprint.pprint(inspect.getclasstree(classes, unique=True))
    # 
    
    import sys
    tree = ASTClassTree.create()
    sys.stdout.write(str(tree) + "\n")
    for leaf in sorted(tree.leaves(), key=lambda item: item.__name__):
        sys.stdout.write(str(leaf) + "\n")
    
