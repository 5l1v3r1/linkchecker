# -*- coding: iso-8859-1 -*-
"""Supporting definitions for the Python regression test."""
import linkcheck
from linkcheck.log.Logger import Logger

class Error (Exception):
        """Base class for regression test exceptions."""

class TestFailed (Error):
        """Test failed."""

class TestSkipped (Error):
        """Test skipped.

        This can be raised to indicate that a test was deliberatly
        skipped, but not because a feature wasn't available.  For
        example, if some resource can't be used, such as the network
        appears to be unavailable, this should be raised instead of
        TestFailed.

        """


verbose = 1		# Flag set to 0 by regrtest.py

def unload (name):
	import sys
	try:
		del sys.modules[name]
	except KeyError:
		pass

def forget (modname):
	unload(modname)
	import sys, os
	for dirname in sys.path:
		try:
			os.unlink(os.path.join(dirname, modname + '.pyc'))
		except os.error:
			pass

FUZZ = 1e-6

def fcmp (x, y): # fuzzy comparison function
	if type(x) == type(0.0) or type(y) == type(0.0):
		try:
			x, y = coerce(x, y)
			fuzz = (abs(x) + abs(y)) * FUZZ
			if abs(x-y) <= fuzz:
				return 0
		except:
			pass
	elif type(x) == type(y) and type(x) in (type(()), type([])):
		for i in range(min(len(x), len(y))):
			outcome = fcmp(x[i], y[i])
			if outcome <> 0:
				return outcome
		return cmp(len(x), len(y))
	return cmp(x, y)

TESTFN = '@test' # Filename used for testing
from os import unlink

def findfile (file, here=__file__):
	import os
	if os.path.isabs(file):
		return file
	import sys
	path = sys.path
	path = [os.path.dirname(here)] + path
	for dn in path:
		fn = os.path.join(dn, file)
		if os.path.exists(fn): return fn
	return file


class TestLogger (Logger):
    """ Output for regression test """
    def init (self):
        pass

    def newUrl (self, urlData):
        print 'url',urlData.urlName
        if urlData.cached:
            print "cached"
        if urlData.name:
            print "name",urlData.name
        if urlData.baseRef:
            print "baseurl",urlData.baseRef
        if urlData.infoString:
            print "info",urlData.infoString
        if urlData.warningString:
            print "warning",urlData.warningString
        if urlData.valid:
            print "valid"
        else:
            print "error"

    def endOfOutput (self, linknumber=-1):
        pass
