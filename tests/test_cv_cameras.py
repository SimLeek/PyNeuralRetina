import unittest

import numpy as np
import cv2

from NeuralRetina.camera.cv_cameras import *

class TestCVCameras(unittest.TestCase):
    # todo: add video filename tests

    def setUp(self):
        self.actual_cam = make_cam(0)

    def test_make_all_cams(self):
        cams = make_cams()

        self.assertIsInstance(cams, dict)
        self.assertTrue(len(cams)>0)  # fails if you don't have any cameras

        for _, cam in cams.items():
            cam.release()

    def test_make_specific_cams(self):
        cam_0 = make_cams(0)
        cam_1 = make_cams(1)

        self.assertIsInstance(cam_0, dict)
        self.assertEqual(cam_0[0].__class__.__name__, "VideoCapture")

        self.assertIsInstance(cam_1, dict)
        self.assertEqual(cam_1[1].__class__.__name__, "VideoCapture")

        cam_0[0].release()
        cam_1[1].release()

    def test_frame(self):
        self.assertIsInstance(capture_cam(self.actual_cam), np.ndarray)
        self.assertEqual(capture_cam(self.actual_cam).ndim, 3)

    def tearDown(self):
        self.actual_cam.release()

        #self.assertTrue(len(cams) > 0)

