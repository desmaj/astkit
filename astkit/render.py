import ast
import copy
import inspect
import logging
import sys

log = logging.getLogger(__name__)

class LocationAdjustingVisitor(ast.NodeTransformer):
    
    def __init__(self, lineno=0, col_offset=0):
        super(LocationAdjustingVisitor, self).__init__()
        self.lineno = lineno
        self.col_offset = 0
    
    def visit(node):
        if hasattr(node, 'lineno'):
            node.lineno += self.lineno
        if hasattr(node, 'col_offset'):
            node.col_offset += self.col_offset
        self.generic_visitor(node)
        return node

def adjust_node_location(node, lineno=0, col_offset=0):
    adjuster = LocationAdjustingVisitor(lineno, col_offset)
    return adjuster.visit(node)

class AccumulatingVisitor(object):
    
    acc = None
    
    def do(self, base_node):
        self.generic_visit(base_node)
        return self.acc
    
    def accumulate(self, node):
        raise NotImplementedError()
    
    def visit(self, node):
        """Visit a node."""
        if isinstance(node, InstrumentedNode):
            method = 'visit_' + node.node.__class__.__name__
        else:
            method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor(node)

    def generic_visit(self, node):
        self.accumulate(node)
        for field, value in ast.iter_fields(node):
            value = getattr(node, field, None)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)
    
INDENTATION = " " * 4

class BlankLine():
    pass

