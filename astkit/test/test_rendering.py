import sys

from astkit.compat import ast
import astkit.render
from astkit.util import ASTClassTree


class TestRenderingCoverage(object):
    
    def test_all_nodes_are_renderable(self):
        class_tree = ASTClassTree.create()
        renderable_classes = class_tree.leaves()
        renderer = astkit.render.SourceCodeRenderer()
        
        def _test_renderability(node_class):
            assert hasattr(renderer, 'render_%s' % node_class.__name__), (
                node_class)
        for node_class in renderable_classes:
            yield _test_renderability, node_class


render_stmt = astkit.render.SourceCodeRenderer.render
render_expr = astkit.render.SourceCodeRenderer.render

class RoundtripTestCase(object):
    
    def roundtrip(self, initial, expected=None):
        if expected is None:
            expected = initial
        node_tree = ast.parse(initial)
        result = render_stmt(node_tree)
        assert expected == result, repr([expected, result])
    
    def test_roundtrip(self):
        for snippet in self.roundtrips:
            yield self.roundtrip, snippet.lstrip()

class TestRendering(RoundtripTestCase):
    
    roundtrips = ["""
if (length == 5):
    printf('five')
""",
                  """
if (length == 5):
    printf('five')
else:
    printf('17')
""",
                  """
if (length == 5):
    printf('five')
else:
    if (length == 4):
        printf('four')
    else:
        printf('17')
""",
                  """
def func(a, b, c='c', *stargs, **kwargs):
    pass
""",
                  ]

    def test_elif(self):
        initial = """
if (length == 5):
    printf('five')
elif (length == 4):
    printf('four')
else:
    printf('17')
""".lstrip()
        expected = """
if (length == 5):
    printf('five')
else:
    if (length == 4):
        printf('four')
    else:
        printf('17')
""".lstrip()
        actual = render_stmt(ast.parse(initial))
        assert expected == actual, \
               repr((expected, actual))

class NodeRenderingTestCase(object):
    nodes = []
    
    def test_node_rendering(self):
        for node, expected in self.nodes:
            yield self.render_and_verify, node, expected

    def render_and_verify(self, node, expected):
        actual = self.render(node)
        assert expected == actual, (expected, actual)

a_body = [ast.Assign(targets=[ast.Name(id="result")],
                     value=ast.Str(s="No class")),
          ast.Return(value=ast.Name(id="result"))]

a_handler = ast.excepthandler(type='ClassException',
                              name='zero_class',
                              body=[ast.Return(value=ast.Name(id='zero_class'))])

an_else = [ast.Assign(targets=[ast.Name(id="result")],
                     value=ast.Str(s="a little class")),
           ast.Return(value=ast.Name(id="result"))]

a_final = [ast.Assign(targets=[ast.Name(id="result")],
                      value=ast.Str(s="a lot of class")),
           ast.Return(value=ast.Name(id="result"))]

standard_arguments = ast.arguments(args=[ast.Name(id="a"),
                                         ast.Name(id="b"),
                                         ast.Name(id="c"),
                                         ast.Name(id="d"),
                                         ],
                                   vararg="stars",
                                   kwarg="kws",
                                   defaults=[ast.Str(s="c"),
                                             ast.Str(s="d"),
                                             ])

standard_comprehensions = \
    [ast.comprehension(target=ast.Name(id="egg"),
                       iter=ast.Name(id="dozen"),
                       ifs=[ast.Compare(left=ast.Name(id="egg"),
                                        ops=[ast.NotEq()],
                                        comparators=[ast.Str(s="rotten")])]
                       ),
     ast.comprehension(target=ast.Name(id="yolk"),
                       iter=ast.Attribute(value=ast.Name(id="egg"), attr="yolks"),
                       ifs=[ast.Compare(left=ast.Name(id="yolk"),
                                        ops=[ast.Eq()],
                                        comparators=[ast.Str(s="yellow")])]
                       ),
     ]


