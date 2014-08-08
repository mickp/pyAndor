import os.path, re, sys, glob
import ctypes
import ctypes.util
from ctypes import c_int, c_uint, c_long, c_ulong
from ctypes import c_longlong, c_ulonglong
from ctypes import Structure

ULONG = c_ulong

"""Version Information Definitions"""
## Version infomration enumeration
class AT_VersionInFold(int): pass
AT_SDKVersion = AT_VersionInFold(0x40000000)
AT_DeviceDriverVersion = AT_VersionInFold(0x40000001)

# No. of elements in version info.
AT_NoOfVersionInfoIds = 2
# Minimum recommended length of the Version Info buffer parameter
AT_VERSION_INFO_LEN = 80
# Minimum recommended length of the Controller Card Model buffer parameter
AT_CONTROLLER_CARD_MODEL_LEN = 80

"""DDG Lite Definitions"""
## Channel enumeration
class AT_DDGLiteChannelId(int): pass
AT_DDGLite_ChannelA = AT_DDGLiteChannelId(0x40000000)
AT_DDGLite_ChannelB = AT_DDGLiteChannelId(0x40000001)
AT_DDGLite_ChannelC = AT_DDGLiteChannelId(0x40000002)

## Control byte flags
AT_DDGLite_ControlBit_GlobalEnable   = 0x01

AT_DDGLite_ControlBit_ChannelEnable  = 0x01
AT_DDGLite_ControlBit_FreeRun        = 0x02
AT_DDGLite_ControlBit_DisableOnFrame = 0x04
AT_DDGLite_ControlBit_RestartOnFire  = 0x08
AT_DDGLite_ControlBit_Invert         = 0x10
AT_DDGLite_ControlBit_EnableOnFire   = 0x20

"""USB iStar Definitions"""
AT_DDG_POLARITY_POSITIVE  = 0
AT_DDG_POLARITY_NEGATIVE  = 1
AT_DDG_TERMINATION_50OHMS = 0
AT_DDG_TERMINATION_HIGHZ  = 1

AT_STEPMODE_CONSTANT      = 0
AT_STEPMODE_EXPONENTIAL   = 1
AT_STEPMODE_LOGARITHMIC   = 2
AT_STEPMODE_LINEAR        = 3
AT_STEPMODE_OFF           = 100

AT_GATEMODE_FIRE_AND_GATE = 0
AT_GATEMODE_FIRE_ONLY     = 1
AT_GATEMODE_GATE_ONLY     = 2
AT_GATEMODE_CW_ON         = 3
AT_GATEMODE_CW_OFF        = 4
AT_GATEMODE_DDG           = 5


"""typedef structs"""
class ANDORCAPS(Structure):
    _fields_ = [
                ("ulSize", ctypes.c_ulong),
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
                ("ulFTReadModes", ctypes.c_ulong),
                ]


    def __init__(self):
        # The function that uses this strcut requires that ulSize contains
        # the size of the structure.
        self.ulSize = sys.getsizeof(self)

AndorCapabilities = ANDORCAPS


class COLORDEMOSAICINFO(Structure):
    _fields_ = [
        ('iX', c_int),
        ('iY', c_int),
        ('iAlgorithm', c_int),
        ('iXPhase', c_int),
        ('iYPhase', c_int),
        ('iBackground', c_int),
        ]
ColorDemosaicInfo = COLORDEMOSAICINFO


class WHITEBALANCEINFO(Structure):
    _fields_ = [
        ('iSize', c_int),
        ('iX', c_int),
        ('iY', c_int),
        ('iAlgorithm', c_int),
        ('iROI_left', c_int),
        ('iROI_right', c_int),
        ('iROI_top', c_int),
        ('iROI_bottom', c_int),
        ('iOperation', c_int),
        ]

WhiteBalanceInfo = WHITEBALANCEINFO

at_32 = c_long
at_u32 = c_ulong
at_64 = c_longlong
at_u64 = c_ulonglong


"""Status codes"""
DRV_ERROR_CODES = 20001
DRV_SUCCESS = 20002
DRV_VXDNOTINSTALLED = 20003
DRV_ERROR_SCAN = 20004
DRV_ERROR_CHECK_SUM = 20005
DRV_ERROR_FILELOAD = 20006
DRV_UNKNOWN_FUNCTION = 20007
DRV_ERROR_VXD_INIT = 20008
DRV_ERROR_ADDRESS = 20009
DRV_ERROR_PAGELOCK = 20010
DRV_ERROR_PAGEUNLOCK = 20011
DRV_ERROR_BOARDTEST = 20012
DRV_ERROR_ACK = 20013
DRV_ERROR_UP_FIFO = 20014
DRV_ERROR_PATTERN = 20015
DRV_ACQUISITION_ERRORS = 20017
DRV_ACQ_BUFFER = 20018
DRV_ACQ_DOWNFIFO_FULL = 20019
DRV_PROC_UNKONWN_INSTRUCTION = 20020
DRV_ILLEGAL_OP_CODE = 20021
DRV_KINETIC_TIME_NOT_MET = 20022
DRV_ACCUM_TIME_NOT_MET = 20023
DRV_NO_NEW_DATA = 20024
DRV_PCI_DMA_FAIL = 20025
DRV_SPOOLERROR = 20026
DRV_SPOOLSETUPERROR = 20027
DRV_FILESIZELIMITERROR = 20028
DRV_ERROR_FILESAVE = 20029
DRV_TEMPERATURE_CODES = 20033
DRV_TEMPERATURE_OFF = 20034
DRV_TEMPERATURE_NOT_STABILIZED = 20035
DRV_TEMPERATURE_STABILIZED = 20036
DRV_TEMPERATURE_NOT_REACHED = 20037
DRV_TEMPERATURE_OUT_RANGE = 20038
DRV_TEMPERATURE_NOT_SUPPORTED = 20039
DRV_TEMPERATURE_DRIFT = 20040
DRV_TEMP_CODES = 20033
DRV_TEMP_OFF = 20034
DRV_TEMP_NOT_STABILIZED = 20035
DRV_TEMP_STABILIZED = 20036
DRV_TEMP_NOT_REACHED = 20037
DRV_TEMP_OUT_RANGE = 20038
DRV_TEMP_NOT_SUPPORTED = 20039
DRV_TEMP_DRIFT = 20040
DRV_GENERAL_ERRORS = 20049
DRV_INVALID_AUX = 20050
DRV_COF_NOTLOADED = 20051
DRV_FPGAPROG = 20052
DRV_FLEXERROR = 20053
DRV_GPIBERROR = 20054
DRV_EEPROMVERSIONERROR = 20055
DRV_DATATYPE = 20064
DRV_DRIVER_ERRORS = 20065
DRV_P1INVALID = 20066
DRV_P2INVALID = 20067
DRV_P3INVALID = 20068
DRV_P4INVALID = 20069
DRV_INIERROR = 20070
DRV_COFERROR = 20071
DRV_ACQUIRING = 20072
DRV_IDLE = 20073
DRV_TEMPCYCLE = 20074
DRV_NOT_INITIALIZED = 20075
DRV_P5INVALID = 20076
DRV_P6INVALID = 20077
DRV_INVALID_MODE = 20078
DRV_INVALID_FILTER = 20079
DRV_I2CERRORS = 20080
DRV_I2CDEVNOTFOUND = 20081
DRV_I2CTIMEOUT = 20082
DRV_P7INVALID = 20083
DRV_P8INVALID = 20084
DRV_P9INVALID = 20085
DRV_P10INVALID = 20086
DRV_P11INVALID = 20087
DRV_USBERROR = 20089
DRV_IOCERROR = 20090
DRV_VRMVERSIONERROR = 20091
DRV_GATESTEPERROR = 20092
DRV_USB_INTERRUPT_ENDPOINT_ERROR = 20093
DRV_RANDOM_TRACK_ERROR = 20094
DRV_INVALID_TRIGGER_MODE = 20095
DRV_LOAD_FIRMWARE_ERROR = 20096
DRV_DIVIDE_BY_ZERO_ERROR = 20097
DRV_INVALID_RINGEXPOSURES = 20098
DRV_BINNING_ERROR = 20099
DRV_INVALID_AMPLIFIER = 20100
DRV_INVALID_COUNTCONVERT_MODE = 20101
DRV_ERROR_NOCAMERA = 20990
DRV_NOT_SUPPORTED = 20991
DRV_NOT_AVAILABLE = 20992
DRV_ERROR_MAP = 20115
DRV_ERROR_UNMAP = 20116
DRV_ERROR_MDL = 20117
DRV_ERROR_UNMDL = 20118
DRV_ERROR_BUFFSIZE = 20119
DRV_ERROR_NOHANDLE = 20121
DRV_GATING_NOT_AVAILABLE = 20130
DRV_FPGA_VOLTAGE_ERROR = 20131
DRV_OW_CMD_FAIL = 20150
DRV_OWMEMORY_BAD_ADDR = 20151
DRV_OWCMD_NOT_AVAILABLE = 20152
DRV_OW_NO_SLAVES = 20153
DRV_OW_NOT_INITIALIZED = 20154
DRV_OW_ERROR_SLAVE_NUM = 20155
DRV_MSTIMINGS_ERROR = 20156
DRV_OA_NULL_ERROR = 20173
DRV_OA_PARSE_DTD_ERROR = 20174
DRV_OA_DTD_VALIDATE_ERROR = 20175
DRV_OA_FILE_ACCESS_ERROR = 20176
DRV_OA_FILE_DOES_NOT_EXIST = 20177
DRV_OA_XML_INVALID_OR_NOT_FOUND_ERROR = 20178
DRV_OA_PRESET_FILE_NOT_LOADED = 20179
DRV_OA_USER_FILE_NOT_LOADED = 20180
DRV_OA_PRESET_AND_USER_FILE_NOT_LOADED = 20181
DRV_OA_INVALID_FILE = 20182
DRV_OA_FILE_HAS_BEEN_MODIFIED = 20183
DRV_OA_BUFFER_FULL = 20184
DRV_OA_INVALID_STRING_LENGTH = 20185
DRV_OA_INVALID_CHARS_IN_NAME = 20186
DRV_OA_INVALID_NAMING = 20187
DRV_OA_GET_CAMERA_ERROR = 20188
DRV_OA_MODE_ALREADY_EXISTS = 20189
DRV_OA_STRINGS_NOT_EQUAL = 20190
DRV_OA_NO_USER_DATA = 20191
DRV_OA_VALUE_NOT_SUPPORTED = 20192
DRV_OA_MODE_DOES_NOT_EXIST = 20193
DRV_OA_CAMERA_NOT_SUPPORTED = 20194
DRV_OA_FAILED_TO_GET_MODE = 20195
DRV_PROCESSING_FAILED = 20211

