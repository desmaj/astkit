Using ASTKit
^^^^^^^^^^^^

Rendering
---------

ASTKit provides a source code renderer astkit.render.SourceCodeRenderer that will transform an ast.Node tree into syntactically correct Python source code. This is easy to do. Have a look at the following example::

 >>> import ast
 >>> call = ast.Call(func=ast.Attribute(value=ast.Name(id='somemodule'),
 ...                                    attr='somefunc'),
 ...                 args=[ast.Num(n=8),
 ...                       ast.Num(n=15),
 ...                       ],
 ...                 keywords=[])
 >>> from astkit.render import SourceCodeRenderer
 >>> SourceCodeRenderer.render(call)
 'somemodule.somefunc(8, 15)'
 
In the example, you can see that we create an ast.Call node; this node represents a function call. Specifically, it is a call to the function 'somefunc' from the module 'somemodule' with two arguments: 8 and 15. You can see that when we call SourceCodeRenderer.render on it we get 'somemodule.somefunc(8, 15)', which is just what we would expect.

The ast.Call node in the above example is an expression, but the SourceCodeRenderer works just as well with statements.
