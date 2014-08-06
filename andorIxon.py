""" andorIxon - driver for Ixon cameras.

2014-08-06:  Modified by MAP to buffer data.
Images were getting lost, most likely due to ExposureThread and
CorrectionThread working on the same image array.  This has been
replaced with a ring buffer.
TODO: tidy the code.
TODO: add checks to report buffer overruns.
(TODO: wrappedAndorFunc could probably be implemented as a decorator.)

"""

import pyAndor
import numpy
import Pyro4
import threading
import time
import traceback
import weakref
import win32event

## The number of images the buffer can store.
# 512 x 512 x 16-bits --> 512 kb per image.
BUFFER_LENGTH = 100


## Amount of time to wait for an event to trigger in the various *Thread 
# classes. Seeing as these all work inside infinite loops this is basically
# the maximum amount of time it takes them to notice that the program is 
# exiting.
DEFAULT_TIMEOUT_MS = 10000

## Generate a mapping of various error codes to the strings that describe
# them. These are all stored as constants in the pyAndor module, so this
# requires some mucking about with the __dict__ attribute. 
errorToDescMap = {}
for key, value in pyAndor.__dict__.iteritems():
    if key.startswith("DRV_"):
        errorToDescMap[value] = key

## Return the string describing an Andor error. Accepts either an int error
# code, or a list where the first element of the list is an int error code.
def convertErrorToDesc(code):
    key = code
    if type(code) is list:
        key = code[0]
    if key in errorToDescMap:
        return errorToDescMap[key]
    return "Invalid error code %s" % key


## This class wraps a function so that it is threadsafe, and automatically
# translates return values into error messages.
class wrappedAndorFunc:
    lock = threading.Lock()
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        if not self.lock.acquire(0):
            raise RuntimeError, ("Function %s locked" % self.func)
        result = self.func(*args, **kwargs)
        self.lock.release()

        if type(result) is int:
            if result != pyAndor.DRV_SUCCESS:
                raise RuntimeError, convertErrorToDesc(result)
            return

        if type(result) is list:
            if result[0] != pyAndor.DRV_SUCCESS:
                raise RuntimeError, convertErrorToDesc(result[0])
            if len(result) == 2:
                return result[1]
            else:
                return result[1:]
        return result



## This class provides a threadsafe wrapping around Andor's API.
class AndorWrap:
    def __init__(self):
        for key, value in pyAndor.__dict__.iteritems():

            if (not callable(value) or key in
                   ['AbortAcquisition',
                    'GetTemperature',
                    'GetTemperatureF',
                    ]):
                self.__dict__[key] = value
            else:
                self.__dict__[key] = wrappedAndorFunc(value)
## Wrapper around Andor's API. Use this to invoke their functions.
andorWrap = AndorWrap()