AC_ACQMODE_SINGLE = 1
AC_ACQMODE_VIDEO = 2
AC_ACQMODE_ACCUMULATE = 4
AC_ACQMODE_KINETIC = 8
AC_ACQMODE_FRAMETRANSFER = 16
AC_ACQMODE_FASTKINETICS = 32
AC_ACQMODE_OVERLAP = 64
AC_READMODE_FULLIMAGE = 1
AC_READMODE_SUBIMAGE = 2
AC_READMODE_SINGLETRACK = 4
AC_READMODE_FVB = 8
AC_READMODE_MULTITRACK = 16
AC_READMODE_RANDOMTRACK = 32
AC_READMODE_MULTITRACKSCAN = 64
AC_TRIGGERMODE_INTERNAL = 1
AC_TRIGGERMODE_EXTERNAL = 2
AC_TRIGGERMODE_EXTERNAL_FVB_EM = 4
AC_TRIGGERMODE_CONTINUOUS = 8
AC_TRIGGERMODE_EXTERNALSTART = 16
AC_TRIGGERMODE_EXTERNALEXPOSURE = 32
AC_TRIGGERMODE_INVERTED = 64
AC_TRIGGERMODE_EXTERNAL_CHARGESHIFTING = 128
AC_TRIGGERMODE_BULB = 32
AC_CAMERATYPE_PDA = 0
AC_CAMERATYPE_IXON = 1
AC_CAMERATYPE_ICCD = 2
AC_CAMERATYPE_EMCCD = 3
AC_CAMERATYPE_CCD = 4
AC_CAMERATYPE_ISTAR = 5
AC_CAMERATYPE_VIDEO = 6
AC_CAMERATYPE_IDUS = 7
AC_CAMERATYPE_NEWTON = 8
AC_CAMERATYPE_SURCAM = 9
AC_CAMERATYPE_USBICCD = 10
AC_CAMERATYPE_LUCA = 11
AC_CAMERATYPE_RESERVED = 12
AC_CAMERATYPE_IKON = 13
AC_CAMERATYPE_INGAAS = 14
AC_CAMERATYPE_IVAC = 15
AC_CAMERATYPE_UNPROGRAMMED = 16
AC_CAMERATYPE_CLARA = 17
AC_CAMERATYPE_USBISTAR = 18
AC_CAMERATYPE_SIMCAM = 19
AC_CAMERATYPE_NEO = 20
AC_CAMERATYPE_IXONULTRA = 21
AC_CAMERATYPE_VOLMOS = 22
AC_PIXELMODE_8BIT = 1
AC_PIXELMODE_14BIT = 2
AC_PIXELMODE_16BIT = 4
AC_PIXELMODE_32BIT = 8

AC_PIXELMODE_MONO = 0x000000
AC_PIXELMODE_RGB  = 0x010000
AC_PIXELMODE_CMY  = 0x020000

AC_SETFUNCTION_VREADOUT = 0x01
AC_SETFUNCTION_HREADOUT = 0x02
AC_SETFUNCTION_TEMPERATURE = 0x04
AC_SETFUNCTION_MCPGAIN = 0x08
AC_SETFUNCTION_EMCCDGAIN = 0x10
AC_SETFUNCTION_BASELINECLAMP = 0x20
AC_SETFUNCTION_VSAMPLITUDE = 0x40
AC_SETFUNCTION_HIGHCAPACITY = 0x80
AC_SETFUNCTION_BASELINEOFFSET = 0x0100
AC_SETFUNCTION_PREAMPGAIN = 0x0200
AC_SETFUNCTION_CROPMODE = 0x0400
AC_SETFUNCTION_DMAPARAMETERS = 0x0800
AC_SETFUNCTION_HORIZONTALBIN = 0x1000
AC_SETFUNCTION_MULTITRACKHRANGE = 0x2000
AC_SETFUNCTION_RANDOMTRACKNOGAPS = 0x4000
AC_SETFUNCTION_EMADVANCED = 0x8000
AC_SETFUNCTION_GATEMODE = 0x010000
AC_SETFUNCTION_DDGTIMES = 0x020000
AC_SETFUNCTION_IOC = 0x040000
AC_SETFUNCTION_INTELLIGATE = 0x080000
AC_SETFUNCTION_INSERTION_DELAY = 0x100000
AC_SETFUNCTION_GATESTEP = 0x200000
AC_SETFUNCTION_TRIGGERTERMINATION = 0x400000
AC_SETFUNCTION_EXTENDEDNIR = 0x800000
AC_SETFUNCTION_SPOOLTHREADCOUNT = 0x1000000

# Deprecated for AC_SETFUNCTION_MCPGAIN
AC_SETFUNCTION_GAIN = 8
AC_SETFUNCTION_ICCDGAIN = 8

