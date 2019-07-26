import unittest
import test
from pyparsing import OneOrMore, nestedExpr, Dict


class ListToDict(unittest.TestCase):

    def testSimple(self):
        input = "(last_trace_width 0.15)"
        data = OneOrMore(nestedExpr()).parseString(input)
        data = data.asList()
        self.assertEqual(test.list_to_dict(data[0]), {'last_trace_width': "0.15"})

    def testOneLevel(self):
        input = "(other_layers_text_dims (size 1 1) (thickness 0.15) keep_upright)"
        data = OneOrMore(nestedExpr()).parseString(input)
        data = data.asList()
        self.assertEqual(test.list_to_dict(data[0]), {'other_layers_text_dims':
                                                          [{'size': ['1', '1']}, {'thickness': '0.15'}, 'keep_upright']})
