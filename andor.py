"""A module for control of Andor cameras via the Andor SDK.

Call from the command line to spawn Pyro objects in separate
processes.
Alternatively, import CameraManager for multiple cameras in one
process.This module defines the Camera class for Andor cameras.

=== Interesting features of the Andor SDK. ===
The DLL relies on runtime-generated handles to access specific
cameras. The handles appear to be generated when there is a call to
GetCameraHandle or Initialize.

The handle for a given camera is not necessarily the same from one
process to the next, which means we need to rely on the camera serial
number. However, it is not possible to sucessfully call
GetCameraSerialNumber until Initialize('') has been completed. Once
Initialize has been called in one process, it grabs the CurrentCamera:
subsequent calls to Initialize in processes that have the same
CurrentCamera will fail, unless the original process made an explicit
call to ShutDown.

So we can't spawn a process then select a known camera:  we have to
blindly pick a different camera for each process and run with what it
gets.

Function names:
* Local function definitions use names as lower_case.
* Direct calls Andor's DLL uses the CapitalCamelCase names it exports.
"""

import andorsdk as sdk
import functools
import numpy
import Pyro4
Pyro4.config.SERIALIZER = 'pickle'
Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')
import sys, os, psutil
import threading
import time
import weakref
from ctypes import byref, c_float, c_int, c_long, c_ulong
from ctypes import create_string_buffer, c_char, c_bool
from multiprocessing import Process, Value
from collections import namedtuple

try:
    from cameras import camera_keys as _camera_keys
    from cameras import cameras as _cameras
except:
    CAMERAS = {}
else:
    CAMERAS = {camera[0]: dict(zip(_camera_keys, camera)) for camera in _cameras}

EPSILON = sys.float_info.epsilon


# A list of the camera models this module supports (or should support.)
SUPPORTED_CAMERAS = ['ixon', 'ixon_plus', 'ixon_ultra']
TRIGGERS = {-1: 'off',
            0: 'internal',
            1: 'external',
            6: 'ex-start',
            7: 'ex-bulb',
            10: 'software',
            12: 'ex-chrge'}

## A lock to prevent concurrent calls to the DLL by different Cameras.
dll_lock = threading.Lock()


# Amplfier modes are defined by the AD channel, amplifier type,
# and an index into the HSSpeed table.
# I use a list of tuples if label and mode to preserve the label order:
# to preserve this order in an OrderedDict, each mode would have to be
# added individually, making it more difficult both to read or edit.
# Changed this - named tuple's can't work over Pyro.  Doesn't work as
# class AmplifierMode(dict), either.  So just write a function that
# returns the right dict.
def AmplifierMode (label, channel, amplifier, index):
        return {'label': label,
                'channel': channel,
                'amplifier': amplifier,
                'index': index}

AMPLIFIER_MODES = {
    sdk.AC_CAMERATYPE_IXONULTRA: [
        # Verified against the hardware.
        AmplifierMode('EM 1MHz'   , 0, 0, 3),
        AmplifierMode('EM 5MHz'   , 0, 0, 2),
        AmplifierMode('EM 10MHz'  , 0, 0, 1),
        AmplifierMode('EM 17MHz'  , 0, 0, 0),
        AmplifierMode('Conv 80kHz', 0, 1, 2),
        AmplifierMode('Conv 1MHz' , 0, 1, 1),
        AmplifierMode('Conv 3MHz' , 0, 1, 0),
        ],
    sdk.AC_CAMERATYPE_IXON: [
        # Needs to be verified.
        AmplifierMode('EM16 1MHz'   , 1, 0, 0),
        AmplifierMode('EM14 3MHz'   , 0, 0, 0),
        AmplifierMode('EM14 5MHz'   , 0, 0, 1),
        AmplifierMode('EM14 10MHz'  , 0, 0, 2),
        AmplifierMode('Conv16 1MHz' , 1, 1, 0),
        AmplifierMode('Conv16 3MHz' , 0, 1, 0),
        ]
    }