AC_GETFUNCTION_TEMPERATURE = 0x01
AC_GETFUNCTION_TARGETTEMPERATURE = 0x02
AC_GETFUNCTION_TEMPERATURERANGE = 0x04
AC_GETFUNCTION_DETECTORSIZE = 0x08
AC_GETFUNCTION_MCPGAIN = 0x10
AC_GETFUNCTION_EMCCDGAIN = 0x20
AC_GETFUNCTION_HVFLAG = 0x40
AC_GETFUNCTION_GATEMODE = 0x80
AC_GETFUNCTION_DDGTIMES = 0x0100
AC_GETFUNCTION_IOC = 0x0200
AC_GETFUNCTION_INTELLIGATE = 0x0400
AC_GETFUNCTION_INSERTION_DELAY = 0x0800
AC_GETFUNCTION_GATESTEP = 0x1000
AC_GETFUNCTION_PHOSPHORSTATUS = 0x2000
AC_GETFUNCTION_MCPGAINTABLE = 0x4000
AC_GETFUNCTION_BASELINECLAMP = 0x8000

# Deprecated for AC_GETFUNCTION_MCPGAIN
AC_GETFUNCTION_GAIN = 0x10
AC_GETFUNCTION_ICCDGAIN = 0x10

AC_FEATURES_POLLING = 1
AC_FEATURES_EVENTS = 2
AC_FEATURES_SPOOLING = 4
AC_FEATURES_SHUTTER = 8
AC_FEATURES_SHUTTEREX = 16
AC_FEATURES_EXTERNAL_I2C = 32
AC_FEATURES_SATURATIONEVENT = 64
AC_FEATURES_FANCONTROL = 128
AC_FEATURES_MIDFANCONTROL = 256
AC_FEATURES_TEMPERATUREDURINGACQUISITION = 512
AC_FEATURES_KEEPCLEANCONTROL = 1024
AC_FEATURES_DDGLITE = 0x0800
AC_FEATURES_FTEXTERNALEXPOSURE = 0x1000
AC_FEATURES_KINETICEXTERNALEXPOSURE = 0x2000
AC_FEATURES_DACCONTROL = 0x4000
AC_FEATURES_METADATA = 0x8000
AC_FEATURES_IOCONTROL = 0x10000
AC_FEATURES_PHOTONCOUNTING = 0x20000
AC_FEATURES_COUNTCONVERT = 0x40000
AC_FEATURES_DUALMODE = 0x80000
AC_FEATURES_OPTACQUIRE = 0x100000
AC_FEATURES_REALTIMESPURIOUSNOISEFILTER = 0x200000
AC_FEATURES_POSTPROCESSSPURIOUSNOISEFILTER = 0x400000
AC_FEATURES_DUALPREAMPGAIN = 0x800000
AC_FEATURES_DEFECT_CORRECTION = 0x1000000
AC_FEATURES_STARTOFEXPOSURE_EVENT = 0x2000000
AC_FEATURES_ENDOFEXPOSURE_EVENT = 0x4000000
AC_FEATURES_CAMERALINK = 0x80000007108864

AC_EMGAIN_8BIT = 1
AC_EMGAIN_12BIT = 2
AC_EMGAIN_LINEAR12 = 4
AC_EMGAIN_REAL12 = 8

"""Functions

Just export the functions - the calling code needs to ensure that the correct
types are passed.  We could just export _dll and call _dll.func, but removing
the _dll reduces the calling overhead."""

#AbortAcquisition(void)
AbortAcquisition = _dll.AbortAcquisition

#CancelWait(void)
CancelWait = _dll.CancelWait

#CoolerOFF(void)
CoolerOFF = _dll.CoolerOFF

#CoolerON(void)
CoolerON = _dll.CoolerON

#DemosaicImage(WORD * grey, WORD * red, WORD * green, WORD * blue, ColorDemosaicInfo * info)
DemosaicImage = _dll.DemosaicImage

#EnableKeepCleans(int iMode)
EnableKeepCleans = _dll.EnableKeepCleans

#FreeInternalMemory(void)
FreeInternalMemory = _dll.FreeInternalMemory

#GetAcquiredData(at_32 * arr, unsigned long size)
GetAcquiredData = _dll.GetAcquiredData

#GetAcquiredData16(WORD * arr, unsigned long size)
GetAcquiredData16 = _dll.GetAcquiredData16

#GetAcquiredFloatData(float * arr, unsigned long size)
GetAcquiredFloatData = _dll.GetAcquiredFloatData

#GetAcquisitionProgress(long * acc, long * series)
GetAcquisitionProgress = _dll.GetAcquisitionProgress

#GetAcquisitionTimings(float * exposure, float * accumulate, float * kinetic)
GetAcquisitionTimings = _dll.GetAcquisitionTimings

#GetAdjustedRingExposureTimes(int inumTimes, float * fptimes)
GetAdjustedRingExposureTimes = _dll.GetAdjustedRingExposureTimes

#GetAllDMAData(at_32 * arr, unsigned long size)
GetAllDMAData = _dll.GetAllDMAData

#GetAmpDesc(int index, char * name, int length)
GetAmpDesc = _dll.GetAmpDesc

#GetAmpMaxSpeed(int index, float * speed)
GetAmpMaxSpeed = _dll.GetAmpMaxSpeed

#GetAvailableCameras(long * totalCameras)
GetAvailableCameras = _dll.GetAvailableCameras

#GetBackground(at_32 * arr, unsigned long size)
GetBackground = _dll.GetBackground

#GetBaselineClamp(int * state)
GetBaselineClamp = _dll.GetBaselineClamp

#GetBitDepth(int channel, int * depth)
GetBitDepth = _dll.GetBitDepth

#GetCameraEventStatus(DWORD * camStatus)
GetCameraEventStatus = _dll.GetCameraEventStatus

#GetCameraHandle(long cameraIndex, long * cameraHandle)
GetCameraHandle = _dll.GetCameraHandle

#GetCameraInformation(int index, long * information)
GetCameraInformation = _dll.GetCameraInformation

#GetCameraSerialNumber(int * number)
GetCameraSerialNumber = _dll.GetCameraSerialNumber

#GetCapabilities(AndorCapabilities * caps)
GetCapabilities = _dll.GetCapabilities

#GetControllerCardModel(char * controllerCardModel)
GetControllerCardModel = _dll.GetControllerCardModel

#GetCountConvertWavelengthRange(float * minval, float * maxval)
GetCountConvertWavelengthRange = _dll.GetCountConvertWavelengthRange

#GetCurrentCamera(long * cameraHandle)
GetCurrentCamera = _dll.GetCurrentCamera

#GetCYMGShift(int * iXshift, int * iYShift)
GetCYMGShift = _dll.GetCYMGShift

#GetDDGExternalOutputEnabled(at_u32 uiIndex, at_u32 * puiEnabled)
GetDDGExternalOutputEnabled = _dll.GetDDGExternalOutputEnabled

#GetDDGExternalOutputPolarity(at_u32 uiIndex, at_u32 * puiPolarity)
GetDDGExternalOutputPolarity = _dll.GetDDGExternalOutputPolarity

#GetDDGExternalOutputStepEnabled(at_u32 uiIndex, at_u32 * puiEnabled)
GetDDGExternalOutputStepEnabled = _dll.GetDDGExternalOutputStepEnabled

#GetDDGExternalOutputTime(at_u32 uiIndex, at_u64 * puiDelay, at_u64 * puiWidth)
GetDDGExternalOutputTime = _dll.GetDDGExternalOutputTime

#GetDDGTTLGateWidth(at_u64 opticalWidth, at_u64 * ttlWidth)
GetDDGTTLGateWidth = _dll.GetDDGTTLGateWidth

#GetDDGGateTime(at_u64 * puiDelay, at_u64 * puiWidth)
GetDDGGateTime = _dll.GetDDGGateTime

#GetDDGInsertionDelay(int * piState)
GetDDGInsertionDelay = _dll.GetDDGInsertionDelay

#GetDDGIntelligate(int * piState)
GetDDGIntelligate = _dll.GetDDGIntelligate

#GetDDGIOC(int * state)
GetDDGIOC = _dll.GetDDGIOC

#GetDDGIOCFrequency(double * frequency)
GetDDGIOCFrequency = _dll.GetDDGIOCFrequency

#GetDDGIOCNumber(unsigned long * numberPulses)
GetDDGIOCNumber = _dll.GetDDGIOCNumber

#GetDDGIOCNumberRequested(at_u32 * pulses)
GetDDGIOCNumberRequested = _dll.GetDDGIOCNumberRequested

