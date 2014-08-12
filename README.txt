andorSDK provides an interface to Andor's SDK DLL via ctypes.

Originally, the DLL was wrapped with SWIG, but ctypes has been chosen
be preference for the following reasons.

* Many SDK functions use pointers to mutable types to pass back results. 
SWIG would require extensive type mappings to wrap these functions, and
the original mappings have been lost.

* The SDK has 32-bit and 64-bit versions.  Ctypes can provide a common
interface to both, whereas SWIG would necessitate separate builds of the 
pxd.