def with_camera(func):
    """A decorator for camera functions.

    If there are multiple cameras per process, this decorator obtains a
    lock on the DLL and calls SetCurrentCamera to ensure that the
    library acts on the correct piece of hardware.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.singleton:
            # There may be > 1 cameras per process, so lock the DLL.
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

        else:
            # There is only 1 camera per process - no locks required.
            result = func(self, *args, **kwargs)

        return result
    return wrapper


def sdk_call(func):
    """A decorator for DLL functions called as methods of Camera.

    This decorator simply passes args to func, without self.
    """
    @functools.wraps(func)
    def sdk_wrapper(self, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            raise
    return sdk_wrapper


class CameraMeta(type):
    """A metaclass that adds DLL methods to the Camera class.

    Methods from the SDK DLL are wrapped by 'sdk_call' to remove 'self'
    from the args, then by 'with_camera' so that
    * a lock is obtained on the DLL;
    * the DLL is set to act on the Camera instance;
    * the DLL method is called;
    * the lock is released.
    """
    def __new__(meta, classname, supers, classdict):
        for f in sdk.camerafuncs:
            classdict[f.__name__] = with_camera(sdk_call(f))
        return type.__new__(meta, classname, supers, classdict)


class CameraLogger(object):
    def __init__(self):
        self.fh = None

    def log(self, message):
        if self.fh:
            self.fh.write(time.strftime('%Y-%m-%d %H:%M:%S:  '))
            self.fh.write(message + '\n')
            self.fh.flush()

    def open(self, filename):
        path = os.path.dirname(os.path.abspath(__file__))
        self.fh = open(os.path.join(path, str(filename) + '.txt'), 'w')

    def close(self):
        self.fh.close()
        self.fh = None


class Camera(object):
    """Camera class for Andor cameras.

    All instance methods should be decorated with @with_camera: this
    obtains a lock on the DLL, and sets the target camera for DLL
    methods.
    """
    # Use the CameraMeta class to add DLL methods to this class.
    __metaclass__ = CameraMeta


    def __enter__(self):
        """Context-manager entry."""
        return self


    @with_camera
    def __exit__(self, type, value, traceback):
        """Context-manager exit - call ShutDown to free camera."""
        ## Shut down the camera.
        print "Shutting down camera with handle %s." % self.handle
        try:
            self.ShutDown()
        except:
            # May raise exception if camera never initialized - not a problem.
            pass
        self.enabled = False
        self.triggering = None


    @with_camera
    def __del__(self):
        self.ShutDown()


    def __init__(self, handle, singleton=False):
        """Init a Camera instance for hardware with ID=handle."""
        # Number of exposures fetched since last StartAcquisition.
        self.count = 0
        # SDK's handle for the camera
        self.handle = handle
        # Does this camera have the lock on the DLL?
        self.has_lock = False
        # Detector dimensions in pixels.
        self.nx, self.ny = None, None
        # Detector capabilties.
        self.caps = sdk.AndorCapabilities()
        # Is this the only camera in this process?
        self.singleton = singleton
        # Is the camera enabled?
        self.enabled = False
        # Is the camera armed for acquisition?
        self.acquiring = None
        # The current acquisition mode.
        self.acquisition_mode = None
        # Thread to handle data on exposure
        self.data_thread = None
        self.settings = {}
        self.client = None
        self.logger = CameraLogger()


    ### Client functions. ###
    @with_camera
    def abort(self):
        self.AbortAcquisition()
        self.acquiring = False


    @with_camera
    def arm(self):
        self.logger.log('Arming camera.')
        if not self.is_ready():
            pass
        #    raise Exception("Camera not ready.")

        # Open the shutter.
        # SetShutter(type, mode, t_close_ms, t_open_ms)
        # type = 0: TTL high = open; 1: TTL low = open
        # mode = 0: auto, 1: open; 2: closed
        self.SetShutter(1, 1, 1, 1)
        # SetReadMode to image.
        self.SetReadMode(4)
        # Set image to full sensor.
        self.SetImage(1, 1, 1, self.nx, 1, self.ny)
        # Reset image count.
        self.count = 0

        # Make sure there is a data thread running.
        if not self.data_thread or not self.data_thread.is_alive():
            self.logger.log('Starting data thread.')
            self.data_thread = DataThread(self, self.client)
            self.update_transform()
            self.data_thread.start()

        # Set camera to espond to triggers.
        self.logger.log('Starting acquisition.')
        try:
            self.StartAcquisition()
        except:
            raise
        else:
            self.acquiring = True


    @with_camera
    def disable(self):
        self.logger.log('Disabling camera.')
        self.enabled = False
        try:
            self.abort()
        except:
            pass
        if self.data_thread:
            if self.data_thread.is_alive():
                self.data_thread.stop()
                self.data_thread.join(5)
            self.data_thread = None


    @with_camera
    def enable(self, settings={}):
        # Clear the flag so that our client will poll until it is True.
        self.disable()

        try:
            # Stop whatever the camera was doing.
            self.abort()
        except Exception:
            try:
                self.Initialize('')
            except:
                raise

        # Get detector size and capabilities.
        self.get_detector()
        self.get_capabilities()

        # Enable temperature control.
        if settings.get('isWaterCooled'):
            # Use fan at low speed.
            self.SetFanMode(1)
        else:
            # Use fan at full speed.
            self.SetFanMode(0)

        # If a temperature is specified, then use it. Otherwise, hardware
        # default or previos value will be used.
        target_temperature = settings.get('targetTemperature')
        if target_temperature is not None:
            self.set_target_temperature(target_temperature)


        # Turn the cooler on.
        self.CoolerON()


        # Set acquisition mode. In old UCSF code, the mode was set to:
        #  5 for run 'til abort without frame transfer;
        #  7 for run 'til abort with frame transfer.
        # However, mode 7 is not documented, so here we use mode 5 and
        # determine frame transfer usage with SetFrameTransferMode.
        # In old UCSF code, this was achieved by using acquisition mode 7.
        self.set_acquisition_mode(5)


        self.update_settings(settings, init=True)

        # Recalculate VS speed.
        self.set_fastest_vs_speed()

        # Set enabled indicator flag.
        self.enabled = True

        self.arm()

        self.logger.log('Camera enabled.')

        return self.enabled


    def get_image_size(self):
        return (self.nx, self.ny)


    @with_camera
    def get_exposure_time(self):
        (exposure, accumulate, kinetics) = self.get_acquisition_timings()
        if self.acquisition_mode in [1, 5]:
            # single exposure or run untul abort
            t = exposure
        elif self.acquisition_mode == 2:
            # accumulate mode
            t = accumulate
        elif self.acquisition_mode in [3, 4]:
            # kinetics or fast kinetics
            t = kinetics
        # Assume worst-case floating point underestimation
        return t + t * EPSILON


    @with_camera
    def get_min_time_between_exposures(self):
        (exposure, accumulate, kinetics) = self.get_acquisition_timings()
        if self.acquisition_mode in [1, 5, 7]:
            # single exposure or run until abort
            t = self.get_read_out_time()
            # Assume worst-case floating point underestimation.
            t += EPSILON * t
            if not self.settings.get('fastTrigger'):
                t_kc = self.get_keep_clean_time()
                # Assume worst-case floating point underestimation.
                t_kc += EPSILON * t_kc
                t += t_kc
            return t
        elif self.acquisition_mode == 2:
            # accumulate mode
            return accumulate - exposure
        elif self.acquisition_mode in [3, 4]:
            # kinetics mode
            return kinetics - exposure
        else:
            # acquisition mode not configured.
            # Return 100ms, although should consider raising an exception here.
            return 0.1


    def get_settings(self):
        """Return the current settings dict. Useful for Pyro debug."""
        return self.settings


    @with_camera
    def make_safe(self):
        """ Put the camera into a safe but active state."""
        # Set lowest EM gain on EMCCD cameras.
        if self.caps.ulSetFunctions & sdk.AC_SETFUNCTION_EMCCDGAIN:
            self.SetEMCCDGain(0)

        # Switch to conventional amplifier on supported cameras.
        if self.caps.ulCameraType in [sdk.AC_CAMERATYPE_CLARA,
                                      sdk.AC_CAMERATYPE_IXON,
                                      sdk.AC_CAMERATYPE_IXONULTRA,
                                      sdk.AC_CAMERATYPE_NEWTON]:
            self.SetOutputAmplifier(1)
            # This means the amplier mode is undefined.
            self.settings.update({'amplifierMode': None})

        self.logger.log('Camera disabled and made safe.')
        self.enabled = False


    def receiveClient(self, uri):
        """Handle connection request from cockpit client."""
        if uri is None:
            self.logger.log('Clearing receiveClient.')
            self.client = None
        else:
            self.logger.log('Setting receiveClient to ' + uri + '.')
            self.client = Pyro4.Proxy(uri)
            if self.data_thread is not None:
                self.logger.log('receiveClient set in data_thread.')
                self.data_thread.set_client(self.client)


    def skip_images(self, next=None, every=None):
        if next:
            self.logger.log('Skipping next %d images.' % next)
            self.data_thread.skip_next_n_images = next

        if every:
            self.logger.log('Skipping every %d images.' % every)
            self.data_thread.skip_every_n_images = every


    def update_transform(self, transform=None):
        # If there is a data thread, then update its transform
        if self.data_thread is None:
            # Nothing to do.
            self.logger.log('Received transform %s. No data_thread to update.' % (transform,))
            return
        amp_mode = self.settings.get('amplifierMode')
        flip = amp_mode.get('label').startswith('Conv')
        
        # orientation transform
        t1 = self.settings.get('baseTransform') or (0, 0, 0)
        # readout-mode transform
        t2 = (0 if not flip else 1, 0, 0)
        # requested transform
        t3 = self.settings.get('pathTransform') or (0, 0, 0)

        # resultant transform
        tprime = tuple(t1[i] ^ t2[i] ^ t3[i] for i in range(3))

        # set this transform on the data_thread
        self.data_thread.set_transform(tprime)
        logstr =  'Updating data_thread transform:\n'
        logstr += '  base:\t%s\n' % (t1,)
        logstr += '  mode:\t%s\n' % (t2,)
        logstr += '  path:\t%s\n' % (t3,)
        logstr += '  result:\t%s\n' % (tprime,)
        self.logger.log(logstr)

    @with_camera
    def update_settings(self, settings, init=False):
        # Store the triggering state on entry.
        acquiring_on_entry = self.acquiring

        if init:
            # Assume nothing about state: set everything.
            # Update our settings with incoming settings.
            self.settings.update(settings)
            update_keys = set(self.settings.keys())
        else:
            # Only update new and changed values.
            my_keys = set(self.settings.keys())
            their_keys = set(settings.keys())
            update_keys = set(key for key in
                               my_keys.intersection(their_keys)
                               if self.settings[key] != settings[key])

            
        if len(update_keys) == 0:
            # there is nothing to update
            return self.enabled
        else:
            self.logger.log('Need to update %d settings:' % len(update_keys))

        self.logger.log('Updating settings.')
        # Clear the flag so that our client will poll until it is True.
        self.enabled = False

        



        try:
            # Stop whatever the camera was doing.
            self.abort()
        except Exception:
            try:
                self.Initialize('')
            except:
                raise

        # Update this camera's settings dict.
        self.settings.update(settings)



        # Apply changed settings to the hardware.
        for key in update_keys:
            val = self.settings.get(key, None)
            self.logger.log('   %s:  %s' % (key, val))
            if key == 'exposureTime':
                self.set_exposure_time(float(val))
            elif key == 'EMGain':
                self.SetEMCCDGain(int(val))
            elif key == 'amplifierMode':
                self.set_amplifier_mode(val)
            elif key == 'targetTemperature':
                self.set_target_temperature(val)
            elif key == 'frameTransfer':
                self.SetFrameTransferMode(val)
            elif key == 'pathTransform':
                self.update_transform(val)
            elif key == 'fastTrigger':
                self.SetFastExtTrigger(val)
            elif key == 'triggerMode':
                self.SetTriggerMode(val)
    
        # Recalculate and apply fastest vertical shift speed.
        self.set_fastest_vs_speed()
        
        # Set enabled indicator flag.
        self.enabled = True

        if acquiring_on_entry:
            self.StartAcquisition()
            self.acquiring = True
            self.logger.log('Resuming acquisition after settings updates.')
        
        return self.enabled


    ### (Fairly) simple wrappers and utility functions. ###
    @with_camera
    def get_acquisition_timings(self):
        exposure = c_float()
        accumulate = c_float()
        kinetic = c_float()
        sdk.GetAcquisitionTimings(exposure, accumulate, kinetic)
        return (exposure.value, accumulate.value, kinetic.value)


    @with_camera
    def get_amp_desc(self, index):
        s = create_string_buffer(128)
        sdk.GetAmpDesc(index, s, len(s))
        return s.value


    @with_camera
    def get_amplifier_modes(self):
        if not self.caps.ulCameraType:
            self.get_capabilities()
        # Return the amplifier mode labels.
        modes = AMPLIFIER_MODES[self.caps.ulCameraType]
        
        return modes


    @with_camera
    def get_camera_serial_number(self):
        sn = c_int()
        sdk.GetCameraSerialNumber(sn)
        return sn.value


    @with_camera
    def get_capabilities(self):
        sdk.GetCapabilities(self.caps)
        return self.caps


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
    def get_keep_clean_time(self):
        t = c_float()
        self.GetKeepCleanTime(t)
        return t.value


    @with_camera
    def get_read_out_time(self):
        t = c_float()
        self.GetReadOutTime(t)
        return t.value


    @with_camera
    def get_temperature(self):
        temperature = c_int()
        self.temperature_state = sdk.GetTemperature(temperature)
        return temperature.value


    @with_camera
    def get_hardware_version(self):
        pcb, decode, dummy1, dummy2, version, build = 6 * [c_ulong()]
        plist = [pcb, decode, dummy1, dummy2, version, build]
        parameters = [byref(p) for p in plist]
        sdk.GetHardwareVersion(*parameters)
        result = [p.value for p in plist]
        return result


    @with_camera
    def get_head_model(self):
        s = create_string_buffer(128)
        sdk.GetHeadModel(s)
        return s.value


    def is_enabled(self):
        return self.enabled


    @with_camera
    def is_preamp_gain_available(self, channel, amplifier, index, gain):
        status = c_int()
        sdk.IsPreAmpGainAvailable(int(channel),
                                  int(amplifier),
                                  int(index),
                                  int(gain),
                                  status)
        return status.value


    @with_camera
    def is_ready(self):
        status = self.GetTemperature(c_int())
        ready = (status == sdk.DRV_TEMP_STABILIZED) and self.enabled
        return ready


    @with_camera
    def set_amplifier_mode(self, mode):
        # If no mode was specified, use the first mode."""
        if mode == None:
            mode = self.get_amplifier_modes()[-1]    
        channel = int(mode['channel'])
        amplifier = int(mode['amplifier'])
        index = int(mode['index'])
        result = []
        try:
            result.append(self.SetADChannel(channel))
            result.append(self.SetOutputAmplifier(amplifier))
            result.append(self.SetHSSpeed(amplifier, index))
        except Exception as e:
            return e.__repr__()
        else:
            self.settings.update({'amplifierMode': mode})
            # We also need to update the data transform.
            self.update_transform()


    @with_camera
    def set_acquisition_mode(self, mode):
        self.SetAcquisitionMode(mode)
        self.acquisition_mode = mode


    @with_camera
    def set_em_gain(self, value):
        return self.SetEMCCDGain(value)


    @with_camera
    def set_exposure_time(self, exposure_time):
        """Set the exposure time and update vertical shift speed."""
        self.SetExposureTime(float(exposure_time))
        self.set_fastest_vs_speed()
        exposure, accumulate, kinetic = self.get_acquisition_timings()
        return exposure
    

    @with_camera
    def set_fastest_vs_speed(self):
        """Update the vertical shift speed to fasted recommended speed."""
        (index, speed) = self.get_fastest_recommended_vs_speed()
        self.SetVSSpeed(int(index))
        return speed

    @with_camera
    def set_target_temperature(self, target):
        t_min = c_int()
        t_max = c_int()
        self.GetTemperatureRange(t_min, t_max)
        # Temperature set-point is limited to available range.
        target = max(t_min.value, min(t_max.value, target))
        self.SetTemperature(target)



