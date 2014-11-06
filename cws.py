import ConfigParser as configparser
import imp
import os
import servicemanager
from signal import CTRL_BREAK_EVENT
import socket
import subprocess
import sys
import win32api
import win32event 
from win32process import DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP, CREATE_NEW_CONSOLE
import win32serviceutil  
import win32service  

CONFIG_NAME = 'WindowsService'

# We need the full path to this file in order to find
# config files in the same folder when invoked as a service.
PATH = os.path.dirname(os.path.abspath(__file__))


class CockpitWindowsService(win32serviceutil.ServiceFramework):  
    """ Serves cockpit devices via a Windows service.

    Creates a service based on information in the 'WindowsService'
    section of a configuration file. The config. file must specify
    the service 'name' and a 'module' to serve.
    The module must implement a 'Server' class, with 'run' and 'shutdown'
    methods.
    (The original intention was to run the module as a script, then
    use signals to trigger shutdown ... but Windows IPC sucks.)
    """

    # Windows services parameters are needed before an instance is 
    # created, so must be set here: read the config and est them.
    config = configparser.ConfigParser()
    config.read(os.path.join(PATH, 'cws.conf'))
    name = config.get(CONFIG_NAME, 'name')
    # Make the short service name CamelCase.
    _svc_name_ = ('cockpit ' + name).title().replace(' ', '')
    _svc_display_name_ = 'Cockpit ' + name + ' service.'
    _svc_description_ = 'Serves cockpit ' + name + ' objects.'
    # This is the device module that will be served.
    device_module = config.get(CONFIG_NAME, 'module')
    # Optional args that the module will be invoked with.
    if config.has_option(CONFIG_NAME, 'args'):
        module_args = config.get(CONFIG_NAME, 'args')
    else:
        module_args = []


    def __init__(self, args):
        self.server = None

        # Initialise service framework.
        win32serviceutil.ServiceFramework.__init__(self,args)  
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)


    def log(self, message, error=False):
        if error:
            logFunc = servicemanager.LogErrorMsg
        else:
            logFunc = servicemanager.LogInfoMsg
        print message
        logFunc("%s: %s" % (self._svc_name_, message))


    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        device = __import__(self.device_module)
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        try:
            self.server = device.Server()
            self.log('%s.server created.' % self.device_module)
            self.server.run()
        except Exception as e:
            self.log(e.message, error = True)
            # Exit with non-zero error code so Windows will attempt to restart.
            sys.exit(-1)
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)


    def SvcStop(self):  
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.server.stop()
        self.log('%s.server shutdown complete.' % self.device_module)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)


if __name__ == '__main__':  
    win32serviceutil.HandleCommandLine(CockpitWindowsService)  