# todo: draw trees to show correct calling and then check that and return errors before running code

# todo: make all these options through redis (just send a string to cam.parseargs, seperate by spaces, and use argparse)
import argparse

# todo: add ffmpeg, opencv, other camera getters as options


class CamArgs:
    update: bool
    show: bool
    publish: bool
    publish_all: bool

    ros: bool
    redis: bool

    max: bool
    max_resolution: bool
    max_fps: bool

    all: bool
    all_resolutions: bool
    all_fps: bool

    nonstandard: bool
    nonstandard_resolutions: bool
    nonstandard_fps: bool

class RedundantArgumentWarning(Warning):
    pass

def parse_args(args):
    """Our argument parser.
    https://stackoverflow.com/a/18161115
    """

    parser = argparse.ArgumentParser(description="ready and broadcast all webcams through redis.")

    parser.add_argument('-u', '--update', dest='update', action='store_true',
                        help="Update the camera system and store new data to JSON."
                             " Useful if you changed plugs or broke something.")

    parser.add_argument('-s', '--show', dest='show', action='store_true',
                        help="Show the camera input in a window.")

    parser.add_argument('-p', '--publish', dest='publish', action='store_true',
                        help="[DEFAULT BEHAVIOR] Publish camera frames through publisher subscriber.")

    parser.add_argument('--ros', dest='ros', action='store_true',
                        help="Publish and subscribe through ROS.")

    parser.add_argument('--redis', dest='redis', action='store_true',
                        help="Publish and subscribe through redis.")

    parser.add_argument('--publish_all', dest='publish_all', action='store_true',
                        help="Publish all cameras, instead of waiting for requests.")

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
                           help="Only check max resolution. ")
    parser.add_argument('--max_fps', dest='max_fps', action='store_true',
                           help="Only check max fps.")
    parser.add_argument('--max', dest='max', action='store_true',
                                   help="Only check max resolution and fps.")

    _args : CamArgs = parser.parse_args(args)

    if (_args.nonstandard and any([_args.all, _args.all_resolutions, _args.all_fps, _args.max, _args.max_resolution, _args.max_fps])) or \
       (_args.nonstandard_resolutions and any([_args.max_resolution, _args.all_resolutions])) or \
       (_args.nonstandard_fps and any([_args.max_fps, _args.all_fps])) or \
       (_args.all and any([_args.nonstandard_fps, _args.nonstandard_resolutions, _args.max, _args.max_fps, _args.max_resolution])) or \
       (_args.all_resolutions and any([_args.max_resolution])) or \
       (_args.all_fps and any([_args.max_fps])):
        parser.error('nonstandard, all, and max are mutually exclusive, unless seperately on resolution and fps.')
        raise SystemExit

    if (_args.max and any([_args.max_fps, _args.max_resolution])) or \
       (_args.all and any([_args.all_fps, _args.all_resolutions])) or \
       (_args.nonstandard and any([_args.nonstandard_fps, _args.nonstandard_resolutions])):
        raise RedundantArgumentWarning("max, all, and nonstandard make max_resolution, all_fps, etc. redundant.")

    if any([_args.all, _args.all_resolutions, _args.all_fps,
    _args.nonstandard, _args.nonstandard_resolutions, _args.nonstandard_fps]) \
    and not _args.update:
        parser.error('-u must be used with any fps or resolution options (except --max).')
        raise SystemExit

    if any([_args.publish_all, _args.ros, _args.redis]) and not _args.publish:
        _args.publish = True

    return _args


if __name__ == '__main__':
    import sys
    parse_args(sys.argv)
