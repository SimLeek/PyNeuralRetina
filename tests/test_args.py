import unittest

import argparse

from NeuralRetina.camera.parse_args import parse_args


class TestCamNode(unittest.TestCase):
    #Don't test standard functionality. Only added.
    def test_conflicting_args(self):
        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['-u', '--all', '--max'])

        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['-u', '--max', '--nonstandard'])

        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['-u', '--nonstandard', '--all'])

        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['-u', '--all', '--nonstandard_resolutions'])

        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['-u', '--all', '--max_fps'])

        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['-u', '--nonstandard', '--max_resolution'])

        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['-u', '--nonstandard_fps', '--max_fps'])

    def test_redundant_args(self):
        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['-u', '--max', '--max_fps'])

    def test_unneeded_args(self): # test --all without -c
        with self.assertRaises(SystemExit):
            with self.assertRaises(argparse.ArgumentError): parse_args(['--all'])