if sys.version_info[0] < 3:
    class TestPython2StatementRendering(NodeRenderingTestCase):
        render = render_stmt
        nodes = [
            (ast.Exec(body=ast.Name(id="the_body"),
                      globals=ast.Name(id="g_dict"),
                      locals=ast.Name(id="l_dict")),
             "exec the_body in g_dict, l_dict\n"),
            
            (ast.Exec(body=ast.Name(id="the_body"),
                      locals=ast.Name(id="l_dict")),
             "exec the_body in l_dict\n"),
            
            (ast.Print(dest=ast.Name(id='stdout'),
                       values=[ast.Str(s='frog'),
                               ast.Str('toad'),
                               ast.Name(id='friends')],
                       nl=False),
             "print >>stdout, 'frog', 'toad', friends,\n"),
            
             (ast.With(context_expr=ast.Call(func=ast.Name(id="NewSeason"),
                                             args=[], keywords=[]),
                       optional_vars=[ast.Name(id="season")],
                       body=a_body),
              ("with NewSeason() as season:\n"
                "    result = 'No class'\n"
                "    return result\n")),
             
            (ast.TryExcept(body=a_body,
                            handlers=[a_handler],
                            orelse=an_else),
              ("try:\n"
               "    result = 'No class'\n"
               "    return result\n"
               "except ClassException, zero_class:\n"
               "    return zero_class\n"
               "else:\n"
               "    result = 'a little class'\n"
               "    return result\n")),

             (ast.TryFinally(body=a_body,
                            finalbody=an_else),
              ("try:\n"
               "    result = 'No class'\n"
               "    return result\n"
               "finally:\n"
               "    result = 'a little class'\n"
               "    return result\n")),
            
             (ast.excepthandler(type=ast.Name(id="Exception"),
                                name=ast.Name(id="exc"),
                                body=a_body),
              ("except Exception, exc:\n"
               "    result = 'No class'\n"
               "    return result\n")),

            ]
else:
    class TestPython3StatementRendering(NodeRenderingTestCase):
        render = render_stmt
        nodes = [
             (ast.With(withitems=[ast.withitem(context_expr=ast.Call(func=ast.Name(id="NewSeason"),
                                                                     args=[], keywords=[]),
                                               optional_vars=[ast.Name(id="season")]),
                                  ast.withitem(context_expr=ast.Call(func=ast.Name(id="OldSeason"),
                                                                     args=[], keywords=[]),
                                               optional_vars=[ast.Name(id="oseason")]),
                                  ],
                       body=a_body),
              ("with NewSeason() as season, OldSeason() as oseason:\n"
                "    result = 'No class'\n"
                "    return result\n")),
             
             (ast.Nonlocal(names=[ast.Name(id="Rand"), ast.Name(id="Todd")]),
              "nonlocal Rand, Todd\n"),
             
            (ast.Try(body=a_body,
                     handlers=[a_handler],
                     orelse=an_else,
                     finalbody=a_final),
              ("try:\n"
               "    result = 'No class'\n"
               "    return result\n"
               "except ClassException as zero_class:\n"
               "    return zero_class\n"
               "else:\n"
               "    result = 'a little class'\n"
               "    return result\n"
               "finally:\n"
               "    result = 'a lot of class'\n"
               "    return result\n")),

             (ast.excepthandler(type=ast.Name(id="Exception"),
                                name=ast.Name(id="exc"),
                                body=a_body),
              ("except Exception as exc:\n"
               "    result = 'No class'\n"
               "    return result\n")),

            ]
    
if sys.version_info[:2] < (2, 6):
    class TestfunctionDefRendering(NodeRenderingTestCase):
        render = render_stmt
        
        nodes = [(ast.FunctionDef(decorators=[ast.Name(id="decorated")],
                                  name="SchoolInSummertime",
                                  args=standard_arguments,
                                  body=a_body),
                  ("@decorated\n"
                   "def SchoolInSummertime(a, b, c='c', d='d', *stars, **kws):\n"
                   "    result = 'No class'\n"
                   "    return result\n")),
                 ]
