import argparse
import cv2

# todo: move cam_node and get_webcams into own directory to refactor. Cam node under source, get_webcams further in because core functionality.
# todo: add unit tests, with arg setting, to test all functions (https://stackoverflow.com/a/18161115)
# todo: store cam info in json file.
# todo: draw trees to show correct caling and then check that and return errors before running code

# todo: make all these options through redis (just send a string to cam.parseargs, seperate by spaces, and use argparse)
parser = argparse.ArgumentParser(description="ready and broadcast all webcams through redis.")

parser.add_argument('-p', '--publish', dest='publish', action='store_true',
                    help="[DEFAULT BEHAVIOR] Publish camera frames through publisher subscriber.")

parser.add_argument('--ros', dest='ros', action='store_true',
                    help="Publish and subscribe through ROS.")

parser.add_argument('--redis', dest='ros', action='store_true',
                    help="Publish and subscribe through redis.")

parser.add_argument('--publish_all', dest='ros', action='store_true',
                    help="Publish all cameras, instead of waiting for requests.")



parser.add_argument('-c', '--check',  type=int, nargs='*', dest='check', default=argparse.SUPPRESS, action='store',
                    help="Check camera resolutions and send to file. Camera numbers may be specified.")

parser.add_argument('--nonstandard_resolutions', dest='nonstandard_resolutions', action='store_true',
                    help="Check for resolutions typically only supported by special devices.")
parser.add_argument('--nonstandard_fps', dest='nonstandard_fps', action='store_true',
                    help="Check for fps rates typically only supported by special devices.")
parser.add_argument('--nonstandard', dest='nonstandard', action='store_true',
                    help="Check for resolutions and fps rates typically only supported by special devices.")

parser.add_argument('--all_resolutions', dest='all_resolutions', action='store_true',
                    help="Check every single possible resolution. e.g., 640x480, 640x481, and so on. " 
                         "It could take a while.")
parser.add_argument('--all_fps', dest='all_fps', action='store_true',
                    help="Check for fps rates typically only supported by special devices.")
parser.add_argument('--all', dest='all', action='store_true',
                    help="Check for resolutions and fps rates typically only supported by special devices.")

parser.add_argument('--max_resolution', dest='max_resolution', action='store_true',
                    help="Only check max resolution. " )
parser.add_argument('--max_fps', dest='max_fps', action='store_true',
                    help="Only check max fps.")
parser.add_argument('--max', dest='max', action='store_true',
                    help="Only check max resolution and fps.")

args = parser.parse_args()

for arg in vars(args):
    print (arg, getattr(args, arg))

#taken from: https://en.wikipedia.org/wiki/List_of_broadcast_video_formats
standard_fps_list = [24, 30, 50, 60, 120, 240]
nonstandard_fps_list = [25, 48, 72, 100, 300]

#taken from:
standard_resolution_list = [(352, 240), (352, 288), (352, 480), (352, 576), (480, 480), (480, 576),
                            (640, 480), (720, 480), (720, 576), (1280, 720), (1366, 768),
                            (1920, 1080), (1920, 1200), (3840, 2160), (7680, 4320)]

