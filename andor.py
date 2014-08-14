"""A module for control of Andor cameras via the Andor SDK.

This module defines the Camera class for Andor cameras."""
import andorsdk as sdk
import functools
import sys
import threading
from ctypes import byref, c_float, c_int, c_long, c_ulong
from ctypes import create_string_buffer

## A lock to prevent concurrent calls to the DLL by different Cameras.
dll_lock = threading.Lock()

##TODO
# Methods Called from cockpit
# abort()
# cammode(is16bit, isConventional, speed, EMgain, None)
# exposeTillAbort(bool)
# getexp()
# gettemp()
# getTimesExpAccKin()
# init
# quit()
# setdarkLRTB(int, int, int, int)
# setExposureTime(int/float?)
# setImage:     height, width = setImage(0, yOffset, None, height)
# setskipLRTB:  imagesize = setskipLRTB(left, right, top, bottom)
# setshutter(int)
# settemp(int)
# settrigger(bool)
# start(isIxonPlus)


def with_camera(func):
    """A decorator for camera functions.

    This decorator obtains a lock on the DLL and calls SetCurrentCamera
    to ensure that the library acts on the correct piece of hardware."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):   
        had_lock_on_entry = self.has_lock
        if not had_lock_on_entry:
            dll_lock.acquire()
            self.has_lock = True
        try:
            sdk.SetCurrentCamera(self.handle)
            result = func(self, *args, **kwargs)
        except:
            if dll_lock.locked():  
                dll_lock.release()
                self.has_lock = False
            raise

        if dll_lock.locked() and not had_lock_on_entry:
            dll_lock.release()
            self.has_lock = False
        return result
    return wrapper


def sdk_call(func):
    """A decorator for DLL functions called as methods of Camera.

    This decorator simply passes args to func, without self."""
    @functools.wraps(func)
    def sdk_wrapper(self, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            raise
    return sdk_wrapper


class CameraManager(object):
    """A class to manage Camera instances.

    This used to be handled by class variables and class methods, but
    that approach will not work when we need to spread several cameras
    over separate processes."""
    def __init__(self):
        # Map handle values to camera instances
        self.handle_to_camera = {}
        # A list of camera instances
        self.cameras = []


    def update_cameras(self):
        """Search for cameras and create Camera instances.

        Camera instances are tracked in the class variables
        Camera.cameralist and Camera.handle_to_camera."""
        for cam in self.cameras:
            self.cameras.remove(cam)

        num_cameras = c_long()
        sdk.GetAvailableCameras(byref(num_cameras))

        for i in range(num_cameras.value):
            handle = c_long()
            sdk.GetCameraHandle(i, byref(handle))
            self.cameras.append(Camera(handle))
            self.handle_to_camera.update({handle.value: i})


class CameraMeta(type):
    """A metaclass that adds DLL methods to the Camera class.

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

    # Use the CameraMeta class to add DLL methods to this class.
    __metaclass__ = CameraMeta


    def __init__(self, handle):
        """Init a Camera instance for hardware with ID=handle."""
        self.handle = handle
        self.has_lock = False
        self.nx, self.ny = None, None
        self.caps = sdk.AndorCapabilities()
        self.read_mode = None
        self.vs_speed = None


    @with_camera
    def abort(self):
        self.AbortAcquisition()


    @with_camera
    def prepare(self):
        """Prepare the camera for data acquisition."""
        self.get_detector()
        self.get_capabilities()


    @with_camera
    def get_acquisition_timings(self):
        exposure = c_float()
        accumulate = c_float()
        kinetic = c_float()
        sdk.GetAcquisitionTimings(exposure, accumulate, kinetic)
        return (exposure, accumulate, kinetic)


    @with_camera
    def get_amp_desc(self, index):
        chars =  create_string_buffer(128)
        sdk.GetAmpDesc(index, s, len(s))
        return s.value


    @with_camera
    def get_camera_serial_number(self):
        sn = c_int()
        sdk.GetCameraSerialNumber(sn)
        return sn.value


    @with_camera
    def get_capabilities(self):
        sdk.GetCapabilities(self.caps)


    @with_camera
    def get_detector(self):
        """Populate nx and ny with the detector geometry."""
        nx, ny = c_int(), c_int()
        sdk.GetDetector(byref(nx), byref(ny))
        self.nx = nx.value
        self.ny = ny.value
        return (self.nx, self.ny)


    @with_camera
    def get_em_advanced(self):
        state = c_int()
        sdk.GetEMAdvanced(state)
        return state.value


    @with_camera
    def get_emccd_gain(self):
        gain = c_int()
        sdk.GetEMCCDGain(gain)
        return gain.value


    @with_camera
    def get_em_gain_range(self):
        low = c_int()
        high = c_int()
        sdk.GetEMGainRange(low, high)
        return (low.value, high.value)


    @with_camera
    def get_fk_exposure_time(self):
        t = c_float()
        sdk.GetFKExposureTime(t)
        return t.value


    @with_camera
    def get_fk_v_shift_speed_f(self, index):
        speed = c_float()
        sdk.GetFKVShiftSpeedF(index, speed)
        return speed.value


    @with_camera
    def get_fastest_recommended_vs_speed(self):
        index = c_int()
        speed = c_float()
        sdk.GetFastestRecommendedVSSpeed(index, speed)
        self.vs_speed = speed.value
        return (index.value, speed.value)


    @with_camera
    def get_hardware_version(self):
        pcb, decode, dummy1, dummy2, version, build = 6 * [c_ulong()]
        plist = [pcb, decode, dummy1, dummy2, version, build]
        parameters = [byref(p) for p in plist]
        sdk.GetHardwareVersion(*parameters)
        result = [p.value for p in plist]
        return result


    @with_camera
    def is_preamp_gain_available(self, channel, amplifier, index, gain):
        status = c_int()
        sdk.IsPreAmpGainAvailable(int(channel), 
                                  int(amplifier), 
                                  int(index), 
                                  int(gain),
                                  status)
        return status.value