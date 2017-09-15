# todo: draw trees to show correct calling and then check that and return errors before running code

# todo: make all these options through redis (just send a string to cam.parseargs, seperate by spaces, and use argparse)
import argparse

# todo: add ffmpeg, opencv, other camera getters as options

def parse_args(args):
    """Our argument parser.
    https://stackoverflow.com/a/18161115
    """
    parser = argparse.ArgumentParser(description="ready and broadcast all webcams through redis.")

    parser.add_argument('-s', '--show', dest='publish', action='store_true',
                        help="[DEFAULT BEHAVIOR] Publish camera frames through publisher subscriber.")

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

    #add checks here

    return parser