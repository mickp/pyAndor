import andorsdk as sdk
import threading
from ctypes import byref, c_float, c_int, c_long

dll_lock = threading.Lock()

def with_lock(func):
        def wrapper(self, *args, **kwargs):
            had_lock_on_entry = self.has_lock
            
            try:
                if not had_lock_on_entry:
                    dll_lock.acquire()
                    sdk.SetCurrentCamera(self.handle)
                    self.has_lock = True
                    print "lock acquired, camera set"
                    result = func(self, *args, **kwargs)
                    dll_lock.release()
                    self.has_lock = False
                    print "lock released"
                else:
                    result = func(self, *args, **kwargs)
                return result
            except:
                dll_lock.release()
                self.has_lock = False
                raise

        return wrapper


class Camera(object):
    """Camera class for Andor cameras.
    
    All instance methods should be decorated with @with_lock: this obtains a
    lock on the DLL, and sets the target camera for DLL methods."""

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
        self.is_initialized = False
        self.nx, self.ny = None, None
        self.caps = sdk.AndorCapabilities()
        self.read_mode = None
        self.vs_speed = None


    @with_lock
    def cooler_on(self):
        sdk.CoolerON()


    @with_lock
    def cooler_off(self):
        sdk.CoolerOFF()


    @with_lock
    def initialize(self):
        if not self.is_initialized:
            if sdk.Initialize('') == sdk.DRV_SUCCESS:
                self.is_initialized = True
                self.get_capabilities()


    @with_lock
    def get_capabilities(self):
        sdk.GetCapabilities(byref(self.caps))


    @with_lock
    def get_detector(self):
        nx, ny = c_int(), c_int()
        sdk.GetDetector(byref(nx), byref(ny))
        self.nx = nx.value
        self.ny = ny.value
        return (self.nx, self.ny)


    @with_lock
    def get_hardware_version(self):
        pcb, decode, dummy1, dummy2, version, build = 6 * [c_int()]
        plist = [pcb, decode, dummy1, dummy2, version, build]
        parameters = [byref(p) for p in plist]
        sdk.GetHardwareVersion(*parameters)
        result = [p.value for p in plist]
        return result


    @with_lock
    def get_fastest_recommended_vs_speed(self):
        index = c_int()
        speed = c_float()
        sdk.GetFastestRecommendedVSSpeed(byref(index), byref(speed))
        self.vs_speed = speed.value
        return speed.value


    @with_lock
    def is_preamp_gain_available(self, channel, amplifier, index, gain):
        status = c_int()
        sdk.IsPreAmpGainAvailable(int(channel), 
                                  int(amplifier), 
                                  int(index), 
                                  int(gain),
                                  byref(status))
        return status.value


    @with_lock
    def set_dma_parameters(self, max_images_per_dma, seconds_per_dma):
        sdk.SetDMAParameters(int(max_images_per_dma),
                             float(seconds_per_dma))


    @with_lock
    def set_em_gain_mode(sefl, mode):
        sdk.SetEMGainMode(int(mode))


    @with_lock
    def set_fan_mode(self, mode):
        sdk.SetFanMode(int(mode))


    @with_lock
    def set_preamp_gain(self, index):
        sdk.SetPreAmpGain(int(index))


    @with_lock
    def set_read_mode(self, n):
        if n != self.read_mode:
            sdk.SetReadMode(int(n))