class DataThread(threading.Thread):
    """A thread to collect acquired data and dispatch it to a client."""
    def __init__(self, cam, client):
        threading.Thread.__init__(self)
        self.skip_next_n_images = 0
        self.exposure_count = 0
        self.sent_count = 0
        self.skip_every_n_images = 1
        self.cam = weakref.proxy(cam)
        self.image_array = numpy.zeros((cam.nx, cam.ny), dtype=numpy.uint16)
        self.n_pixels = cam.nx * cam.ny
        self.client = client
        self.run_flag = True
        # Transform operation: fliplr, flipud, rot90
        self.transform = (0, 0, 0)
        self.transform_lock = threading.Lock()


    def __del__(self):
        if self.is_alive:
            self.should_quit = True


    def get_transformed_image(self):
        m = self.image_array
        with self.transform_lock:
            flips = (self.transform[0], self.transform[1])
            rotation = self.transform[2]

        return {(0,0): numpy.rot90(m, rotation),
                (0,1): numpy.flipud(numpy.rot90(m, rotation)),
                (1,0): numpy.fliplr(numpy.rot90(m, rotation)),
                (1,1): numpy.fliplr(numpy.flipud(numpy.rot90(m, rotation)))}[flips]


    def run(self):
        self.cam.logger.log('    DataThread: entering run loop.')
        while self.run_flag:
            try:
                result = self.cam.GetOldestImage16(self.image_array,
                                                   self.n_pixels)
            except:
                self.cam.logger.log('    DataThread: Exception when tying GetOldestImage16.')
                raise

            if result[0] == sdk.DRV_SUCCESS:
                # increment the camera exposure counter
                self.cam.count += 1
                # increment our exposure counter
                self.exposure_count += 1
                # indicate that there is data to send
                send_data = True

                if self.skip_next_n_images > 0:
                    self.skip_next_n_images -= 1
                    send_data = False
                    self.cam.logger.log('    DataThread: Skipping image (next N).')

                if self.exposure_count % self.skip_every_n_images > 0:
                    send_data = False
                    self.cam.logger.log('    DataThread: Skipping image (every N).')
            else:
                send_data = False

            if send_data:
                # Timestamp.  When using external triggering, the camera
                # offers nothing more accurate than the system time.
                timestamp = time.time()
                if self.client is not None:
                    try:
                        self.client.receiveData('new image',
                                                 self.get_transformed_image(),
                                                 timestamp)
                    except Pyro4.errors.ConnectionClosedError:
                        self.cam.logger.log('    DataThread: Data not sent - client not listening.')
                        # No-one is listening.
                        self.cam.abort()
                        self.should_quit = True
                    # self.cam.logger.log('    DataThread: Data from camera sent to client.')
                    self.sent_count += 1
                else:
                    self.cam.logger.log('    DataThread: Data not sent - no client to receive data.')
            else:
                time.sleep(0.01)
        self.cam.logger.log('    DataThread: exiting run loop.')


    def set_client(self, client):
        self.client = client


    def set_transform(self, transform):
        if (type(transform) is tuple and len(transform) == 3 and 
                all(t ==0 or t == 1 for t in transform)):
            with self.transform_lock:
                self.transform = transform
        else:
            raise Exception('Bad transform: expected three-element tuple of 1s and 0s.')


    def stop(self):
        self.run_flag = False
        self.cam.logger.log('    DataThread: sent %d of %d exposures.' 
                           % (self.sent_count, self.exposure_count))


