import andorsdk as sdk
import threading
from ctypes import byref, c_float, c_int, c_long, c_ulong
import functools

dll_lock = threading.Lock()

def with_camera(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):   
        had_lock_on_entry = self.has_lock
        try:
            if not had_lock_on_entry:
                dll_lock.acquire()
                self.has_lock = True
                sdk.SetCurrentCamera(self.handle)
                result = func(self, *args, **kwargs)
                dll_lock.release()
                self.has_lock = False
            else: # already had lock
                result = func(self, *args, **kwargs)
            return result
        except:
            if dll_lock.locked():  
                dll_lock.release()
            self.has_lock = False
            raise
    return wrapper


def sdk_call(func):
    ## Simply passes args to func, without self.
    @functools.wraps(func)
    def sdk_wrapper(self, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            raise
    return sdk_wrapper


class CameraMeta(type):
    """Metaclass that adds DLL methods to the Camera class.

    Methods from the SDK DLL are wrapped by 'sdk_call' to remove 'self' from
    the args, then by 'with_camera' so that
    * a lock is obtained on the DLL;
    * the DLL is set to act on the Camera instance;
    * the DLL method is called;
    * the lock is released."""
    def __new__(meta, classname, supers, classdict):
        for f in sdk.camerafuncs:
            classdict[f.__name__] = with_camera(sdk_call(f))
        return type.__new__(meta, classname, supers, classdict)


class Camera(object):
    """Camera class for Andor cameras.
    
    All instance methods should be decorated with @with_camera: this obtains a
    lock on the DLL, and sets the target camera for DLL methods."""
    __metaclass__ = CameraMeta
    # Map handle values to camera instances
    handle_to_camera = {}
    # A list of camera instances
    cameras = []


    @classmethod
    def update_cameras(cls):      
        cameras = cls.cameras
        handle_to_camera = cls.handle_to_camera

        for cam in cameras:
            cameras.remove(cam)

        num_cameras = c_long()
        sdk.GetAvailableCameras(byref(num_cameras))

        for i in range(num_cameras.value):
            handle = c_long()
            sdk.GetCameraHandle(i, byref(handle))
            cameras.append(Camera(handle))
            handle_to_camera.update({handle.value: i})


    def __init__(self, handle):
        self.handle = handle
        self.has_lock = False
        self.nx, self.ny = None, None
        self.caps = sdk.AndorCapabilities()
        self.read_mode = None
        self.vs_speed = None


    def prepare(self):
        self.get_detector()
        self.GetCapabilities(self.caps)



    @with_camera
    def get_detector(self):
        nx, ny = c_int(), c_int()
        self.GetDetector(byref(nx), byref(ny))
        self.nx = nx.value
        self.ny = ny.value
        return (self.nx, self.ny)


    @with_camera
    def get_hardware_version(self):
        pcb, decode, dummy1, dummy2, version, build = 6 * [c_ulong()]
        plist = [pcb, decode, dummy1, dummy2, version, build]
        parameters = [byref(p) for p in plist]
        self.GetHardwareVersion(*parameters)
        result = [p.value for p in plist]
        return result


    @with_camera
    def get_fastest_recommended_vs_speed(self):
        index = c_int()
        speed = c_float()
        self.GetFastestRecommendedVSSpeed(index, speed)
        self.vs_speed = speed.value
        return (index.value, speed.value)


    @with_camera
    def is_preamp_gain_available(self, channel, amplifier, index, gain):
        status = c_int()
        sdk.IsPreAmpGainAvailable(int(channel), 
                                  int(amplifier), 
                                  int(index), 
                                  int(gain),
                                  status)
        return status.value