class SourceCodeRenderer(ast.NodeVisitor):
    
    @classmethod
    def render(cls, node):        
        renderer = cls()
        renderer.visit(node)
        return ''.join(renderer._sourcelines)
    
    def _render(self, node):
        render_method = getattr(self, 'render_%s' % node.__class__.__name__)
        return render_method(node)
        
    def __init__(self):
        self._sourcelines = []
        self._blocklevel = 0
    
    def emit(self, source):
        for sourceline in source.splitlines(False):
            self._sourcelines.append("%s%s\n" % (self._indent,
                                                 sourceline.lstrip()))
    
    def start_block(self):
        self._blocklevel += 1
    
    def end_block(self):
        self._blocklevel -= 1

    @property
    def _indent(self):
        return INDENTATION * self._blocklevel
    
    def visit(self, node):
        self._render(node)
    
    def _render_statements(self, statements):
        for stmt in statements:
            self._render(stmt)
    
    def _maybe_render_docstring(self, node):
        """ Render the node's docstring, if present """
        docstring = ast.get_docstring(node)
        if docstring:
            node.body.pop(0)
            self.emit('""" ' + docstring + '\n"""')
    
    def _maybe_rearrange_imports(self, node):
        future_imports = []
        for index, stmt in enumerate(node.body):
            if isinstance(stmt, ast.ImportFrom) and \
                    stmt.module == '__future__':
                future_imports.append(index)
        for index in reversed(future_imports):
            node.body.insert(0, node.body.pop(index))
        
    def default_renderer(self, node):
        return repr(node)
    
    def render_Add(self, node):
        return '+'
    
    def render_And(self, node):
        return "and"
    
    def render_BitAnd(self, node):
        return "&"
    
    def render_arguments(self, node):
        sep = ", "
        arg_parts = []
        args_with_defaults = []
        for i, arg in enumerate(reversed(node.args)):
            if i < len(node.defaults):
                args_with_defaults.append(\
                    (arg, node.defaults[len(node.defaults)-i-1]))
            else:
                args_with_defaults.append((arg, None))
        args = []
        for arg, default in reversed(args_with_defaults):
            arg_part = self._render(arg)
            if default:
                arg_part += "=" + self._render(default)
            args.append(arg_part)
        if args:
            arg_parts.append(self._render(args))
        if node.vararg:
            arg_parts.append("*%s" % node.vararg)
        if node.kwarg:
            arg_parts.append("**%s" % node.kwarg)
        return sep.join(arg_parts)
    
    def render_alias(self, node):
        alias = node.name
        if hasattr(node, 'asname') and node.asname:
            alias += " as " + node.asname
        return alias
    
    def render_Assert(self, node):
        source = "assert " + self._render(node.test)
        if node.msg:
            source += ", " + self._render(node.msg)
        self.emit(source)
    
    def render_Assign(self, node):
        source = " = ".join([self._render(target)
                             for target in node.targets])
        source += " = " + self._render(node.value)
        self.emit(source)
    
    def render_Attribute(self, node):
        return self._render(node.value) + '.' + node.attr
    
    def render_AugAssign(self, node):
        source = "%s %s= %s" % (self._render(node.target),
                                self._render(node.op),
                                self._render(node.value))
        self.emit(source)
    
    def render_BinOp(self, node):
        return "(%s %s %s)" % (self._render(node.left),
                               self._render(node.op),
                               self._render(node.right))
    
    def render_BitOr(self, node):
        return "|"
    
    def render_BlankLine(self, node):
        self.emit("\n")
    
    def render_Break(self, node):
        self.emit("break")

    def render_BoolOp(self, node):
        op = self._render(node.op)
        return "(" + (" " + op + " ").join([self._render(value)
                                            for value in node.values]) + ")"

    def render_Call(self, node):
        name = self._render(node.func)
        acc = "%s(" % (name)
        if node.args:
            acc += self._render(node.args)
        if node.keywords:
            if acc[-1] != "(":
                acc += ", "
            acc += self._render(node.keywords)
        if hasattr(node, 'starargs') and node.starargs:
            if acc[-1] != "(":
                acc += ", "
            acc += "*" + self._render(node.starargs)
        if hasattr(node, 'kwargs') and node.kwargs:
            if acc[-1] != "(":
                acc += ", "
            acc += "**" + self._render(node.kwargs)
        return acc + ")"
    
    def render_ClassDef(self, node):
        source = "\n".join([self._render(dec)
                         for dec in node.decorator_list])
        source += "class " + self._render(node.name)
        source += "(%s):\n" % ", ".join([self._render(base)
                                      for base in node.bases])
        self.emit(source)
        self.start_block()
        self._maybe_render_docstring(node)
        self._render_statements(node.body)
        self.end_block()
    
    def render_Compare(self, node):
        ops_and_comparators = zip(node.ops, node.comparators)
        rendered_ops_and_comparators = \
            " ".join(["%s %s" % (self._render(op), self._render(comparator))
                      for op, comparator in ops_and_comparators])
        
        return "(%s %s)" % (self._render(node.left),
                            rendered_ops_and_comparators)
    
    def render_comprehension(self, node):
        source = "for %s in %s" % (self._render(node.target),
                                self._render(node.iter))
        for if_ in node.ifs:
            source += "\n" + "if " + self._render(if_)
        return source
    
    def render_Continue(self, node):
        self.emit("continue")

    def render_Dict(self, node):
        acc = "{"
        acc +=  ", ".join(["%s: %s" % (self._render(key),
                                         self._render(value))
                           for key, value in zip(node.keys, node.values)])
        return acc + "}"
    
    def render_Div(self, node):
        return "/"
    
    def render_Delete(self, node):
        return self.emit("del " + self._render(node.targets))
    
    def render_Eq(self, node):
        return "=="
    
    def render_ExceptHandler(self, node):
        parts = [node.type, node.name]
        source = "except"
        if parts:
            source += " "
            source += ", ".join([self._render(part) for part in parts if part])
        source += ":\n"
        self.emit(source)
        self.start_block()
        self._render_statements(node.body)
        self.end_block()
    
    def render_Exec(self, node):
        source = 'exec %s' % self._render(node.body)
        if node.globals or node.locals:
            source + " in "
            if node.globals:
                source += self._render(node.globals)
                if node.locals:
                    source += ", " + self._render(node.locals)
            else:
                if node.locals:
                    source += self._render(node.locals)
        self.emit(source)
    
    def render_Expr(self, node):
        self.emit(self._render(node.value))
    
    def render_Expression(self, node):
        self.emit(self._render(node.body))
    
    def render_For(self, node):
        source = ("for %s in %s:\n" % (self._render(node.target),
                                       self._render(node.iter)))
        self.start_block()
        self._render_statements(node.body)
        self.end_block()
        if node.orelse:
            self.emit("else:\n")
            self.start_block()
            self._render_statements(node.orelse)
            self.end_block()
    
    def render_FunctionDef(self, node):
        source = "def %s(" % node.name
        source += self._render(node.args)
        if source.endswith(", "):
            source = source[:-3]
        source += "):\n"
        self.emit(source)
        self.start_block()
        self._maybe_render_docstring(node)
        self._render_statements(node.body)
        self.end_block()
    
    def render_GeneratorComp(self, node):
        source = "( " + self._render(node.elt) + "\n"
        source += "\n".join(self._render(generator)
                            for generator in node.generator)
        return source + " )"
        
    def render_Global(self, node):
        self.emit("global %s\n" % self._render(node.names))
    
    def render_Gt(self, node):
        return ">"
    
    def render_GtE(self, node):
        return ">="
    
    def render_If(self, node):
        source = "if %s:\n" % self._render(node.test)
        self.emit(source)
        self.start_block()
        self._render_statements(node.body)
        self.end_block()
        if node.orelse:
            self.emit("else:\n")
            self.start_block()
            self._render_statements(node.orelse)
            self.end_block()
        
    def render_IfExp(self, node):
        source = "(%s if %s" % (self._render(node.body),
                            self._render(node.test))
        if node.orelse:
            source += " " + self._render(node.orelse)
        return source + ")"
    
    def render_Import(self, node):
        self.emit("import %s\n" % self._render(node.names))
    
    def render_ImportFrom(self, node):
        import_tmpl = "from %s import %s"
        import_stmt = import_tmpl % (node.module,
                                     ", ".join([self._render(name)
                                                for name
                                                in node.names]))
        self.emit(import_stmt)
    
    def render_In(self, node):
        return "in"
    
    def render_NotIn(self, node):
        return "not in"
    
    def render_Index(self, node):
        return self._render(node.value)
    
    def render_Interactive(self, node):
        self.emit(node.body())
    
    def render_Is(self, node):
        return "is"
    
    def render_IsNot(self, node):
        return "is not"
    
    def render_keyword(self, node):
        return "%s=%s" % (node.arg, self._render(node.value))
    
    def render_Lambda(self, node):
        source = "lambda"
        if node.args:
            source += " " + self._render(node.args)
        return source + ": %s" % self._render(node.body)
    
    def render_list(self, elts, separator=", "):
        return separator.join([self._render(elt) for elt in elts])
    
    def render_List(self, node):
        return "[%s]" % ", ".join([self._render(elt) for elt in node.elts])
    
    def render_ListComp(self, node):
        source = "[ " + self._render(node.elt) + "\n"
        source += "\n".join([self._render(generator)
                             for generator in node.generators])
        return source + " ]"
    
    def render_Lt(self, node):
        return "<"
    
    def render_LtE(self, node):
        return "<="
    
    def render_Mod(self, node):
        return '%'
    
    def render_Module(self, node):
        self._maybe_render_docstring(node)
        self._maybe_rearrange_imports(node)
        self._render_statements(node.body)
    
    def render_Mult(self, node):
        return "*"
    
    def render_Name(self, node):
        return node.id
    
    def render_Not(self, node):
        return "not"
    
    def render_NotEq(self, node):
        return "!="
    
    def render_Num(self, node):
        return str(node.n)
    
    def render_Or(self, node):
        return "or"
    
    def render_Pass(self, node):
        self.emit("pass\n")
    
    def render_Pow(self, node):
        return "**"
    
    def render_Print(self, node):
        source = "print "
        if node.dest:
            source += ">>" + self._render(node.dest) + ", "
        source += ', '.join(self._render(value) for value in node.values)
        if node.nl and (source[-1] != '\n'):
            source += '\n'
        self.emit(source)
    
    def render_Raise(self, node):
        source = "raise"
        args = []
        for attr in ['type', 'inst', 'tback']:
            arg = getattr(node, attr)
            if arg:
                args.append(arg)
        if args:
            source += " " + ",".join([self._render(arg) for arg in args])
        self.emit(source)
    
    def render_Repr(self, node):
        return "repr(%s)" % self._render(node.value)
    
    def render_Return(self, node):
        source = "return"
        if node.value:
            source += " " + self._render(node.value)
        source += "\n"
        self.emit(source)
    
    def render_Slice(self, node):
        parts = [node.lower, node.upper, node.step]
        if parts:
            slice_ = ":".join([self._render(part) for part in parts
                               if part])
            return "slice(" + slice_ + ")"
        else:
            return ":"
    
    def render_Str(self, node):
        return repr(node.s)
    
    def render_str(self, node):
        return node
    
    def render_Sub(self, node):
        return "-"
    
    def render_Subscript(self, node):
        return "%s[%s]" % (self._render(node.value), self._render(node.slice))
    
    def render_Suite(self, node):
        self._render(node.body)
    
    def render_TryExcept(self, node):
        self.emit("try:\n")
        self.start_block()
        self._render_statements(node.body)
        self.end_block()
        for handler in node.handlers:
            self._render(handler)
        if node.orelse:
            self.emit("else:\n")
            self.start_block()
            self._render_statements(node.orelse)
            self.end_block()
    
    def render_TryFinally(self, node):
        self.emit("try:\n")
        self.start_block()
        self._render_statements(node.body)
        self.end_block()
        self.emit("finally:\n")
        self.start_block()
        self._render_statements(node.finalbody)
        self.end_block()
    
    def render_Tuple(self, node):
        return "(%s)" % \
            "".join([(self._render(elt) + ", ") for elt in node.elts])
    
    def render_UnaryOp(self, node):
        return self._render(node.op) + " " + self._render(node.operand)
    
    def render_USub(self, node):
        return "-"
    
    def render_While(self, node):
        self.emit("while %s:\n" % (self._render(node.test)))
        self.start_block()
        self._render_statements(node.body)
        self.end_block()
        if node.orelse:
            self.emit("else:\n")
            self.start_block()
            self._render_statements(node.orelse)
            self.end_block()
    
    def render_With(self, node):
        source = "with %s:\n" % (self._render(node.context_expr))
        if node.optional_vars:
            source += self._render(optional_vars)
        source += ":\n"
        self.emit(source)
        self.start_block()
        self._render_statements(node.body)
        self.end_block()
    
    def render_Yield(self, node):
        return "yield %s" % self._render(node.value)