nonstandard_resolution_list = [(16, 16), (42, 11), (32, 32), (40, 30), (42, 32), (48, 32), (60, 40), (64, 64), (72, 64),
                               (128, 36), (75, 64), (84, 48), (150, 40), (96, 64), (96, 64), (128, 48), (96, 65),
                               (96, 96), (102, 64), (240, 64), (160, 102), (128, 128), (160, 120), (160, 144),
                               (144, 168), (160, 152), (160, 160), (140, 192), (160, 200), (224, 144), (208, 176),
                               (240, 160), (220, 176), (160, 256), (208, 208), (256, 192), (256, 212), (280, 192),
                               (432, 128), (240, 240), (320, 192), (320, 200), (256, 256), (320, 208), (320, 224),
                               (320, 240), (320, 256), (272, 340), (400, 240), (320, 320), (432, 240), (560, 192),
                               (400, 270), (384, 288), (480, 234), (480, 250), (400, 300), (376, 240), (312, 390),
                               (640, 200), (480, 272), (512, 212), (512, 256), (416, 352), (640, 240), (480, 320),
                               (640, 256), (512, 342), (800, 240), (512, 384), (640, 320), (640, 350), (640, 360),
                               (480, 500), (720, 348), (720, 350), (640, 400), (720, 364), (800, 352), (600, 480),
                               (640, 512), (768, 480), (800, 480), (848, 480), (854, 480), (800, 600),
                               (960, 540), (832, 624), (960, 544), (1024, 576), (1024, 600), (960, 640), (1024, 640),
                               (960, 720), (1136, 640), (1024, 768), (1024, 800), (1152, 720), (1152, 768),
                               (1120, 832), (1280, 768), (1152, 864), (1334, 750), (1280, 800), (1152, 900),
                               (1024, 1024), (1280, 854), (1600, 768), (1280, 960), (1080, 1200),
                               (1440, 900), (1440, 900), (1280, 1024), (1440, 960), (1600, 900), (1400, 1050),
                               (1440, 1024), (1440, 1080), (1600, 1024), (1680, 1050), (1776, 1000), (1600, 1200),
                               (1600, 1280), (1920, 1280), (2048, 1152), (1792, 1344),
                               (1856, 1392), (2880, 900), (1800, 1440), (2048, 1280), (1920, 1400), (2538, 1080),
                               (2560, 1080), (1920, 1440), (2160, 1440), (2048, 1536), (2304, 1440), (2560, 1440),
                               (2304, 1728), (2560, 1600), (2560, 1700), (2560, 1800), (2560, 1920), (2736, 1824),
                               (2880, 1620), (2256, 1504), (2880, 1800), (2560, 2048), (2732, 2048), (2800, 2100),
                               (3200, 1800), (3000, 2000), (3200, 2048), (3200, 2400), (3440, 1440), (3840, 1600),
                                (3840, 2400), (4096, 2160), (5120, 2160), (4096, 3072), (4500, 3000),
                               (5120, 2880), (5120, 3200), (5120, 4096), (6400, 4096), (6400, 4800),
                               (7680, 4800), (8192, 4608), (10240, 4320), (8192, 8192) ]


cam_settings = dict()

def test_camera(cam, width, height, fps):
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cam.set(cv2.CAP_PROP_FPS, fps)

        _width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        _height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        _fps = int(cam.get(cv2.CAP_PROP_FPS))

        if (_width, _height, _fps) == (0,0,0):
            raise SystemError("Cameras are returning zeroes. Wait for them to cool off, then try again.")

        global cam_settings
        if cam not in cam_settings:
            cam_settings[cam] = set()
        print((_width, _height, _fps))
        if (_width, _height, _fps) not in cam_settings[cam]:
            cam_settings[cam].add((_width, _height, _fps))
            print([_width, _height, _fps])

def ready_camera(cam_num):
    #return false if camera didn't open at all
    global args

    global standard_resolution_list
    global standard_fps_list

    cam = cv2.VideoCapture(cam_num)

    #todo: determine fps. Start with max, all, nonstandard, else
    #todo: then do same with resolution, then check
    #todo: check for webcam accepting illegal fps or resolution values
    #todo: test for fps calculated vs fps requested, standard vs max

    if args.max_fps or args.max:
        fps_to_check = [240]
    else:
        fps_to_check = [240] # todo: remove temp val
    if args.max_resolution or args.max:
        res_to_check = (99999,99999)

        test_camera(cam, *res_to_check, fps_to_check[0])
        return cam

    if not args.all_resolutions and not args.all:
        if not args.nonstandard_resolutions and not args.nonstandard:
            # only check standardcam
            if not args.all_fps and not args.all:
                if not args.nonstandard_fps and not args.nonstandard:

                    for res in standard_resolution_list:
                        for fps in standard_fps_list:
                            test_camera(cam, *res, fps)



    return False

from get_webcams import capture_cams

def show_cams(cam_list  # type: List[cv2.VideoCapture]
              ):  # type: (...) -> None
    while True:
        frame_list = capture_cams(cam_list)
        for f in range(len(frame_list)):
            print(frame_list[f].shape)
            cv2.imshow('frame' + str(f), frame_list[f])
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if hasattr(args, 'check'):
    if len(args.check) > 0:
        for i in args.check:
            cam = ready_camera(i)
            show_cams([cam])
    else:
        i=0
        while show_cams([ready_camera(i)]):
            i += 1