#GetDDGIOCPeriod(at_u64 * period)
GetDDGIOCPeriod = _dll.GetDDGIOCPeriod

#GetDDGIOCPulses(int * pulses)
GetDDGIOCPulses = _dll.GetDDGIOCPulses

#GetDDGIOCTrigger(at_u32 * trigger)
GetDDGIOCTrigger = _dll.GetDDGIOCTrigger

#GetDDGOpticalWidthEnabled(at_u32 * puiEnabled)
GetDDGOpticalWidthEnabled = _dll.GetDDGOpticalWidthEnabled

#GetDDGLiteGlobalControlByte(unsigned char * control)
GetDDGLiteGlobalControlByte = _dll.GetDDGLiteGlobalControlByte

#GetDDGLiteControlByte(AT_DDGLiteChannelId channel, unsigned char * control)
GetDDGLiteControlByte = _dll.GetDDGLiteControlByte

#GetDDGLiteInitialDelay(AT_DDGLiteChannelId channel, float * fDelay)
GetDDGLiteInitialDelay = _dll.GetDDGLiteInitialDelay

#GetDDGLitePulseWidth(AT_DDGLiteChannelId channel, float * fWidth)
GetDDGLitePulseWidth = _dll.GetDDGLitePulseWidth

#GetDDGLiteInterPulseDelay(AT_DDGLiteChannelId channel, float * fDelay)
GetDDGLiteInterPulseDelay = _dll.GetDDGLiteInterPulseDelay

#GetDDGLitePulsesPerExposure(AT_DDGLiteChannelId channel, at_u32 * ui32Pulses)
GetDDGLitePulsesPerExposure = _dll.GetDDGLitePulsesPerExposure

#GetDDGPulse(double wid, double resolution, double * Delay, double * Width)
GetDDGPulse = _dll.GetDDGPulse

#GetDDGStepCoefficients(at_u32 mode, double * p1, double * p2)
GetDDGStepCoefficients = _dll.GetDDGStepCoefficients

#GetDDGStepMode(at_u32 * mode)
GetDDGStepMode = _dll.GetDDGStepMode

#GetDetector(int * xpixels, int * ypixels)
GetDetector = _dll.GetDetector

#GetDICameraInfo(void * info)
GetDICameraInfo = _dll.GetDICameraInfo

#GetEMAdvanced(int * state)
GetEMAdvanced = _dll.GetEMAdvanced

#GetEMCCDGain(int * gain)
GetEMCCDGain = _dll.GetEMCCDGain

#GetEMGainRange(int * low, int * high)
GetEMGainRange = _dll.GetEMGainRange

#GetExternalTriggerTermination(at_u32 * puiTermination)
GetExternalTriggerTermination = _dll.GetExternalTriggerTermination

#GetFastestRecommendedVSSpeed(int * index, float * speed)
GetFastestRecommendedVSSpeed = _dll.GetFastestRecommendedVSSpeed

#GetFIFOUsage(int * FIFOusage)
GetFIFOUsage = _dll.GetFIFOUsage

#GetFilterMode(int * mode)
GetFilterMode = _dll.GetFilterMode

#GetFKExposureTime(float * time)
GetFKExposureTime = _dll.GetFKExposureTime

#GetFKVShiftSpeed(int index, int * speed)
GetFKVShiftSpeed = _dll.GetFKVShiftSpeed

#GetFKVShiftSpeedF(int index, float * speed)
GetFKVShiftSpeedF = _dll.GetFKVShiftSpeedF

#GetFrontEndStatus(int * piFlag)
GetFrontEndStatus = _dll.GetFrontEndStatus

#GetGateMode(int * piGatemode)
GetGateMode = _dll.GetGateMode

#GetHardwareVersion(unsigned int * PCB, unsigned int * Decode, unsigned int * dummy1, unsigned int * dummy2, unsigned int * CameraFirmwareVersion, unsigned int * CameraFirmwareBuild)
GetHardwareVersion = _dll.GetHardwareVersion

#GetHeadModel(char * name)
GetHeadModel = _dll.GetHeadModel

#GetHorizontalSpeed(int index, int * speed)
GetHorizontalSpeed = _dll.GetHorizontalSpeed

#GetHSSpeed(int channel, int typ, int index, float * speed)
GetHSSpeed = _dll.GetHSSpeed

#GetHVflag(int * bFlag)
GetHVflag = _dll.GetHVflag

#GetID(int devNum, int * id)
GetID = _dll.GetID

#GetImageFlip(int * iHFlip, int * iVFlip)
GetImageFlip = _dll.GetImageFlip

#GetImageRotate(int * iRotate)
GetImageRotate = _dll.GetImageRotate

#GetImages(long first, long last, at_32 * arr, unsigned long size, long * validfirst, long * validlast)
GetImages = _dll.GetImages

#GetImages16(long first, long last, WORD * arr, unsigned long size, long * validfirst, long * validlast)
GetImages16 = _dll.GetImages16

#GetImagesPerDMA(unsigned long * images)
GetImagesPerDMA = _dll.GetImagesPerDMA

#GetIRQ(int * IRQ)
GetIRQ = _dll.GetIRQ

#GetKeepCleanTime(float * KeepCleanTime)
GetKeepCleanTime = _dll.GetKeepCleanTime

#GetMaximumBinning(int ReadMode, int HorzVert, int * MaxBinning)
GetMaximumBinning = _dll.GetMaximumBinning

#GetMaximumExposure(float * MaxExp)
GetMaximumExposure = _dll.GetMaximumExposure

#GetMCPGain(int * piGain)
GetMCPGain = _dll.GetMCPGain

#GetMCPGainRange(int * iLow, int * iHigh)
GetMCPGainRange = _dll.GetMCPGainRange

#GetMCPGainTable(int iNum, int * piGain, float * pfPhotoepc)
GetMCPGainTable = _dll.GetMCPGainTable

#GetMCPVoltage(int * iVoltage)
GetMCPVoltage = _dll.GetMCPVoltage

#GetMinimumImageLength(int * MinImageLength)
GetMinimumImageLength = _dll.GetMinimumImageLength

#GetMinimumNumberInSeries(int * number)
GetMinimumNumberInSeries = _dll.GetMinimumNumberInSeries

#GetMostRecentColorImage16(unsigned long size, int algorithm, WORD * red, WORD * green, WORD * blue)
GetMostRecentColorImage16 = _dll.GetMostRecentColorImage16

#GetMostRecentImage(at_32 * arr, unsigned long size)
GetMostRecentImage = _dll.GetMostRecentImage

#GetMostRecentImage16(WORD * arr, unsigned long size)
GetMostRecentImage16 = _dll.GetMostRecentImage16

#GetMSTimingsData(SYSTEMTIME * TimeOfStart, float * pfDifferences, int inoOfImages)
GetMSTimingsData = _dll.GetMSTimingsData

#GetMetaDataInfo(SYSTEMTIME * TimeOfStart, float * pfTimeFromStart, unsigned int index)
GetMetaDataInfo = _dll.GetMetaDataInfo

#GetMSTimingsEnabled(void)
GetMSTimingsEnabled = _dll.GetMSTimingsEnabled

#GetNewData(at_32 * arr, unsigned long size)
GetNewData = _dll.GetNewData

#GetNewData16(WORD * arr, unsigned long size)
GetNewData16 = _dll.GetNewData16

#GetNewData8(unsigned char * arr, unsigned long size)
GetNewData8 = _dll.GetNewData8

#GetNewFloatData(float * arr, unsigned long size)
GetNewFloatData = _dll.GetNewFloatData

#GetNumberADChannels(int * channels)
GetNumberADChannels = _dll.GetNumberADChannels

#GetNumberAmp(int * amp)
GetNumberAmp = _dll.GetNumberAmp

#GetNumberAvailableImages(at_32 * first, at_32 * last)
GetNumberAvailableImages = _dll.GetNumberAvailableImages

#GetNumberDDGExternalOutputs(at_u32 * puiCount)
GetNumberDDGExternalOutputs = _dll.GetNumberDDGExternalOutputs