else:             
    class TestfunctionDefRendering(NodeRenderingTestCase):
        render = render_stmt
        
        nodes = [(ast.FunctionDef(decorator_list=[ast.Name(id="decorated")],
                                  name="SchoolInSummertime",
                                  args=standard_arguments,
                                  body=a_body),
                  ("@decorated\n"
                   "def SchoolInSummertime(a, b, c='c', d='d', *stars, **kws):\n"
                   "    result = 'No class'\n"
                   "    return result\n")),
                 ]

class TestStatementRendering(NodeRenderingTestCase):
    render = render_stmt
    nodes = [(ast.Assert(test=ast.BinOp(left=ast.Num(n=5),
                                        op=ast.NotEq(),
                                        right=ast.Num(n=7)),
                         msg=ast.Str(s="Let's hope this assert is true")),
              "assert (5 != 7), \"Let's hope this assert is true\"\n"),

             (ast.Assign(targets=[ast.Name(id="frog"),
                                     ast.Name(id="toad")],
                            value=ast.Str(s="Steve")),
              "frog = toad = 'Steve'\n"),

             (ast.AugAssign(target=ast.Name(id="frog"),
                             op=ast.Add(),
                             value=ast.Str(s="Steve")),
              "frog += 'Steve'\n"),

             (ast.Break(),
              "break\n"),

             (ast.ClassDef(decorator_list=[ast.Name(id="decorated")],
                           name="SchoolInSummertime",
                           bases=["Ecole", "School"],
                           body=[ast.Str(s=""" This is the docstring """)] + a_body),
              ("@decorated\n"
               "class SchoolInSummertime(Ecole, School):\n"
               "    result = 'No class'\n"
               "    return result\n")),

             (ast.Continue(),
              "continue\n"),

             (ast.Delete(targets=[ast.Name(id="tanks"), ast.Name(id="bombs")]),
              "del tanks, bombs\n"),

             (ast.Expr(value=ast.Call(func="a_funny_call",
                                      args=[],
                                      keywords=[])),
              "a_funny_call()\n"),

             (ast.Expression(body=ast.Call(func="a_funny_call",
                                           args=[],
                                           keywords=[])),
              "a_funny_call()\n"),

             (ast.For(target=ast.Name(id="i"),
                      iter=ast.Call(func=ast.Name(id="range"),
                                    args=[ast.Num(n=5)],
                                    keywords=[]),
                      body=a_body,
                      orelse=[]),
              ("for i in range(5):\n"
               "    result = 'No class'\n"
               "    return result\n")),
              
             (ast.For(target=ast.Name(id="i"),
                      iter=ast.Call(func=ast.Name(id="range"),
                                    args=[ast.Num(n=5)],
                                    keywords=[]),
                      body=[ast.Pass()],
                      orelse=a_body),
              ("for i in range(5):\n"
               "    pass\n"
               "else:\n"
               "    result = 'No class'\n"
               "    return result\n")),
              
             (ast.Global(names=[ast.Name(id="Rand"), ast.Name(id="Todd")]),
              "global Rand, Todd\n"),
             
             # I'm taking credit for testing If in the cases above.
             # What can I say, I'm lazy.

             (ast.Import(names=[ast.Name(id="John"), ast.Name(id="Paul")]),
              "import John, Paul\n"),

             (ast.ImportFrom(module=ast.Name(id="thebeatles"),
                             names=[ast.Name(id="George"), ast.Name(id="Ringo")],
                             level=None),
              "from thebeatles import George, Ringo\n"),

             (ast.ImportFrom(module=None,
                             names=[ast.Name(id="George"), ast.Name(id="Ringo")],
                             level=2),
              "from .. import George, Ringo\n"),
             
             (ast.Pass(), 'pass\n'),

             (ast.Raise(type='Exception', inst='exc', tback='tb'),
              'raise Exception, exc, tb\n'),

             (ast.Return(value=ast.Num(n=42)),
              'return 42\n'),

              (ast.While(test=ast.Compare(left=ast.Name(id="season"),
                                          ops=[ast.Eq()],
                                          comparators=[ast.Str(s="Summer")]),
                         body=a_body,
                         orelse=an_else),
               ("while (season == 'Summer'):\n"
                "    result = 'No class'\n"
                "    return result\n"
                "else:\n"
                "    result = 'a little class'\n"
                "    return result\n")),

             ]


