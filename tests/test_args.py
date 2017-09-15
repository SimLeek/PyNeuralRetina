import unittest

import NeuralRetina.cam_node as cam_node

class TestCamNode(unittest.TestCase):
    def test_parse_args(self):
        cam_node.parse_args(['-c', '--all'])