class CameraManager(object):
    """A class to manage Camera instances in a single process.

    Useful for debugging.
    """
    def __init__(self):
        # Map handle values to camera instances
        self.handle_to_camera = {}
        # A list of camera instances
        self.cameras = []
        self.num_cameras = c_long()
        sdk.GetAvailableCameras(self.num_cameras)


    def update_cameras(self):
        """Search for cameras and create Camera instances.

        Camera instances are tracked in the class variables
        Camera.cameralist and Camera.handle_to_camera.
        """
        for cam in self.cameras:
            self.cameras.remove(cam)

        num_cameras = c_long()
        sdk.GetAvailableCameras(num_cameras)

        for i in range(num_cameras.value):
            handle = c_long()
            sdk.GetCameraHandle(i, handle)
            self.cameras.append(Camera(handle))
            self.handle_to_camera.update({handle.value: i})


class SingleCameraServer(Process):
    """A process to serve a single Camera object over Pyro."""
    def __init__(self, index, serial_to_host, serial_to_port):
        super(SingleCameraServer, self).__init__()
        # Camera index.
        self.index = index
        # Mapping of camera serial number to host.
        self.serial_to_host = serial_to_host
        # Mapping of camera serial number to port.
        self.serial_to_port = serial_to_port
        # Shared object that indicates we should continue running.
        self.shared_run_flag = Value('b', True)
        # The camera object.
        self.cam = None
        # A thread to run the Pyro daemon.
        self.pyro_thread = None


    def run(self):
        serial = None
        num_cameras = c_long()
        handle = c_long()

        sdk.GetAvailableCameras(num_cameras)
        if self.index >= num_cameras.value:
            raise Exception(
                "Camera index %d too large: I only have %d cameras."
                % (self.index, num_cameras.value))

        sdk.GetCameraHandle(self.index, handle)

        # SetCurrentCamera once, and create Camera with singleton=True:
        # this is the only camera in this process, so we don't need to
        # SetCurrentCamera and lock for each Camera method.
        sdk.SetCurrentCamera(handle)

        self.cam = Camera(handle, singleton=True)
        init_success = False
        retry_delay = 5
        while not init_success:
            try:
                self.cam.Initialize('')
            except:
                msgstr = 'Camera failed to initialize.'
                msgstr += ' Retrying in %ds.\n' % retry_delay
                sys.stdout.write(msgstr)
                time.sleep(retry_delay)
            else:
                init_success = True

        serial = self.cam.get_camera_serial_number()
        self.cam.logger.open(serial)

        if not self.serial_to_host.has_key(serial):
            raise Exception("No host found for camera with serial number %s."
                                % serial)

        if not self.serial_to_port.has_key(serial):
            raise Exception("No host found for camera with serial number %s."
                                % serial)

        host = self.serial_to_host[serial]
        port = self.serial_to_port[serial]

        daemon = Pyro4.Daemon(port=port, host=host)

        self.pyro_thread = threading.Thread(
            target=Pyro4.Daemon.serveSimple,
            args=({self.cam: 'pyroCam'},),
            kwargs={'daemon':daemon, 'ns':False})
        self.pyro_thread.start()

        while self.shared_run_flag.value:
            time.sleep(1)

        daemon.Shutdown()

        if hasattr(self.cam, 'data_thread'):
            data_thread.stop()
            data_thread.join()

        self.cam.Shutdown()
        self.cam.logger.close()
        deamon_thread.join()

    def stop(self):
        self.shared_run_flag.value = False


class Server(object):
    def __init__(self):
        self.serial_to_host = {}
        self.serial_to_port = {}
        self.cam_processes = []
        self.run_flag = True


    def run(self):
        for label, cam in CAMERAS.iteritems():
            self.serial_to_host.update({cam['serial']: cam['ipAddress']})
            self.serial_to_port.update({cam['serial']: cam['port']})

        self.cam_preocesses = []

        for i in range(len(self.serial_to_host)):
            self.cam_processes.append(SingleCameraServer(i, 
                                                       self.serial_to_host, 
                                                       self.serial_to_port))
            self.cam_processes[i].start()

        while self.run_flag:
            time.sleep(1)


    def stop(self):
        for proc in self.cam_processes:
            proc.stop()
            proc.join()
            del(proc)
        self.run_flag = 0
 

def main():
    s = Server()
    s.run()


if __name__ == '__main__':
    main()
