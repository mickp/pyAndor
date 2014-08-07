import ctypes
from ctypes import byref, c_long, d_float, c_double, c_int
import sys

dll = ctypes.WinDLL("atmcd64d.dll")

class AndorCaps(ctypes.Structure):
    _fields_ = [("ulSize", ctypes.c_ulong),
                ("ulAcqModes", ctypes.c_ulong),
                ("ulReadModes", ctypes.c_ulong),
                ("ulTriggerModes", ctypes.c_ulong),
                ("ulCameraType", ctypes.c_ulong),
                ("ulPixelMode", ctypes.c_ulong),
                ("ulSetFunctions", ctypes.c_ulong),
                ("ulGetFunctions", ctypes.c_ulong),
                ("ulFeatures", ctypes.c_ulong),
                ("ulPCICard", ctypes.c_ulong),
                ("ulEMGainCapability", ctypes.c_ulong),
                ("ulFTReadModes", ctypes.c_ulong),]

    def __init__(self):
        self.ulSize = sys.getsizeof(self)

caps = AndorCaps()
dll.GetCapabilities(byref(caps))
for field in caps._fields_:
    print "%s: \t%s" % (field[0].ljust(12), caps.__getattribute__(field[0]))

dll.Initialize('')
dll.GetDetector()
dll.GetHardwareVersion()
dll.SetAcquisitionMode(c_int(1))
dll.SetReadoutMode()
dll.SetShutter()
dll.SetTriggerMode(c_int(0))
dll.SetExposureTime(c_float(0.1))

# set exposure time