## Primary class for dealing with the cameras.
class Camera:
    def __init__(self):
        ## Whether or not this is an iXon-Plus camera, which has slightly
        # different settings. Will be modified in our start() method.
        self.isIxonPlus = False
        ## Connection to the cockpit computer, for sending it data.
        self.clientConnection = None
        ## Thread for receiving image data.
        self.exposureThread = None
        ## Thread for correcting images and sending them to the cockpit.
        self.correctionThread = None
        ## Result of the last call to SetExposureTime; this should be the
        # actual data integration time for the camera.
        self.exposureTime_cache = None
        ## Acquisition mode used. Generally we're in frame-transfer mode. 
        # See prepareAcqMode for more information.
        self.acquisitionMode = None
        ## Result of the last time we called SetEMCCDGain.
        self.gain_cache = None
        ## Result of the last time we called SetShutter.
        self.shutter_cache = None
        ## Result of the last time we called SetTrigger. Generally we always
        # run in external trigger mode, so this should always be 1.
        self.trigger_cache = None
        ## Result of calling SetFanMode. Generally we leave the fans off and
        # rely instead on water cooling.
        self.fanmode_cache = None
        ## Result of calling SetOutputAmplifier; this is 0 if we're in 
        # conventional mode or 1 if in EM mode.
        self.outamp_cache = None
        ## Result of calling SetADChannel; this is 0 if we're in 14-bit mode
        # or 1 if in 16-bit mode.
        self.adc_cache = None
        ## Result of calling SetVSSpeed.
        self.vsspeed_cache = None
        ## Result of calling SetHSSpeed
        self.hsspeed_cache = None
        ## Result of calling SetPreAmpGain
        self.preAmpGain_cache = None
        ## Result of calling setcorrrot, or used as the default value if 
        # none is specified in that function. This is rotation applied to the 
        # correction files, which depends on the current value of
        # self.outamp_cache. I suspect this is all going to need to be redone
        # when we re-add correction files.
        self.rot_cache = 0
        ## Ring buffer for exposure number.
        self.picNum_arr = numpy.empty(BUFFER_LENGTH, dtype = numpy.uint16)
        ## As picNum_arr, but in this case tracks the time when an image is
        # obtained. 
        self.picTime_arr = numpy.empty(BUFFER_LENGTH, dtype = numpy.float32)

        ## This a ring buffer for images.  It will be allocated elsewhere.
        self.ring = []
        # We use a semaphore to control the CorrectionThread.
        self.semaphore = threading.Semaphore()
        # Set semaphore count to zero


    def startThreads(self):
        self.quit() # in case start() was called twice ...
        ## Create exposureThread before correctionThread:  the threads
        # call .start() at the end of their __init__s, so start running
        # immediately; exposureThread needs to grab a semaphore first, 
        # otherwise correctionThread will to operate on no data.
        self.exposureThread = ExposureThread(self)
        self.correctionThread = CorrectionThread(self)
        self.correctionThread.setClient(self.clientConnection)


    def quit(self):
        self.resetToSafe()

        try:
            self.exposureThread.quit()
        except:
            pass
        try:
            self.correctionThread.quit()
        except:
            pass


    def quitAndShutdown(self):
        self.quit()
        self.controlledShutdown()


    def __del__(self):
        self.quit()


    def receiveClient(self, uri):
        if uri is None:
            self.correctionThread.setClient(None)
        else:
            self.clientConnection = Pyro4.Proxy(uri)
            if self.correctionThread is not None:
                self.correctionThread.setClient(self.clientConnection)


    def init(self):
        andorWrap.Initialize("")


    def start(self, isIxonPlus = False):
        self.isIxonPlus = isIxonPlus
        try:
            andorWrap.GetStatus()
        except RuntimeError, e:
            print "Processing error getting status:",e
            if e.args[0] == 'DRV_NOT_INITIALIZED':
                print 'initing...'
                try:
                    print "call init"
                    self.init()
                except Exception, e:
                    print "Error in initialization:",e
                    raise e
            else:
                print "Error in start:",e
                raise e

        nx, ny = self.chipSizeXY = andorWrap.GetDetector()
        andorWrap.SetReadMode(4) # image mode
        andorWrap.SetDMAParameters(MaxImagesPerDMA = 1, SecondsPerDMA = 0)

        self.settrigger(ext = 0)
#IMD 20130405 - hacked to keep fan on as we dont have water cooling as yet.
        self.setfan(0)
        andorWrap.CoolerON()
        self.prepareAcqMode(7)
        self.SetPreAmpGain(0)

        ## iXon-Plus cameras have different EM gain modes
        if self.isIxonPlus:
            # Allow settings in [10, 300]
