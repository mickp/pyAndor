import andorIxon as camera

import Pyro4

cameraObject = camera.Camera()
print "Providing camera as [pyroCam] on port 7767"
try:
    daemon = Pyro4.Daemon(port = 7767, host = '172.16.0.20')
    Pyro4.Daemon.serveSimple({cameraObject: 'pyroCam'},
            daemon = daemon, ns = False, verbose = True)
except Exception, e:
    print "Error serving camera:", e
    traceback.print_exc()
