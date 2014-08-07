For some reason, the SWIG files generated here cause errors with the "HANDLE" type when we call SetDriverEvent, so we have
to modify them to fix this. First we strip out the code that causes the error (it refers to a variable, "res1", that 
appears to be completely unused otherwise); second, we set arg1 like so:

arg1 = (HANDLE) (SEB_As_long(obj0));

Dunno what exactly this accomplishes but it seems to do the trick, anyway. The pyAndor_wrap-hackedHANDLE.cxx file is the 
latest "working" hacked SWIG file if you need something to compare against.