if sys.version_info[0] < 3:
    class TestPython2ExpressionRendering(NodeRenderingTestCase):
        render = render_expr
        nodes = [
            (ast.Repr(value=ast.Name(id="frogs")),
             'repr(frogs)'),
            
            ]
else:
    class TestPython3ExpressionRendering(NodeRenderingTestCase):
        render = render_expr
        nodes = [
            (ast.Starred(value=ast.Name(id="frogs")),
             '*frogs'),
            
            (ast.YieldFrom(value=ast.Name(id="frogs")),
             'yield from frogs'),
            
            (ast.withitem(context_expr=ast.Call(func=ast.Name(id="NewSeason"),
                                                args=[], keywords=[]),
                          optional_vars=[ast.Name(id="season")]),
             "NewSeason() as season"),
            
            (ast.Bytes(s="some bytes"),
             "b'some bytes'"),
            
            ]

if sys.version_info[:2] >= (2, 7):
    class Test27ExpressionRendering(NodeRenderingTestCase):
        render = render_expr
        nodes = [
            (ast.DictComp(key=ast.Name(id="yolk"),
                          value=ast.Attribute(value=ast.Name(id="yolk"),
                                              attr="radius"),
                          generators=standard_comprehensions),
             ("{yolk: yolk.radius\n"
              "  for egg in dozen\n"
              "  if (egg != 'rotten')\n"
              "  for yolk in egg.yolks\n"
              "  if (yolk == 'yellow')")),
            
             (ast.SetComp(elt=ast.Name(id="frog"),
                          generators=standard_comprehensions),
              ("{ frog\n"
               "  for egg in dozen\n"
               "  if (egg != 'rotten')\n"
               "  for yolk in egg.yolks\n"
               "  if (yolk == 'yellow') }")),

            (ast.Set(elts=[ast.Num(n=1),
                           ast.Num(n=2),
                           ast.Num(n=3),
                           ]),
             "{1, 2, 3}"),
             
            ]
        

