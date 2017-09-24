from typing import Dict, List, Union
import numpy as np
import cv2


def make_cam(cam_id ) :  # type: (Union[int, str]) -> Union[bool, cv2.VideoCapture]
    cam: cv2.VideoCapture = cv2.VideoCapture(cam_id)

    if cam is not None and cam.isOpened():
        return cam
    else:
        return False

def make_cams(*argv ) :  # type: (Union[int, str]) -> Dict[Union[int, str], cv2.VideoCapture]
    cam_list : Dict[cv2.VideoCapture] = {}

    if len(argv) == 0:
        i = 0
        while len(cam_list) == 0 or cam_list[i-1].isOpened():
            cam_list[i] = cv2.VideoCapture(i)
            i += 1
    else:
        for i in argv:
            cam_list[i] = cv2.VideoCapture(i)

    return cam_list

def capture_cam(camera ) :  # type: (cv2.VideoCapture) -> Union[np.ndarray, bool]
    (ret, frame) = camera.read()
    if ret is False or not isinstance(frame, np.ndarray):
        return False
    else:
        return frame