#GetNumberDevices(int * numDevs)
GetNumberDevices = _dll.GetNumberDevices

#GetNumberFKVShiftSpeeds(int * number)
GetNumberFKVShiftSpeeds = _dll.GetNumberFKVShiftSpeeds

#GetNumberHorizontalSpeeds(int * number)
GetNumberHorizontalSpeeds = _dll.GetNumberHorizontalSpeeds

#GetNumberHSSpeeds(int channel, int typ, int * speeds)
GetNumberHSSpeeds = _dll.GetNumberHSSpeeds

#GetNumberNewImages(long * first, long * last)
GetNumberNewImages = _dll.GetNumberNewImages

#GetNumberPhotonCountingDivisions(at_u32 * noOfDivisions)
GetNumberPhotonCountingDivisions = _dll.GetNumberPhotonCountingDivisions

#GetNumberPreAmpGains(int * noGains)
GetNumberPreAmpGains = _dll.GetNumberPreAmpGains

#GetNumberRingExposureTimes(int * ipnumTimes)
GetNumberRingExposureTimes = _dll.GetNumberRingExposureTimes

#GetNumberIO(int * iNumber)
GetNumberIO = _dll.GetNumberIO

#GetNumberVerticalSpeeds(int * number)
GetNumberVerticalSpeeds = _dll.GetNumberVerticalSpeeds

#GetNumberVSAmplitudes(int * number)
GetNumberVSAmplitudes = _dll.GetNumberVSAmplitudes

#GetNumberVSSpeeds(int * speeds)
GetNumberVSSpeeds = _dll.GetNumberVSSpeeds

#GetOldestImage(at_32 * arr, unsigned long size)
GetOldestImage = _dll.GetOldestImage

#GetOldestImage16(WORD * arr, unsigned long size)
GetOldestImage16 = _dll.GetOldestImage16

#GetPhosphorStatus(int * piFlag)
GetPhosphorStatus = _dll.GetPhosphorStatus

#GetPhysicalDMAAddress(unsigned long * Address1, unsigned long * Address2)
GetPhysicalDMAAddress = _dll.GetPhysicalDMAAddress

#GetPixelSize(float * xSize, float * ySize)
GetPixelSize = _dll.GetPixelSize

#GetPreAmpGain(int index, float * gain)
GetPreAmpGain = _dll.GetPreAmpGain

#GetPreAmpGainText(int index, char * name, int length)
GetPreAmpGainText = _dll.GetPreAmpGainText

#GetDualExposureTimes(float * exposure1, float * exposure2)
GetDualExposureTimes = _dll.GetDualExposureTimes

#GetQE(char * sensor, float wavelength, unsigned int mode, float * QE)
GetQE = _dll.GetQE

#GetReadOutTime(float * ReadOutTime)
GetReadOutTime = _dll.GetReadOutTime

#GetRegisterDump(int * mode)
GetRegisterDump = _dll.GetRegisterDump

#GetRingExposureRange(float * fpMin, float * fpMax)
GetRingExposureRange = _dll.GetRingExposureRange

#GetSDK3Handle(int * Handle)
GetSDK3Handle = _dll.GetSDK3Handle

#GetSensitivity(int channel, int horzShift, int amplifier, int pa, float * sensitivity)
GetSensitivity = _dll.GetSensitivity

#GetShutterMinTimes(int * minclosingtime, int * minopeningtime)
GetShutterMinTimes = _dll.GetShutterMinTimes

#GetSizeOfCircularBuffer(long * index)
GetSizeOfCircularBuffer = _dll.GetSizeOfCircularBuffer

#GetSlotBusDeviceFunction(DWORD * dwslot, DWORD * dwBus, DWORD * dwDevice, DWORD * dwFunction)
GetSlotBusDeviceFunction = _dll.GetSlotBusDeviceFunction

#GetSoftwareVersion(unsigned int * eprom, unsigned int * coffile, unsigned int * vxdrev, unsigned int * vxdver, unsigned int * dllrev, unsigned int * dllver)
GetSoftwareVersion = _dll.GetSoftwareVersion

#GetSpoolProgress(long * index)
GetSpoolProgress = _dll.GetSpoolProgress

#GetStartUpTime(float * time)
GetStartUpTime = _dll.GetStartUpTime

#GetStatus(int * status)
GetStatus = _dll.GetStatus

#GetTECStatus(int * piFlag)
GetTECStatus = _dll.GetTECStatus

#GetTemperature(int * temperature)
GetTemperature = _dll.GetTemperature

#GetTemperatureF(float * temperature)
GetTemperatureF = _dll.GetTemperatureF

#GetTemperatureRange(int * mintemp, int * maxtemp)
GetTemperatureRange = _dll.GetTemperatureRange

#GetTemperatureStatus(float * SensorTemp, float * TargetTemp, float * AmbientTemp, float * CoolerVolts)
GetTemperatureStatus = _dll.GetTemperatureStatus

#GetTotalNumberImagesAcquired(long * index)
GetTotalNumberImagesAcquired = _dll.GetTotalNumberImagesAcquired

#GetIODirection(int index, int * iDirection)
GetIODirection = _dll.GetIODirection

#GetIOLevel(int index, int * iLevel)
GetIOLevel = _dll.GetIOLevel

#GetVersionInfo(AT_VersionInfoId arr, char * szVersionInfo, at_u32 ui32BufferLen)
GetVersionInfo = _dll.GetVersionInfo

#GetVerticalSpeed(int index, int * speed)
GetVerticalSpeed = _dll.GetVerticalSpeed

#GetVirtualDMAAddress(void ** Address1, void ** Address2)
GetVirtualDMAAddress = _dll.GetVirtualDMAAddress

#GetVSAmplitudeString(int index, char * text)
GetVSAmplitudeString = _dll.GetVSAmplitudeString

#GetVSAmplitudeFromString(char * text, int * index)
GetVSAmplitudeFromString = _dll.GetVSAmplitudeFromString

#GetVSAmplitudeValue(int index, int * value)
GetVSAmplitudeValue = _dll.GetVSAmplitudeValue

#GetVSSpeed(int index, float * speed)
GetVSSpeed = _dll.GetVSSpeed

#GPIBReceive(int id, short address, char * text, int size)
GPIBReceive = _dll.GPIBReceive

#GPIBSend(int id, short address, char * text)
GPIBSend = _dll.GPIBSend

#I2CBurstRead(BYTE i2cAddress, long nBytes, BYTE * data)
I2CBurstRead = _dll.I2CBurstRead

#I2CBurstWrite(BYTE i2cAddress, long nBytes, BYTE * data)
I2CBurstWrite = _dll.I2CBurstWrite

#I2CRead(BYTE deviceID, BYTE intAddress, BYTE * pdata)
I2CRead = _dll.I2CRead

#I2CReset(void)
I2CReset = _dll.I2CReset

#I2CWrite(BYTE deviceID, BYTE intAddress, BYTE data)
I2CWrite = _dll.I2CWrite

#IdAndorDll(void)
IdAndorDll = _dll.IdAndorDll

#InAuxPort(int port, int * state)
InAuxPort = _dll.InAuxPort

#Initialize(char * dir)
Initialize = _dll.Initialize

#InitializeDevice(char * dir)
InitializeDevice = _dll.InitializeDevice

#IsAmplifierAvailable(int iamp)
IsAmplifierAvailable = _dll.IsAmplifierAvailable

#IsCoolerOn(int * iCoolerStatus)
IsCoolerOn = _dll.IsCoolerOn

#IsCountConvertModeAvailable(int mode)
IsCountConvertModeAvailable = _dll.IsCountConvertModeAvailable

#IsInternalMechanicalShutter(int * InternalShutter)
IsInternalMechanicalShutter = _dll.IsInternalMechanicalShutter

#IsPreAmpGainAvailable(int channel, int amplifier, int index, int pa, int * status)
IsPreAmpGainAvailable = _dll.IsPreAmpGainAvailable

