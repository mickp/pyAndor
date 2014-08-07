// -*- c++ -*-

///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
//////////////////// !!!!  THREAD  !!!!   /////////////////////////////////
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

//---------------------------------------------------------------------------
// Tell SWIG to wrap all the wrappers with our thread protection

// from email:
//     --------------------  <email> ----------------------------------
//  Delivered-To: Swig@cs.uchicago.edu
//  From: Lars Immisch <lars@ibp.de>
//  To: Sebastian Haase <haase@msg.ucsf.edu>
//  Cc: Swig@cs.uchicago.edu
//  Subject: Re: [Swig] PyAllowThreads  with  %exception and %typemap(throws) char *
//  References: <0db001c382c3$bf328aa0$421ee6a9@rodan>
//  In-Reply-To: <0db001c382c3$bf328aa0$421ee6a9@rodan>
//  Date: Wed, 24 Sep 2003 23:02:59 +0200

#if 1 /// 2004/11/11 // c
%{
  //SWIGDEBUG  
/* this goes inside the module definition scope */
#ifdef WIN32
#include <windows.h>
DWORD tlsindex;
#else
#include <pthread.h> 
pthread_key_t tlsindex;
#endif
 %}

/* outside the module definition scope */
%init %{
  //SWIGDEBUG  %init
#ifdef WIN32
	tlsindex = TlsAlloc();
#else
	pthread_key_create(&tlsindex, NULL);
#endif
%}

#endif // 2004/11/11 //c

// -------- Then:

%exception {
  //SWIGDEBUG  %exception 
	PyThreadState *tstate = PyEval_SaveThread(); // wxPyBeginAllowThreads();

/* note %#ifdef - this prompts SWIG to put the #ifdef into
    the generated code. */
%#ifdef WIN32
	TlsSetValue(tlsindex, tstate);
%#else
	pthread_setspecific(tlsindex, tstate);
%#endif
	$action
	PyEval_RestoreThread(tstate); //wxPyEndAllowThreads( tstate );
	if (PyErr_Occurred()) return NULL;
}

%typemap(throws) char * {
  //SWIGDEBUG  %typemap(throws) char *
	PyThreadState *tstate;

%#ifdef WIN32
	tstate = (PyThreadState*)TlsGetValue(tlsindex);
%#else
	tstate = (PyThreadState*)pthread_getspecific(tlsindex);
%#endif

	PyEval_RestoreThread(tstate); //wxPyEndAllowThreads(tstate);
	PyErr_SetString(PyExc_RuntimeError, $1);
	SWIG_fail;
}

//     --------------------  </email> ----------------------------------

//  //  //  //  //  //  //  //%except(python) {
//  //  //  //  //  //  //  %exception {
//  //  //  //  //  //  //    //fprintf(stderr,"SWIG ex 1/5:*** %d\n", wxThread::IsMain());
//  //  //  //  //  //  //    //////////////wxGetApp().main_tstate = wxPyBeginAllowThreads();
//  //  //  //  //  //  //    PyThreadState* __tstate = wxPyBeginAllowThreads();
//  //  //  //  //  //  //    //fprintf(stderr,"SWIG ex 2/5:*** %d\n", wxThread::IsMain());

//  //  //  //  //  //  //  $action
//  //  //  //  //  //  //    //fprintf(stderr,"SWIG ex 3/5:*** %d\n", wxThread::IsMain());
//  //  //  //  //  //  //    //////////////wxPyEndAllowThreads( wxGetApp().main_tstate );
//  //  //  //  //  //  //    wxPyEndAllowThreads( __tstate );
//  //  //  //  //  //  //    //fprintf(stderr,"SWIG ex 4/5:*** %d\n", wxThread::IsMain());
//  //  //  //  //  //  //      if (PyErr_Occurred()) return NULL;
//  //  //  //  //  //  //    //fprintf(stderr,"SWIG ex 5/5:*** %d\n", wxThread::IsMain());
//  //  //  //  //  //  //  }


//  //  //  //  //  //  //  %typemap(throws) char * {
//  //  //  //  //  //  //    //yyyyyyyyyyyy
//  //  //  //  //  //  //    printf("FIXME  %typemap(throws)  FIXME %s:%d\n", __FILE__, __LINE__);
//  //  //  //  //  //  //    wxPyEndAllowThreads( wxGetApp().main_tstate );
//  //  //  //  //  //  //    PyErr_SetString(PyExc_RuntimeError, $1);
//  //  //  //  //  //  //    SWIG_fail;
//  //  //  //  //  //  //  }
