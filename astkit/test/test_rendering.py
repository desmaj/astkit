import ast

import astkit.render

class RenderingTestCase(object):

    render = astkit.render.SourceCodeRenderer.render

    def roundtrip(self, initial, expected=None):
        if expected is None:
            expected = initial
        node_tree = ast.parse(initial)
        result = self.render(node_tree)
        assert expected == result, repr([expected, result])

    def test_roundtrip(self):
        for snippet in self.roundtrips:
            yield self.roundtrip, snippet.lstrip()
    
class TestRenderIf(RenderingTestCase):
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
        actual = self.render(ast.parse(initial))
        assert expected == actual, \
               repr((expected, actual))