#IMD 20130213 was mode 3 for real gain, ixon ultra claims not supported?
            andorWrap.SetEMGainMode(2)
        else:
            # Allow settings in [1, 255]
            andorWrap.SetEMGainMode(0)
        self.exposureEvent = win32event.CreateEvent(None, 0, 0, None)
        self.correctionEvent = win32event.CreateEvent(None, 0, 0, None)

        andorWrap.SetDriverEvent(int(self.exposureEvent))

        self.startThreads()
        print self.setImage() #default size is "fullCCD" no binning - create imageArray
        self.setskipLRTB(0, 0, 0, 0) #create imageOutArray

        self.setdarkLRTB(0, 0, 0, 0)
        self.setcorrmode(True)
        self.setcorrrot(0)
        #IMD 20130218 - set offset from 1000 to 0.
        self.setcorrbaseoffset(0)
        self.setcorroffset(numpy.zeros(self.imageOutArray.shape))
        self.setcorrgain(numpy.ones(self.imageOutArray.shape))

        vs, vspeed = andorWrap.GetFastestRecommendedVSSpeed()
        print "SetVSSpeed to GetFastestRecommendedVSSpeed: %gus (idx %d)" % (vspeed, vs)

        ####### this needs to be AFTER startThreads !!!! because of correctionThread in setcorrror
        self.setoutamp(conv = 1) # workaround: otherwise sethsspeed uses self.outamp_cache being None

        self.cammode(is16Bit = 1, conv = 1, hsSpeedIdx = 0, vsSpeedIdx = vs)
        self.resetToSafe()
        print "setExpTime: ", self.setExposureTime(100)


    ## Reset the camera to "safe" settings: close the shutter and turn off
    # EM gain. Note that several of our cameras have their shutters glued
    # open, so trying to close them won't accomplish anything.
    def resetToSafe(self):
        status = andorWrap.GetStatus()
        if status == pyAndor.DRV_ACQUIRING:
            r = andorWrap.AbortAcquisition()
            print "abort:", convertErrorToDesc(r)
        status = andorWrap.GetStatus()

        print "Reset to safe settings, status:", convertErrorToDesc(status)

        try:
            self.setshutter(1)
            print "open shutter"
            self.setgain(0)
        except Exception, e:
            print "Error setting shutter/gain:", e
            raise e


    def cammode(self, is16Bit = 1, conv = 0, hsSpeedIdx = None, EMgain = None, vsSpeedIdx = None):
        self.setadc(is16Bit = is16Bit)
        if hsSpeedIdx is not None:
            self.sethsspeed(hsSpeedIdx, outamp = conv)
        else:
            self.setoutamp(conv = conv)            
        if vsSpeedIdx is not None:
            self.setvsspeed(vsSpeedIdx)
        if EMgain is not None:
            self.setgain(EMgain)


    def prepareAcqMode(self, mode):
        '''
        mode :
        1 Single Scan (non FrameTransfer mode)
        2 Accumulate
        3 Kinteics
        4 Fast Kinetics
        5 'till abort' non-frame transfer
        6 frame-transfer 
        7 'till abort' frame transfer
        '''

        if self.acquisitionMode == mode:
            # Already in that mode.
            return

        andorWrap.SetAcquisitionMode(mode)
        self.acquisitionMode = mode
        print "acq mode = ",mode

        # reset exposure counter
        self.exposureThread.exposureCounter = 0


    def controlledShutdown(self, waitMinTemp=-40, deltaSecs = 3):
        self.resetToSafe()
        andorWrap.SetTemperature(0)

        print "ShutDown()...",
        Y.refresh()
        andorWrap.ShutDown()
        print "done."


    def info_HSSpeeds(self):
        nADChannels = andorWrap.GetNumberADChannels()
        s = "GetNumberADChannels: %d\n" % nADChannels
        for ch in range(nADChannels):
            for conv in [0, 1]:
                nADSpeeds = andorWrap.GetNumberHSSpeeds(ch, conv)
                s += "   ADChannel: %d type(conv=):%d->  GetNumberHSSpeeds: %d\n" % (ch, conv, nADSpeeds)
                for i in range(nADSpeeds):
                    f = andorWrap.GetHSSpeed(ch, conv, i)
                    s+= "          speed %d (conv=%s)-> %5s\n" % (i, conv, f)
        return s


    def info_VSSpeeds(self):
        nVSSpeeds = andorWrap.GetNumberVSSpeeds()
        s = "GetNumberVSSpeeds: %s\n" % nVSSpeeds

        for i in range(nVSSpeeds):
            f = andorWrap.GetVSSpeed(i)
            s += "   GetVSSpeed %d: %s\n" % (i, f)
        return s


    def setExposureTime(self, ms):
        andorWrap.SetExposureTime(ms / 1000.0)
        # It is necessary to get the actual times as the system will 
        # calculate the nearest possible time. eg if you set exposure time 
        # to be 0, the system will use the closest value (around 0.01s)
        fExposure, fAccumTime, fKineticTime = andorWrap.GetAcquisitionTimings()
        self.exposureTime_cache = fExposure * 1000
        print "exp time",self.exposureTime_cache
        return self.exposureTime_cache


    def getexp(self):
        return self.exposureTime_cache


    def gettrig(self):
        return self.trigger_cache


    def getoutamp(self):
        return self.outamp_cache


    def getadc(self):
        return self.adc_cache


    def gethsspeed(self, channel, amp, index):
        return andorWrap.GetHSSpeed(channel, amp, index)


    def gethsspeed_cache(self):
        return self.hsspeed_cache


    def getvsspeed(self, val):
        return andorWrap.GetVSSpeed(val)


    def getvsspeed_cache(self):
        return self.vsspeed_cache


    def getshutter(self):
        return self.shutter_cache


    def getgain(self):
        return self.gain_cache


    def getfanmode(self):
        return self.fanmode_cache


    def getTimesExpAccKin(self):
        return [1000*t for t in andorWrap.GetAcquisitionTimings()]


    def getFastestRecommendedVSSpeed(self):
        return andorWrap.GetFastestRecommendedVSSpeed()


    def getStatus(self):
        return convertErrorToDesc(andorWrap.GetStatus())


    def getImage(self):
        ## Reads an image from the camera and puts it into imageArray.
        try:
            andorWrap.GetOldestImage16(self.imageArray)
            return self.imageArray
        except Exception, e:
            print "Couldn't get image at %s: %s" % (time.asctime(), e)


    def setgain(self, g):
        andorWrap.SetEMCCDGain(g)
        self.gain_cache = g


    def setAdvanced(self, val):
        andorWrap.SetEMAdvanced(val)


    def setshutter(self, shutter):
        '''mode
        0 auto
        1 open
        2 close
        '''
        openclose = 1
        ttl = 1
        andorWrap.SetShutter(ttl, shutter, openclose, openclose)
        self.shutter_cache = shutter


    def settrigger(self, ext):
        '''trigger mode:
        ext = 0  internal
        ext = 1  external
        '''
        andorWrap.SetTriggerMode(ext)
        self.trigger_cache = ext


    def setfan(self, mode):
        '''mode:
        fan on full (0)
        fan on low (1)
        fan off (2)
        '''
        andorWrap.SetFanMode(mode)
        self.fanmode_cache = mode


    def setoutamp(self, conv):
        '''
        conv = 0 = EM-gain output amplifier
        conv = 1 = conventional output amplifier
        '''
        andorWrap.SetOutputAmplifier(conv)
        self.outamp_cache = conv
        self.setcorrrot() # adjust rotationCorrection according to outamp


    def setadc(self, is16Bit):
        '''
        is16Bit = 0  use 14-bit ad-channel
        is16Bit = 1  use 16-bit ad-channel
        '''