#IsTriggerModeAvailable(int iTriggerMode)
IsTriggerModeAvailable = _dll.IsTriggerModeAvailable

#Merge(const at_32 * arr, long nOrder, long nPoint, long nPixel, float * coeff, long fit, long hbin, at_32 * output, float * start, float * step_Renamed)
Merge = _dll.Merge

#OutAuxPort(int port, int state)
OutAuxPort = _dll.OutAuxPort

#PrepareAcquisition(void)
PrepareAcquisition = _dll.PrepareAcquisition

#SaveAsBmp(char * path, char * palette, long ymin, long ymax)
SaveAsBmp = _dll.SaveAsBmp

#SaveAsCommentedSif(char * path, char * comment)
SaveAsCommentedSif = _dll.SaveAsCommentedSif

#SaveAsEDF(char * szPath, int iMode)
SaveAsEDF = _dll.SaveAsEDF

#SaveAsFITS(char * szFileTitle, int typ)
SaveAsFITS = _dll.SaveAsFITS

#SaveAsRaw(char * szFileTitle, int typ)
SaveAsRaw = _dll.SaveAsRaw

#SaveAsSif(char * path)
SaveAsSif = _dll.SaveAsSif

#SaveAsSPC(char * path)
SaveAsSPC = _dll.SaveAsSPC

#SaveAsTiff(char * path, char * palette, int position, int typ)
SaveAsTiff = _dll.SaveAsTiff

#SaveAsTiffEx(char * path, char * palette, int position, int typ, int mode)
SaveAsTiffEx = _dll.SaveAsTiffEx

#SaveEEPROMToFile(char * cFileName)
SaveEEPROMToFile = _dll.SaveEEPROMToFile

#SaveToClipBoard(char * palette)
SaveToClipBoard = _dll.SaveToClipBoard

#SelectDevice(int devNum)
SelectDevice = _dll.SelectDevice

#SendSoftwareTrigger(void)
SendSoftwareTrigger = _dll.SendSoftwareTrigger

#SetAccumulationCycleTime(float time)
SetAccumulationCycleTime = _dll.SetAccumulationCycleTime

#SetAcqStatusEvent(HANDLE statusEvent)
SetAcqStatusEvent = _dll.SetAcqStatusEvent

#SetAcquisitionMode(int mode)
SetAcquisitionMode = _dll.SetAcquisitionMode

#SetAcquisitionType(int typ)
SetAcquisitionType = _dll.SetAcquisitionType

#SetADChannel(int channel)
SetADChannel = _dll.SetADChannel

#SetAdvancedTriggerModeState(int iState)
SetAdvancedTriggerModeState = _dll.SetAdvancedTriggerModeState

#SetBackground(at_32 * arr, unsigned long size)
SetBackground = _dll.SetBackground

#SetBaselineClamp(int state)
SetBaselineClamp = _dll.SetBaselineClamp

#SetBaselineOffset(int offset)
SetBaselineOffset = _dll.SetBaselineOffset

#SetCameraLinkMode(int mode)
SetCameraLinkMode = _dll.SetCameraLinkMode

#SetCameraStatusEnable(DWORD Enable)
SetCameraStatusEnable = _dll.SetCameraStatusEnable

#SetChargeShifting(unsigned int NumberRows, unsigned int NumberRepeats)
SetChargeShifting = _dll.SetChargeShifting

#SetComplexImage(int numAreas, int * areas)
SetComplexImage = _dll.SetComplexImage

#SetCoolerMode(int mode)
SetCoolerMode = _dll.SetCoolerMode

#SetCountConvertMode(int Mode)
SetCountConvertMode = _dll.SetCountConvertMode

#SetCountConvertWavelength(float wavelength)
SetCountConvertWavelength = _dll.SetCountConvertWavelength

#SetCropMode(int active, int cropHeight, int reserved)
SetCropMode = _dll.SetCropMode

#SetCurrentCamera(long cameraHandle)
SetCurrentCamera = _dll.SetCurrentCamera

#SetCustomTrackHBin(int bin)
SetCustomTrackHBin = _dll.SetCustomTrackHBin

#SetDataType(int typ)
SetDataType = _dll.SetDataType

#SetDACOutput(int iOption, int iResolution, int iValue)
SetDACOutput = _dll.SetDACOutput

#SetDACOutputScale(int iScale)
SetDACOutputScale = _dll.SetDACOutputScale

#SetDDGAddress(BYTE t0, BYTE t1, BYTE t2, BYTE t3, BYTE address)
SetDDGAddress = _dll.SetDDGAddress

#SetDDGExternalOutputEnabled(at_u32 uiIndex, at_u32 uiEnabled)
SetDDGExternalOutputEnabled = _dll.SetDDGExternalOutputEnabled

#SetDDGExternalOutputPolarity(at_u32 uiIndex, at_u32 uiPolarity)
SetDDGExternalOutputPolarity = _dll.SetDDGExternalOutputPolarity

#SetDDGExternalOutputStepEnabled(at_u32 uiIndex, at_u32 uiEnabled)
SetDDGExternalOutputStepEnabled = _dll.SetDDGExternalOutputStepEnabled

#SetDDGExternalOutputTime(at_u32 uiIndex, at_u64 uiDelay, at_u64 uiWidth)
SetDDGExternalOutputTime = _dll.SetDDGExternalOutputTime

#SetDDGGain(int gain)
SetDDGGain = _dll.SetDDGGain

#SetDDGGateStep(double step_Renamed)
SetDDGGateStep = _dll.SetDDGGateStep

#SetDDGGateTime(at_u64 uiDelay, at_u64 uiWidth)
SetDDGGateTime = _dll.SetDDGGateTime

#SetDDGInsertionDelay(int state)
SetDDGInsertionDelay = _dll.SetDDGInsertionDelay

#SetDDGIntelligate(int state)
SetDDGIntelligate = _dll.SetDDGIntelligate

#SetDDGIOC(int state)
SetDDGIOC = _dll.SetDDGIOC

#SetDDGIOCFrequency(double frequency)
SetDDGIOCFrequency = _dll.SetDDGIOCFrequency

#SetDDGIOCNumber(unsigned long numberPulses)
SetDDGIOCNumber = _dll.SetDDGIOCNumber

#SetDDGIOCPeriod(at_u64 period)
SetDDGIOCPeriod = _dll.SetDDGIOCPeriod

#SetDDGIOCTrigger(at_u32 trigger)
SetDDGIOCTrigger = _dll.SetDDGIOCTrigger

#SetDDGOpticalWidthEnabled(at_u32 uiEnabled)
SetDDGOpticalWidthEnabled = _dll.SetDDGOpticalWidthEnabled

#SetDDGLiteGlobalControlByte(unsigned char control)
SetDDGLiteGlobalControlByte = _dll.SetDDGLiteGlobalControlByte

#SetDDGLiteControlByte(AT_DDGLiteChannelId channel, unsigned char control)
SetDDGLiteControlByte = _dll.SetDDGLiteControlByte

#SetDDGLiteInitialDelay(AT_DDGLiteChannelId channel, float fDelay)
SetDDGLiteInitialDelay = _dll.SetDDGLiteInitialDelay

#SetDDGLitePulseWidth(AT_DDGLiteChannelId channel, float fWidth)
SetDDGLitePulseWidth = _dll.SetDDGLitePulseWidth

#SetDDGLiteInterPulseDelay(AT_DDGLiteChannelId channel, float fDelay)
SetDDGLiteInterPulseDelay = _dll.SetDDGLiteInterPulseDelay

#SetDDGLitePulsesPerExposure(AT_DDGLiteChannelId channel, at_u32 ui32Pulses)
SetDDGLitePulsesPerExposure = _dll.SetDDGLitePulsesPerExposure

#SetDDGStepCoefficients(at_u32 mode, double p1, double p2)
SetDDGStepCoefficients = _dll.SetDDGStepCoefficients

#SetDDGStepMode(at_u32 mode)
SetDDGStepMode = _dll.SetDDGStepMode