class TestExpressionRendering(NodeRenderingTestCase):
    render = render_expr
    nodes = [(ast.Add(),
              '+'),
             
             (ast.And(),
              'and'),

             (ast.BitAnd(),
              '&'),

             (ast.alias(name="steve", asname="todd"),
              'steve as todd'),

             (ast.Attribute(value=ast.Str("frog"), attr="length"),
              "'frog'.length"),

             (ast.BinOp(left=ast.Str(s="frog"), op=ast.Add(), right=ast.Str(s="io")),
              "('frog' + 'io')"),

             (ast.BitOr(),
              '|'),

             (ast.BitXor(),
              '^'),
             
             (ast.BoolOp(op=ast.And(), values=[ast.Name(id="a"),
                                               ast.Name(id="b"),
                                               ast.Name(id="c"),
                                               ]
                         ),
              "(a and b and c)"),
             
              (ast.Call(func=ast.Name(id="funcy"),
                        args=[ast.Name(id="a"), ast.Name(id="b")],
                        keywords=[ast.keyword(arg="c", value=ast.Str(s="c"))],
                        starargs=ast.Name(id="stars"),
                        kwargs=ast.Name(id="kws")),
               "funcy(a, b, c='c', *stars, **kws)"),

             (ast.Compare(left=ast.Name(id="frog"),
                          ops=[ast.Eq(), ast.NotEq()],
                          comparators=[ast.Name(id="toad"),
                                       ast.Str(s="friends")]),
              "(frog == toad != 'friends')"),

             (ast.Dict(keys=[ast.Str(s="frog"), ast.Name(id="toad")],
                       values=[ast.Name(id="friends"), ast.Str(s="enemies")]),
              "{'frog': friends, toad: 'enemies'}"),

             (ast.Div(),
              "/"),

             (ast.Ellipsis(),
              '...'),

             (ast.Eq(),
              '=='),

             (ast.ExtSlice(dims=[ast.Slice(),
                                 ast.Index(value=ast.List(elts=[ast.Num(n=2),
                                                                ast.Num(n=4)]))
                                 ]),
              ':, [2, 4]'),

             (ast.FloorDiv(),
              '//'),
             
             (ast.GeneratorExp(elt=ast.Name(id="frog"),
                               generators=standard_comprehensions),
              ("( frog\n"
               "  for egg in dozen\n"
               "  if (egg != 'rotten')\n"
               "  for yolk in egg.yolks\n"
               "  if (yolk == 'yellow') )")),
             
             (ast.Gt(), ">"),

             (ast.GtE(), ">="),

             (ast.IfExp(test=ast.Compare(left=ast.Name(id="lastname"),
                                         ops=[ast.Eq()],
                                         comparators=[ast.Str(s="McQueen")]),
                        body=ast.Str(s="Steve"),
                        orelse=ast.Str(s="Stew")),
              "( 'Steve' if (lastname == 'McQueen') else 'Stew' )"),

             (ast.In(), "in"),

             (ast.NotIn(), "not in"),

             (ast.Index(value=ast.BinOp(left=ast.Num(n=4),
                                        op=ast.Add(),
                                        right=ast.Num(n=5))),
              "(4 + 5)"),

             (ast.Is(), "is"),

             (ast.IsNot(), "is not"),

             (ast.keyword(arg="kwarg", value=ast.Str(s="I'm a kwarg!")),
              'kwarg="I\'m a kwarg!"'),

             (ast.Lambda(args=["x"], body=ast.BinOp(left=ast.Name(id="x"),
                                                    op=ast.Pow(),
                                                    right=ast.Num(n=2))),
              "lambda x: (x ** 2)"),

             (ast.List(elts=[ast.Name(id="a"), ast.Str(s="b"), ast.Num(n=4)]),
              "[a, 'b', 4]"),
             
             (ast.ListComp(elt=ast.Name(id="frog"),
                           generators=standard_comprehensions),
              ("[ frog\n"
               "  for egg in dozen\n"
               "  if (egg != 'rotten')\n"
               "  for yolk in egg.yolks\n"
               "  if (yolk == 'yellow') ]")),

             (ast.Lt(), '<'),

             (ast.LtE(), '<='),

             (ast.Mod(), '%'),

             (ast.Mult(), '*'),

             (ast.Name(id="froggie"), 'froggie'),

             (ast.Not(), 'not'),

             (ast.NotEq(), '!='),

             (ast.Num(n=17), '17'),
             
             (ast.Or(), 'or'),

             (ast.Pow(), '**'),
             
             (ast.Slice(lower=ast.Num(n=1),
                        upper=ast.Num(n=4),
                        step=ast.Num(n=6)),
              '1:4:6'),

             (ast.Slice(lower=None,
                        upper=None,
                        step=None),
              ':'),

             (ast.Str(s='froggie'), "'froggie'"),

             (ast.Sub(), '-'),

             (ast.Subscript(value='eggs', slice=ast.Num(n=12)),
              'eggs[12]'),
             
             (ast.Tuple(elts=[ast.Name(id="a"), ast.Str(s="b"), ast.Num(n=4)]),
              "(a, 'b', 4, )"),

             (ast.UnaryOp(op=ast.USub(), operand=ast.Num(n=42)),
              "- 42"),

             (ast.USub(), '-'),

             
             (ast.Yield(value=ast.Name(id="to_oncoming_traffic")),
              "yield to_oncoming_traffic"),

             (ast.Yield(value=None),
              "yield"),
             
             ]
    
class TestStatementRenderingWithNonDefaultIndentation(NodeRenderingTestCase):
    
    def render_and_verify(self, node, expected):
        actual = self.render(node, 2)
        assert expected == actual, (expected, actual)
        
    render = render_stmt
    nodes = [(ast.ClassDef(decorator_list=[ast.Name(id="decorated")],
                           name="SchoolInSummertime",
                           bases=["Ecole", "School"],
                           body=[ast.Str(s=""" This is the docstring """)] + a_body),
              ("@decorated\n"
               "class SchoolInSummertime(Ecole, School):\n"
               "  result = 'No class'\n"
               "  return result\n")),
             ]