#IMD 20130219 The ultra only has a single ad channel I think.        
#        andorWrap.SetADChannel(is16Bit)
        andorWrap.SetADChannel(0)

        self.adc_cache = is16Bit


    def GetNumberHSSpeeds(self, amp, channel):
        return andorWrap.GetNumberHSSpeeds(amp, channel)


    def GetNumberVSSpeeds(self):
        return andorWrap.GetNumberVSSpeeds()


    def setvsspeed(self, vsSpeedIdx):
        andorWrap.SetVSSpeed(vsSpeedIdx)
        self.vsspeed_cache = vsSpeedIdx


    def sethsspeed(self, hsSpeedIdx, outamp = None):
        if outamp is None:
            outamp = self.outamp_cache
        andorWrap.SetHSSpeed(type = outamp, index = hsSpeedIdx)
        self.outamp_cache  = outamp
        self.hsspeed_cache = hsSpeedIdx
        self.setcorrrot() # adjust rotationCorrection according to outamp


    def GetNumberPreAmpGains(self):
        return andorWrap.GetNumberPreAmpGains()


    def GetPreAmpGain(self, idx):
        return andorWrap.GetPreAmpGain(idx)


    def SetPreAmpGain(self, idx):
        andorWrap.SetPreAmpGain(idx)
        self.preAmpGain_cache = idx


    def GetPreAmpGain_Cache(self):
        return self.preAmpGain_cache


    def IsPreAmpGainAvailable(self, channel, amplifier, index, gain):
        return andorWrap.IsPreAmpGainAvailable(channel, amplifier, index, gain)


    def setImage(self, x0 = 0, y0 = 0, nx = None, ny = None, binX = 1, binY = 1):
        '''
        if nx ny are None use values from chipSizeXY
        nx, ny are in pixels
         if bin>1 the resulting image will be smaller than nx, ny ! (divided)
        '''
        if nx is None:
            nx = ((self.chipSizeXY[0]-x0) // binX) * binX
        if ny is None:
            ny = ((self.chipSizeXY[1]-y0) // binY) * binY

        if nx % binX:
            raise ValueError, "binX=%d does not divide nx=%d" % (binX, nx)
        if ny % binY:
            raise ValueError, "binY=%d does not divide ny=%d" % (binY, ny)

        andorWrap.SetImage(binX, binY,
                        1 + x0, 1 + x0 + nx - 1,
                        1 + y0, 1 + y0 + ny - 1)

        nx /= binX
        ny /= binY

        # Allocate the array for incoming images.
        self.imageArray = numpy.zeros((ny, nx), dtype = numpy.uint16)

        # Allocate the image buffer and initialise buffer indices in threads.
        self.ring = [numpy.empty((ny, nx), dtype=numpy.uint16) for null in range(BUFFER_LENGTH)]
        self.exposureThread.ring_i = 0
        self.correctionThread.ring_i = 0

        # Allocate the array for corrected images to be sent to client.
        self.correctionThread.setImgArray_in(self.imageArray)
        return ny, nx


    def setdarkLRTB(self, left, right, top, bottom):
        self.correctionThread.setDarkLRTB(left, right, top, bottom)


    def setskipLRTB(self, left, right, top, bottom):
        self.correctionThread.setSkipLRTB(left, right, top, bottom)
        ny, nx = self.imageArray.shape
        self.imageOutArray = numpy.zeros((ny-top-bottom, nx-left-right), dtype = numpy.uint16)
        self.correctionThread.setImgArray_out(self.imageOutArray)
        return self.imageOutArray.shape


    def getdarkLRTB(self):
        return self.correctionThread.getDarkLRTB()


    def getskipLRTB(self):
        return self.correctionThread.getSkipLRTB()


    def setcorrbaseoffset(self, baseoffset):
        self.correctionThread.setBaseOffset(baseoffset)


    def getcorrbaseoffset(self):
        return self.correctionThread.getBaseOffset()


    def setcorroffset(self, offsetImg):
        self.correctionThread.setOffset(offsetImg)


    def getcorroffset(self):
        return self.correctionThread.getOffset()


    def setcorrgain(self, gainImg):
        self.correctionThread.setGain(gainImg)


    def getcorrgain(self):
        return self.correctionThread.getGain()


    def setcorrmode(self, mode):
        self.correctionThread.setCorrMode(mode)


    def getcorrmode(self):
        return self.correctionThread.getCorrMode()


    def setcorrrot(self, rot = None):
        '''adjust rotationCorrection according to outamp
           and omx port (ne, nw, west, east)
        '''
        if rot is None:
            rot = self.rot_cache
        else:
            self.rot_cache = rot
        if self.outamp_cache == 1: # conv channel
            if   rot == 0: corrRot = -2
            elif rot == 1: corrRot = -3
            elif rot == 2: corrRot = -1
            elif rot == 3: corrRot = -4
            elif rot ==-1: corrRot = 2
            elif rot ==-2: corrRot = 0
            elif rot ==-3: corrRot = 1
            elif rot ==-4: corrRot = 3        
            else: raise ValueError, "illegal rotation mode"
        else:
            if -4 <= rot <4:
                corrRot = rot
            else: raise ValueError, "illegal rotation mode"
        self.correctionThread.setCorrRot(corrRot)


    def getcorrrot(self):
        return self.rot_cache


    def skipNextNimages(self, n = None):
        '''if n is None: get skip-value
           else: set how many of the upcoming acuisition should NOT be send ("skipped")
        '''
        print "Skipping next",n,"images"
        if n is None:
            return self.exposureThread.skipNextNimages
        else:
            self.exposureThread.skipNextNimages = n


    def skipEveryNimages(self, n):
        '''Starting from now, only return every Nth image.'''
        print "Skipping every",n,"images"
        self.exposureThread.skipEveryNimages = n
        self.exposureThread.exposureCount = 0


    def gettemp(self):
        s, t = andorWrap.GetTemperature()
        return (convertErrorToDesc(s),t)


    def settemp(self, t):
        andorWrap.SetTemperature(t)


    def expose(self):
        self.prepareAcqMode(1)
        self.exposureThread.camAborted = False
        andorWrap.StartAcquisition()


    def prepareTillAbort(self, frameTransfer):
        if frameTransfer:
            self.prepareAcqMode(7)
        else:
            self.prepareAcqMode(5)


    def exposeTillAbort(self, frameTransfer):
        self.prepareTillAbort(frameTransfer)
        self.exposureThread.camAborted = False
        andorWrap.StartAcquisition()


    def abort(self):
        self.exposureThread.camAborted = True
        andorWrap.AbortAcquisition()



## This thread waits for an exposure event to occur, and when it does, 
# calls Camera.getImage(). It has support for skipping some number of images,
# which I believe we use to toss the first image in a given stack (since that
# image has been integrating since the last time we took an image, and is
# therefore largely junk).
class ExposureThread(threading.Thread):
    def __init__(self, cam):
        threading.Thread.__init__(self)
        self.skipNextNimages = 0
        self.exposureCount = 0
        self.skipEveryNimages = 1
        self.haveQuit = 0
        self.camAborted = False
        self.cam = weakref.proxy(cam)
        self.ring_i = 0

        self.start()


    def __del__(self):
        if self.isAlive():
            self.quit()


    def quit(self):
        self.haveQuit = 1
        win32event.SetEvent(self.cam.exposureEvent)


    def run(self):
        try:
            self.run1()
        except:
            print "** thread aborted ** (%s)" %self
            traceback.print_exc()


    def run1(self):
        print "ExposureThread start"
        exposureEvent = self.cam.exposureEvent

        ## Decrement the semaphore - will be released when there is data for
        # correctionThread to process.
        self.cam.semaphore.acquire()

        import time
        t0 = None

        while not self.haveQuit:
            x = win32event.WaitForSingleObject(exposureEvent, DEFAULT_TIMEOUT_MS)#HERE WE WAIT FOR IRQ 
            # Reset the event so that subsequent events will be detected.
            if self.haveQuit:
                break

            if x == 0 and not self.camAborted: # not timed out
                try:
                    now = time.clock()
                    self.cam.picTime_arr[self.ring_i] = now
                    # MAP 20140806: hint - this populates imageArray.
                    self.cam.getImage()
                    if self.skipNextNimages > 0:
                        print "Skipping exposure at clock = %g." % now
                        self.skipNextNimages -= 1
                    else:
                        if self.exposureCount == 0: t0 = now
                        self.exposureCount += 1
                        print "Buffering exposure %d  at  clock = %g." % (self.exposureCount, now - t0)
                        if self.exposureCount % self.skipEveryNimages == 0:
                            # Copy image data to buffer and update buffer_index
                            self.cam.picNum_arr[self.ring_i] = self.exposureCount
                            self.cam.ring[self.ring_i][:,:] = self.cam.imageArray
                            self.cam.semaphore.release()
                            self.ring_i += 1
                            if self.ring_i >= BUFFER_LENGTH:
                                self.ring_i = 0
                except:
                    print "** exception in exposeThread loop ** (%s)" %self
                    traceback.print_exc()                    
        print "ExposureThread done"


class CorrectionThread(threading.Thread):
    def __init__(self, cam):
        threading.Thread.__init__(self)
        self.haveQuit = 0

        self.cam = cam

        darkPixelMaxInt = 10000
        self.darkPixelHist = numpy.zeros((darkPixelMaxInt), dtype = numpy.int32)

        self.corrRot     = 0
        self.correctMode = 1
        self.clientConnection = None
#IMD 20130218 added to stop correct thread crashes
        self.skipLeft = 0
        self.skipRight = 0
        self.skipTop = 0
        self.skipBottom = 0

        self.imageArray=numpy.zeros((512, 512), dtype = numpy.uint16)
        self.newImage = numpy.zeros((512, 512), dtype = numpy.uint16)

        self.ring_i = 0
        self.start()


    def __del__(self):
        print "__del__ CorrectionThread", self
        if self.isAlive():
            self.quit()

    def quit(self):
        self.haveQuit = 1


    def setClient(self, client):
        self.clientConnection = client


    def setDarkLRTB(self, left, right, top, bottom):
        self.darkLeft, self.darkRight, self.darkTop, self.darkBottom=\
        left, right, top, bottom


    def setSkipLRTB(self, left, right, top, bottom):
        self.skipLeft, self.skipRight, self.skipTop, self.skipBottom=\
        left, right, top, bottom


    def getDarkLRTB(self):
        return self.darkLeft, self.darkRight, self.darkTop, self.darkBottom


    def getSkipLRTB(self):
        return self.skipLeft, self.skipRight, self.skipTop, self.skipBottom

    def setBaseOffset(self, baseoffset):
        self.baseOffset = baseoffset


    def getBaseOffset(self):
        return self.baseOffset


    def setOffset(self, offsetImg):
        self.offset = offsetImg


    def getOffset(self):
        return self.offset


    def setGain(self, gainImg):
        self.gain = gainImg


    def getGain(self):
        return self.gain

    def setCorrMode(self, mode):
        self.correctMode = mode


    def getCorrMode(self):
        return self.correctMode


    def setCorrRot(self, corrRot):
        self.corrRot = corrRot


    def setImgArray_in(self, arr):
        self.imageArray = arr


    def setImgArray_out(self, arr):
        self.newImage = arr
        self.offset = numpy.zeros(arr.shape)
        self.gain = numpy.ones(arr.shape)


    def run(self):
        try:
            self.run1()
        except:
            print "** thread aborted ** (%s)" %self
            traceback.print_exc()


    def run1(self):
        print "CorrectionThread start.\n"
        while not self.haveQuit:
            if self.haveQuit:
                break
            # Here we check the to see if there is data to process
            if self.cam.semaphore.acquire(blocking=False):
                try:
                    # Crop down to our readout size. This requires rotating/flipping our crop values,
                    # since the shape of self.imageArray depends on our current rotation.
                    left, right, top, bottom = self.skipLeft, self.skipRight, self.skipTop, self.skipBottom
                    # We'll want to use negative indices for these two offsets.
                    right = -right
                    top = -top
                    # Of course, negative indices don't work for 0, so use None instead
                    # as appropriate.
                    if not right:
                        right = None
                    if not top:
                        top = None
                    self.newImage[:,:] = self.cam.ring[self.ring_i][bottom:top, left:right]

                    buffers = self.cam.exposureThread.ring_i - self.ring_i
                    if buffers < 0: buffers = buffers + BUFFER_LENGTH

                    print "... ... sent image %d from clock = %g. \t Using %d buffers." % (
                            self.cam.picNum_arr[self.ring_i],
                            self.cam.picTime_arr[self.ring_i],
                            buffers)

                    if self.clientConnection is not None:
                        self.clientConnection.receiveData('new image',
                                                          self.newImage, 
                                                          self.cam.picTime_arr[self.ring_i])
                except Exception, e:
                    print "Exception in correction thread: %s" % e
                    print ''.join(Pyro4.util.getPyroTraceback())
                    traceback.print_exc()

                finally:
                    self.ring_i += 1
                    if self.ring_i >= BUFFER_LENGTH:
                        self.ring_i = 0
            else:
                time.sleep(0.01)

        print "CorrectionThread done"


    ## Rotate/mirror the input image according to self.corrRot.
    def rotateImage(self, image):
        if self.corrRot == 0:
            return image
        elif self.corrRot > 0:
            # Rotate clockwise by 90 * corrRot; rot90 rotates
            # counterclockwise so we have to flip sign.
            return numpy.rot90(image, 4 - self.corrRot)
        elif self.corrRot == -1:
            # Mirror vertically.
            return numpy.flipud(image)
        elif self.corrRot == -2:
            # Mirror horizontally
            return numpy.fliplr(image)
        elif self.corrRot == -3:
            # Rotate 90 degrees and mirror vertically.
            temp = numpy.rot90(image, 3)
            return numpy.flipud(temp)
        elif self.corrRot == -4:
            # Rotate 90 degrees and mirror vertically.
            temp = numpy.rot90(image, 3)
            return numpy.fliplr(temp)

        raise RuntimeError("Invalid correction rotation value %d" % self.corrRot)