#SetDDGTimes(double t0, double t1, double t2)
SetDDGTimes = _dll.SetDDGTimes

#SetDDGTriggerMode(int mode)
SetDDGTriggerMode = _dll.SetDDGTriggerMode

#SetDDGVariableGateStep(int mode, double p1, double p2)
SetDDGVariableGateStep = _dll.SetDDGVariableGateStep

#SetDelayGenerator(int board, short address, int typ)
SetDelayGenerator = _dll.SetDelayGenerator

#SetDMAParameters(int MaxImagesPerDMA, float SecondsPerDMA)
SetDMAParameters = _dll.SetDMAParameters

#SetDriverEvent(HANDLE driverEvent)
SetDriverEvent = _dll.SetDriverEvent

#SetEMAdvanced(int state)
SetEMAdvanced = _dll.SetEMAdvanced

#SetEMCCDGain(int gain)
SetEMCCDGain = _dll.SetEMCCDGain

#SetEMClockCompensation(int EMClockCompensationFlag)
SetEMClockCompensation = _dll.SetEMClockCompensation

#SetEMGainMode(int mode)
SetEMGainMode = _dll.SetEMGainMode

#SetExposureTime(float time)
SetExposureTime = _dll.SetExposureTime

#SetExternalTriggerTermination(at_u32 uiTermination)
SetExternalTriggerTermination = _dll.SetExternalTriggerTermination

#SetFanMode(int mode)
SetFanMode = _dll.SetFanMode

#SetFastExtTrigger(int mode)
SetFastExtTrigger = _dll.SetFastExtTrigger

#SetFastKinetics(int exposedRows, int seriesLength, float time, int mode, int hbin, int vbin)
SetFastKinetics = _dll.SetFastKinetics

#SetFastKineticsEx(int exposedRows, int seriesLength, float time, int mode, int hbin, int vbin, int offset)
SetFastKineticsEx = _dll.SetFastKineticsEx

#SetFilterMode(int mode)
SetFilterMode = _dll.SetFilterMode

#SetFilterParameters(int width, float sensitivity, int range, float accept, int smooth, int noise)
SetFilterParameters = _dll.SetFilterParameters

#SetFKVShiftSpeed(int index)
SetFKVShiftSpeed = _dll.SetFKVShiftSpeed

#SetFPDP(int state)
SetFPDP = _dll.SetFPDP

#SetFrameTransferMode(int mode)
SetFrameTransferMode = _dll.SetFrameTransferMode

#SetFrontEndEvent(HANDLE driverEvent)
SetFrontEndEvent = _dll.SetFrontEndEvent

#SetFullImage(int hbin, int vbin)
SetFullImage = _dll.SetFullImage

#SetFVBHBin(int bin)
SetFVBHBin = _dll.SetFVBHBin

#SetGain(int gain)
SetGain = _dll.SetGain

#SetGate(float delay, float width, float stepRenamed)
SetGate = _dll.SetGate

#SetGateMode(int gatemode)
SetGateMode = _dll.SetGateMode

#SetHighCapacity(int state)
SetHighCapacity = _dll.SetHighCapacity

#SetHorizontalSpeed(int index)
SetHorizontalSpeed = _dll.SetHorizontalSpeed

#SetHSSpeed(int typ, int index)
SetHSSpeed = _dll.SetHSSpeed

#SetImage(int hbin, int vbin, int hstart, int hend, int vstart, int vend)
SetImage = _dll.SetImage

#SetImageFlip(int iHFlip, int iVFlip)
SetImageFlip = _dll.SetImageFlip

#SetImageRotate(int iRotate)
SetImageRotate = _dll.SetImageRotate

#SetIsolatedCropMode(int active, int cropheight, int cropwidth, int vbin, int hbin)
SetIsolatedCropMode = _dll.SetIsolatedCropMode

#SetKineticCycleTime(float time)
SetKineticCycleTime = _dll.SetKineticCycleTime

#SetMCPGain(int gain)
SetMCPGain = _dll.SetMCPGain

#SetMCPGating(int gating)
SetMCPGating = _dll.SetMCPGating

#SetMessageWindow(HWND wnd)
SetMessageWindow = _dll.SetMessageWindow

#SetMetaData(int state)
SetMetaData = _dll.SetMetaData

#SetMultiTrack(int number, int height, int offset, int * bottom, int * gap)
SetMultiTrack = _dll.SetMultiTrack

#SetMultiTrackHBin(int bin)
SetMultiTrackHBin = _dll.SetMultiTrackHBin

#SetMultiTrackHRange(int iStart, int iEnd)
SetMultiTrackHRange = _dll.SetMultiTrackHRange

#SetMultiTrackScan(int trackHeight, int numberTracks, int iSIHStart, int iSIHEnd, int trackHBinning, int trackVBinning, int trackGap, int trackOffset, int trackSkip, int numberSubFrames)
SetMultiTrackScan = _dll.SetMultiTrackScan

#SetNextAddress(at_32 * data, long lowAdd, long highAdd, long length, long physical)
SetNextAddress = _dll.SetNextAddress

#SetNextAddress16(at_32 * data, long lowAdd, long highAdd, long length, long physical)
SetNextAddress16 = _dll.SetNextAddress16

#SetNumberAccumulations(int number)
SetNumberAccumulations = _dll.SetNumberAccumulations

#SetNumberKinetics(int number)
SetNumberKinetics = _dll.SetNumberKinetics

#SetNumberPrescans(int iNumber)
SetNumberPrescans = _dll.SetNumberPrescans

#SetOutputAmplifier(int typ)
SetOutputAmplifier = _dll.SetOutputAmplifier

#SetOverlapMode(int mode)
SetOverlapMode = _dll.SetOverlapMode

#SetPCIMode(int mode, int value)
SetPCIMode = _dll.SetPCIMode

#SetPhotonCounting(int state)
SetPhotonCounting = _dll.SetPhotonCounting

#SetPhotonCountingThreshold(long min, long max)
SetPhotonCountingThreshold = _dll.SetPhotonCountingThreshold

#SetPhosphorEvent(HANDLE driverEvent)
SetPhosphorEvent = _dll.SetPhosphorEvent

#SetPhotonCountingDivisions(at_u32 noOfDivisions, at_32 * divisions)
SetPhotonCountingDivisions = _dll.SetPhotonCountingDivisions

#SetPixelMode(int bitdepth, int colormode)
SetPixelMode = _dll.SetPixelMode

#SetPreAmpGain(int index)
SetPreAmpGain = _dll.SetPreAmpGain

#SetDualExposureTimes(float expTime1, float expTime2)
SetDualExposureTimes = _dll.SetDualExposureTimes

#SetDualExposureMode(int mode)
SetDualExposureMode = _dll.SetDualExposureMode

#SetRandomTracks(int numTracks, int * areas)
SetRandomTracks = _dll.SetRandomTracks

#SetReadMode(int mode)
SetReadMode = _dll.SetReadMode

#SetRegisterDump(int mode)
SetRegisterDump = _dll.SetRegisterDump

#SetRingExposureTimes(int numTimes, float * times)
SetRingExposureTimes = _dll.SetRingExposureTimes

#SetSaturationEvent(HANDLE saturationEvent)
SetSaturationEvent = _dll.SetSaturationEvent

#SetShutter(int typ, int mode, int closingtime, int openingtime)
SetShutter = _dll.SetShutter

#SetShutterEx(int typ, int mode, int closingtime, int openingtime, int extmode)
SetShutterEx = _dll.SetShutterEx

#SetShutters(int typ, int mode, int closingtime, int openingtime, int exttype, int extmode, int dummy1, int dummy2)
SetShutters = _dll.SetShutters

#SetSifComment(char * comment)
SetSifComment = _dll.SetSifComment

#SetSingleTrack(int centre, int height)
SetSingleTrack = _dll.SetSingleTrack

#SetSingleTrackHBin(int bin)
SetSingleTrackHBin = _dll.SetSingleTrackHBin

#SetSpool(int active, int method, char * path, int framebuffersize)
SetSpool = _dll.SetSpool

