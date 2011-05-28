# -*- coding: iso-8859-1 -*-
# Copyright (C) 2004-2009 Bastian Kleineidam
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
Define http test support classes for LinkChecker tests.
"""

import SimpleHTTPServer
import BaseHTTPServer
import httplib
import time
import threading
from . import LinkCheckTest


class StoppableHttpRequestHandler (SimpleHTTPServer.SimpleHTTPRequestHandler, object):
    """
    HTTP request handler with QUIT stopping the server.
    """

    def do_QUIT (self):
        """
        Send 200 OK response, and set server.stop to True.
        """
        self.send_response(200)
        self.end_headers()
        self.server.stop = True

    def log_message (self, format, *args):
        """
        Logging is disabled.
        """
        pass

# serve .xhtml files as application/xhtml+xml
StoppableHttpRequestHandler.extensions_map.update({
        '.xhtml': 'application/xhtml+xml',
})


class StoppableHttpServer (BaseHTTPServer.HTTPServer, object):
    """
    HTTP server that reacts to self.stop flag.
    """

    def serve_forever (self):
        """
        Handle one request at a time until stopped.
        """
        self.stop = False
        while not self.stop:
            self.handle_request()


class NoQueryHttpRequestHandler (StoppableHttpRequestHandler):
    """
    Handler ignoring the query part of requests.
    """

    def remove_path_query (self):
        """
        Remove everything after a question mark.
        """
        i = self.path.find('?')
        if i != -1:
            self.path = self.path[:i]

    def do_GET (self):
        """
        Removes query part of GET request.
        """
        self.remove_path_query()
        super(NoQueryHttpRequestHandler, self).do_GET()

    def do_HEAD (self):
        """
        Removes query part of HEAD request.
        """
        self.remove_path_query()
        super(NoQueryHttpRequestHandler, self).do_HEAD()


class HttpServerTest (LinkCheckTest):
    """
    Start/stop an HTTP server that can be used for testing.
    """

    def __init__ (self, methodName='runTest'):
        """
        Init test class and store default http server port.
        """
        super(HttpServerTest, self).__init__(methodName=methodName)
        self.port = None

    def start_server (self, handler=NoQueryHttpRequestHandler):
        """Start a new HTTP server in a new thread."""
        self.port = start_server(handler)
        assert self.port is not None

    def stop_server (self):
        """Send QUIT request to http server."""
        stop_server(self.port)


def start_server (handler):
    """Start an HTTP server thread and return its port number."""
    server_address = ('localhost', 0)
    handler.protocol_version = "HTTP/1.0"
    httpd = StoppableHttpServer(server_address, handler)
    port = httpd.server_port
    t = threading.Thread(None, httpd.serve_forever)
    t.start()
    # wait for server to start up
    while True:
        try:
            conn = httplib.HTTPConnection("localhost:%d" % port)
            conn.request("GET", "/")
            conn.getresponse()
            break
        except:
            time.sleep(0.5)
    return port


def stop_server (port):
    """Stop an HTTP server thread."""
    conn = httplib.HTTPConnection("localhost:%d" % port)
    conn.request("QUIT", "/")
    conn.getresponse()
