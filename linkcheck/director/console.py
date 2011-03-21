# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2011 Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
Helpers for console output.
"""
import sys
import os
import traceback
from .. import i18n, configuration, strformat

# Output to stdout and stderr, encoded with the default encoding
stderr = i18n.get_encoded_writer(out=sys.stderr)
stdout = i18n.get_encoded_writer()


def encode (text):
    """Encode text with default encoding if its Unicode."""
    if isinstance(text, unicode):
        return text.encode(i18n.default_encoding, 'ignore')
    return text


class StatusLogger (object):
    """Standard status logger. Default output is stderr."""

    def __init__ (self, fd=stderr):
        """Save file descriptor for logging."""
        self.fd = fd

    def log_status (self, checked, in_progress, queue, duration):
        """Write status message to file descriptor."""
        msg = _n("%2d URL active", "%2d URLs active", in_progress) % \
          in_progress
        self.write(u"%s, " % msg)
        msg = _n("%5d URL queued", "%5d URLs queued", queue) % queue
        self.write(u"%s, " % msg)
        msg = _n("%4d URL checked", "%4d URLs checked", checked) % checked
        self.write(u"%s, " % msg)
        msg = _("runtime %s") % strformat.strduration_long(duration)
        self.writeln(msg)
        self.flush()

    def write (self, msg):
        """Write message to file descriptor."""
        self.fd.write(msg)

    def writeln (self, msg):
        """Write status message and line break to file descriptor."""
        self.fd.write(u"%s%s" % (msg, unicode(os.linesep)))

    def flush (self):
        """Flush file descriptor."""
        self.fd.flush()


def internal_error (out=stderr, etype=None, evalue=None, tb=None):
    """Print internal error message (output defaults to stderr)."""
    print >> out, os.linesep
    print >> out, _("""********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at %s
and include the following information:
- the URL or file you are testing
- the system information below

When using the commandline client:
- your commandline arguments and any custom configuration files.
- the output of a debug run with option "-Dall"

Not disclosing some of the information above due to privacy reasons is ok.
I will try to help you nonetheless, but you have to give me something
I can work with ;) .
""") % configuration.SupportUrl
    if etype is None:
        etype = sys.exc_info()[0]
    if evalue is None:
        evalue = sys.exc_info()[1]
    print >> out, etype, evalue
    if tb is None:
        tb = sys.exc_info()[2]
    traceback.print_exception(etype, evalue, tb, None, out)
    print_app_info(out=out)
    print >> out, os.linesep, \
            _("******** LinkChecker internal error, over and out ********")


def print_app_info (out=stderr):
    """Print system and application info (output defaults to stderr)."""
    print >> out, _("System info:")
    print >> out, configuration.App
    print >> out, _("Python %(version)s on %(platform)s") % \
                    {"version": sys.version, "platform": sys.platform}
    for key in ("LC_ALL", "LC_MESSAGES", "http_proxy", "ftp_proxy", "no_proxy"):
        value = os.getenv(key)
        if value is not None:
            print >> out, key, "=", repr(value)


def print_version (out=stdout):
    """Print the program version (output defaults to stdout)."""
    print >> out, configuration.AppInfo
