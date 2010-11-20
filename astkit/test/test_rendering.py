import ast

import astkit.render


render_stmt = astkit.render.SourceCodeRenderer.render
render_expr = astkit.render.SourceCodeRenderer()._render

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
    print 'five'
""",
                  """
if (length == 5):
    print 'five'
else:
    print '17'
""",
                  """
if (length == 5):
    print 'five'
else:
    if (length == 4):
        print 'four'
    else:
        print '17'
""",
                  ]

    def test_elif(self):
        initial = """
if (length == 5):
    print 'five'
elif (length == 4):
    print 'four'
else:
    print '17'
""".lstrip()
        expected = """
if (length == 5):
    print 'five'
else:
    if (length == 4):
        print 'four'
    else:
        print '17'
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

standard_arguments = ast.arguments(args=[ast.Name(id="a"),
                                         ast.Name(id="b")],
                                   vararg="stars",
                                   kwarg="kws",
                                   defaults=[ast.keyword(arg="c",
                                                value=ast.Str(s="c"))])

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
                           body=a_body),
              ("@decorated\n"
               "class SchoolInSummertime(Ecole, School):\n"
               "    result = 'No class'\n"
               "    return result\n")),

             (ast.Continue(),
              "continue\n"),

             (ast.Delete(targets=[ast.Name(id="tanks"), ast.Name(id="bombs")]),
              "del tanks, bombs\n"),

             (ast.excepthandler(type=ast.Name(id="Exception"),
                                name=ast.Name(id="exc"),
                                body=a_body),
              ("except Exception, exc:\n"
               "    result = 'No class'\n"
               "    return result\n")),

             (ast.Exec(body=ast.Name(id="the_body"),
                       globals=ast.Name(id="g_dict"),
                       locals=ast.Name(id="l_dict")),
              "exec the_body in g_dict, l_dict\n"),

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
              
              (ast.FunctionDef(decorator_list=[ast.Name(id="decorated")],
                               name="SchoolInSummertime",
                               args=standard_arguments,
                               body=a_body),
               ("@decorated\n"
                "def SchoolInSummertime(a, b, c='c', *stars, **kws):\n"
                "    result = 'No class'\n"
                "    return result\n")),
             
             
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

             (ast.Eq(),
              '=='),

             (ast.GeneratorExp(elt=ast.Name(id="frog"),
                               generators=standard_comprehensions),
              ("( frog\n"
               "  for egg in dozen\n"
               "  if (egg != 'rotten')\n"
               "  for yolk in egg.yolks\n"
               "  if (yolk == 'yellow') )")),
             
             
             ]
    