#SetSpoolThreadCount(int count)
SetSpoolThreadCount = _dll.SetSpoolThreadCount

#SetStorageMode(long mode)
SetStorageMode = _dll.SetStorageMode

#SetTECEvent(HANDLE driverEvent)
SetTECEvent = _dll.SetTECEvent

#SetTemperature(int temperature)
SetTemperature = _dll.SetTemperature

#SetTemperatureEvent(HANDLE temperatureEvent)
SetTemperatureEvent = _dll.SetTemperatureEvent

#SetTriggerMode(int mode)
SetTriggerMode = _dll.SetTriggerMode

#SetTriggerInvert(int mode)
SetTriggerInvert = _dll.SetTriggerInvert

#GetTriggerLevelRange(float * minimum, float * maximum)
GetTriggerLevelRange = _dll.GetTriggerLevelRange

#SetTriggerLevel(float f_level)
SetTriggerLevel = _dll.SetTriggerLevel

#SetIODirection(int index, int iDirection)
SetIODirection = _dll.SetIODirection

#SetIOLevel(int index, int iLevel)
SetIOLevel = _dll.SetIOLevel

#SetUserEvent(HANDLE userEvent)
SetUserEvent = _dll.SetUserEvent

#SetUSGenomics(long width, long height)
SetUSGenomics = _dll.SetUSGenomics

#SetVerticalRowBuffer(int rows)
SetVerticalRowBuffer = _dll.SetVerticalRowBuffer

#SetVerticalSpeed(int index)
SetVerticalSpeed = _dll.SetVerticalSpeed

#SetVirtualChip(int state)
SetVirtualChip = _dll.SetVirtualChip

#SetVSAmplitude(int index)
SetVSAmplitude = _dll.SetVSAmplitude

#SetVSSpeed(int index)
SetVSSpeed = _dll.SetVSSpeed

#ShutDown(void)
ShutDown = _dll.ShutDown

#StartAcquisition(void)
StartAcquisition = _dll.StartAcquisition

#UnMapPhysicalAddress(void)
UnMapPhysicalAddress = _dll.UnMapPhysicalAddress

#WaitForAcquisition(void)
WaitForAcquisition = _dll.WaitForAcquisition

#WaitForAcquisitionByHandle(long cameraHandle)
WaitForAcquisitionByHandle = _dll.WaitForAcquisitionByHandle

#WaitForAcquisitionByHandleTimeOut(long cameraHandle, int iTimeOutMs)
WaitForAcquisitionByHandleTimeOut = _dll.WaitForAcquisitionByHandleTimeOut

#WaitForAcquisitionTimeOut(int iTimeOutMs)
WaitForAcquisitionTimeOut = _dll.WaitForAcquisitionTimeOut

#WhiteBalance(WORD * wRed, WORD * wGreen, WORD * wBlue, float * fRelR, float * fRelB, WhiteBalanceInfo * info)
WhiteBalance = _dll.WhiteBalance

#OA_Initialize(const char * const pcFilename, unsigned int uiFileNameLen)
OA_Initialize = _dll.OA_Initialize

#OA_EnableMode(const char * const pcModeName)
OA_EnableMode = _dll.OA_EnableMode

#OA_GetModeAcqParams(const char * const pcModeName, char * const pcListOfParams)
OA_GetModeAcqParams = _dll.OA_GetModeAcqParams

#OA_GetUserModeNames(char * pcListOfModes)
OA_GetUserModeNames = _dll.OA_GetUserModeNames

#OA_GetPreSetModeNames(char * pcListOfModes)
OA_GetPreSetModeNames = _dll.OA_GetPreSetModeNames

#OA_GetNumberOfUserModes(unsigned int * const puiNumberOfModes)
OA_GetNumberOfUserModes = _dll.OA_GetNumberOfUserModes

#OA_GetNumberOfPreSetModes(unsigned int * const puiNumberOfModes)
OA_GetNumberOfPreSetModes = _dll.OA_GetNumberOfPreSetModes

#OA_GetNumberOfAcqParams(const char * const pcModeName, unsigned int * const puiNumberOfParams)
OA_GetNumberOfAcqParams = _dll.OA_GetNumberOfAcqParams

#OA_AddMode(char * pcModeName, unsigned int uiModeNameLen, char * pcModeDescription, unsigned int uiModeDescriptionLen)
OA_AddMode = _dll.OA_AddMode

#OA_WriteToFile(const char * const pcFileName, unsigned int uiFileNameLen)
OA_WriteToFile = _dll.OA_WriteToFile

#OA_DeleteMode(const char * const pcModeName, unsigned int uiModeNameLen)
OA_DeleteMode = _dll.OA_DeleteMode

#OA_SetInt(const char * const pcModeName, const char * pcModeParam, const int iIntValue)
OA_SetInt = _dll.OA_SetInt

#OA_SetFloat(const char * const pcModeName, const char * pcModeParam, const float fFloatValue)
OA_SetFloat = _dll.OA_SetFloat

#OA_SetString(const char * const pcModeName, const char * pcModeParam, char * pcStringValue, const unsigned int uiStringLen)
OA_SetString = _dll.OA_SetString

#OA_GetInt(const char * const pcModeName, const char * const pcModeParam, int * iIntValue)
OA_GetInt = _dll.OA_GetInt

#OA_GetFloat(const char * const pcModeName, const char * const pcModeParam, float * fFloatValue)
OA_GetFloat = _dll.OA_GetFloat

#OA_GetString(const char * const pcModeName, const char * const pcModeParam, char * pcStringValue, const unsigned int uiStringLen)
OA_GetString = _dll.OA_GetString

#Filter_SetMode(unsigned int mode)
Filter_SetMode = _dll.Filter_SetMode

#Filter_GetMode(unsigned int * mode)
Filter_GetMode = _dll.Filter_GetMode

#Filter_SetThreshold(float threshold)
Filter_SetThreshold = _dll.Filter_SetThreshold

#Filter_GetThreshold(float * threshold)
Filter_GetThreshold = _dll.Filter_GetThreshold

#Filter_SetDataAveragingMode(int mode)
Filter_SetDataAveragingMode = _dll.Filter_SetDataAveragingMode

#Filter_GetDataAveragingMode(int * mode)
Filter_GetDataAveragingMode = _dll.Filter_GetDataAveragingMode

#Filter_SetAveragingFrameCount(int frames)
Filter_SetAveragingFrameCount = _dll.Filter_SetAveragingFrameCount

#Filter_GetAveragingFrameCount(int * frames)
Filter_GetAveragingFrameCount = _dll.Filter_GetAveragingFrameCount

#Filter_SetAveragingFactor(int averagingFactor)
Filter_SetAveragingFactor = _dll.Filter_SetAveragingFactor

#Filter_GetAveragingFactor(int * averagingFactor)
Filter_GetAveragingFactor = _dll.Filter_GetAveragingFactor

#PostProcessNoiseFilter(at_32 * pInputImage, at_32 * pOutputImage, int iOutputBufferSize, int iBaseline, int iMode, float fThreshold, int iHeight, int iWidth)
PostProcessNoiseFilter = _dll.PostProcessNoiseFilter

#PostProcessCountConvert(at_32 * pInputImage, at_32 * pOutputImage, int iOutputBufferSize, int iNumImages, int iBaseline, int iMode, int iEmGain, float fQE, float fSensitivity, int iHeight, int iWidth)
PostProcessCountConvert - _dll.PostProcessCountConvert

#PostProcessPhotonCounting(at_32 * pInputImage, at_32 * pOutputImage, int iOutputBufferSize, int iNumImages, int iNumframes, int iNumberOfThresholds, float * pfThreshold, int iHeight, int iWidth)
PostProcessPhotonCounting = _dll.PostProcessPhotonCounting

#PostProcessDataAveraging(at_32 * pInputImage, at_32 * pOutputImage, int iOutputBufferSize, int iNumImages, int iAveragingFilterMode, int iHeight, int iWidth, int iFrameCount, int iAveragingFactor)
PostProcessDataAveraging = _dll.PostProcessDataAveraging