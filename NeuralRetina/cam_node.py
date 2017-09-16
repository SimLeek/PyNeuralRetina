import cv2


# todo: move cam_node and get_webcams into own directory to refactor. Cam node under source, get_webcams further in because core functionality.
# todo: add unit tests, with arg setting, to test all functions (https://stackoverflow.com/a/18161115)
# todo: store cam info in json file.



for arg in vars(args):
    print (arg, getattr(args, arg))

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

if __name__ == '__main__':
    from .camera.parse_args import parse_args
    import sys
    parse_args(sys.argv)
