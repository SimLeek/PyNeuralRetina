import redis
from enum import Enum

r = redis.StrictRedis(host='localhost', port=6379, db=0)

p = r.pubsub()

class CamType(Enum):
    max = 1

class Backend(Enum):
    cv = 1

class Cam():
    def __init__(self, cam_name):
        self.cam_name = cam_name
        self.cam_p = r.pubsub()
        self.cam_p.subscribe("cam."+str(cam_name))

    def run(self):
        msg = self.cam_p.get_message()
        while msg is None or msg['data']!='exit':
            msg = self.cam_p.get_message()
            cam_data = None
            r.publish("cam."+str(self.cam_name)+".frames", cam_data)

def publish_cam(cam_name, cam_type, backend = Backend.cv):

    if backend == Backend.cv:


