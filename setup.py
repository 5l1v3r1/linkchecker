#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
# Copyright (C) 2000-2010 Bastian Kleineidam
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
Setup file for the distuils module.
"""

import sys
if not (hasattr(sys, 'version_info') or
        sys.version_info < (2, 5, 0, 'final', 0)):
    raise SystemExit("This program requires Python 2.5 or later.")
import os
import subprocess
import platform
import stat
import glob

# Use setuptools to support eggs. Note that this conflicts with py2exe.
# The setuptools are not officially supported.
#try:
#    from setuptools import setup
#    from setuptools.command.install_lib import install_lib
#    from setuptools.command.build_ext import build_ext
#    from setuptools.command.sdist import sdist
#    from distutils.command.sdist import sdist as _sdist
#    sdist.user_options = _sdist.user_options + sdist.user_options
#    from setuptools.extension import Extension
#    from setuptools.dist import Distribution
#except ImportError:
# use distutils
from distutils.core import setup, Extension
from distutils.command.install_lib import install_lib
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist
from distutils.command.clean import clean
from distutils.command.build import build
from distutils.command.install_data import install_data
from distutils.command.register import register
from distutils.dir_util import remove_tree, copy_tree
from distutils.file_util import write_file
from distutils import util, log
try:
    # Note that py2exe monkey-patches the distutils.core.Distribution class
    import py2exe
except ImportError:
    # ignore when py2exe is not installed
    pass
from distutils.core import Distribution

AppVersion = "5.2"
AppName = "LinkChecker"

# py2exe options for windows .exe packaging
py2exe_options = dict(
    packages=["encodings"],
    excludes=['doctest', 'unittest', 'optcomplete', 'Tkinter', 'win32com.gen_py'],
    # add sip so that PyQt4 works
    # add PyQt4.QtSql so that sqlite neede by QHelpCollection works
    includes=["sip", "PyQt4.QtSql"],
    compressed=1,
    optimize=2,
)

def normpath (path):
    """Norm a path name to platform specific notation."""
    return os.path.normpath(path)


def cnormpath (path):
    """Norm a path name to platform specific notation."""
    path = normpath(path)
    if os.name == 'nt':
        # replace slashes with backslashes
        path = path.replace("/", "\\")
    if not os.path.isabs(path):
        path= normpath(os.path.join(sys.prefix, path))
    return path


class MyInstallLib (install_lib, object):

    def install (self):
        """Install the generated config file."""
        outs = super(MyInstallLib, self).install()
        infile = self.create_conf_file()
        outfile = os.path.join(self.install_dir, os.path.basename(infile))
        self.copy_file(infile, outfile)
        outs.append(outfile)
        return outs

    def create_conf_file (self):
        cmd_obj = self.distribution.get_command_obj("install")
        cmd_obj.ensure_finalized()
        # we have to write a configuration file because we need the
        # <install_data> directory (and other stuff like author, url, ...)
        # all paths are made absolute by cnormpath()
        data = []
        for d in ['purelib', 'platlib', 'lib', 'headers', 'scripts', 'data']:
            attr = 'install_%s' % d
            if cmd_obj.root:
                # cut off root path prefix
                cutoff = len(cmd_obj.root)
                # don't strip the path separator
                if cmd_obj.root.endswith(os.sep):
                    cutoff -= 1
                val = getattr(cmd_obj, attr)[cutoff:]
            else:
                val = getattr(cmd_obj, attr)
            if attr == 'install_data':
                cdir = os.path.join(val, "share", "linkchecker")
                data.append('config_dir = %r' % cnormpath(cdir))
            elif attr == 'install_lib':
                if cmd_obj.root:
                    _drive, tail = os.path.splitdrive(val)
                    if tail.startswith(os.sep):
                        tail = tail[1:]
                    self.install_lib = os.path.join(cmd_obj.root, tail)
                else:
                    self.install_lib = val
            data.append("%s = %r" % (attr, cnormpath(val)))
        self.distribution.create_conf_file(data, directory=self.install_lib)
        return self.distribution.get_conf_filename(self.install_lib)

    def get_outputs (self):
        """Add the generated config file to the list of outputs."""
        outs = super(MyInstallLib, self).get_outputs()
        outs.append(self.distribution.get_conf_filename(self.install_lib))
        return outs


class MyInstallData (install_data, object):
    """Handle locale files and permissions."""

    def run (self):
        """Adjust permissions on POSIX systems."""
        self.add_message_files()
        super(MyInstallData, self).run()
        self.fix_permissions()

    def add_message_files (self):
        """Add locale message files to data_files list."""
        for (src, dst) in list_message_files(self.distribution.get_name()):
            dstdir = os.path.dirname(dst)
            self.data_files.append((dstdir, [os.path.join("build", dst)]))

    def fix_permissions (self):
        """Set correct read permissions on POSIX systems. Might also
        be possible by setting umask?"""
        if os.name == 'posix' and not self.dry_run:
            # Make the data files we just installed world-readable,
            # and the directories world-executable as well.
            for path in self.get_outputs():
                mode = os.stat(path)[stat.ST_MODE]
                if stat.S_ISDIR(mode):
                    mode |= 011
                mode |= 044
                os.chmod(path, mode)


class MyDistribution (Distribution, object):
    """Custom distribution class generating config file."""

    def __init__ (self, attrs):
        super(MyDistribution, self).__init__(attrs)
        self.console = ['linkchecker']
        self.windows = [{
            "script": "linkchecker-gui",
            "icon_resources": [(1, "doc/html/favicon.ico")],
        }]


    def run_commands (self):
        """Generate config file and run commands."""
        cwd = os.getcwd()
        data = []
        data.append('config_dir = %r' % os.path.join(cwd, "config"))
        data.append("install_data = %r" % cwd)
        data.append("install_scripts = %r" % cwd)
        self.create_conf_file(data)
        super(MyDistribution, self).run_commands()

    def get_conf_filename (self, directory):
        """Get name for config file."""
        return os.path.join(directory, "_%s_configdata.py" % self.get_name())

    def create_conf_file (self, data, directory=None):
        """Create local config file from given data (list of lines) in
        the directory (or current directory if not given)."""
        data.insert(0, "# this file is automatically created by setup.py")
        data.insert(0, "# -*- coding: iso-8859-1 -*-")
        if directory is None:
            directory = os.getcwd()
        filename = self.get_conf_filename(directory)
        # add metadata
        metanames = ("name", "version", "author", "author_email",
                     "maintainer", "maintainer_email", "url",
                     "license", "description", "long_description",
                     "keywords", "platforms", "fullname", "contact",
                     "contact_email", "fullname")
        for name in metanames:
            method = "get_" + name
            val = getattr(self.metadata, method)()
            if isinstance(val, str):
                val = unicode(val)
            cmd = "%s = %r" % (name, val)
            data.append(cmd)
        # write the config file
        data.append('appname = "LinkChecker"')
        util.execute(write_file, (filename, data),
                     "creating %s" % filename, self.verbose>=1, self.dry_run)


def cc_run (args):
    """Run the C compiler with a simple main program.

    @return: successful exit flag
    @rtype: bool
    """
    prog = "int main(){}\n"
    pipe = subprocess.Popen(args,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    pipe.communicate(input=prog)
    if os.WIFEXITED(pipe.returncode):
        return os.WEXITSTATUS(pipe.returncode) == 0
    return False


def cc_supports_option (cc, option):
    """Check if the given C compiler supports the given option.

    @return: True if the compiler supports the option, else False
    @rtype: bool
    """
    return cc_run([cc[0], "-E", option, "-"])


def cc_remove_option (compiler, option):
    for optlist in (compiler.compiler, compiler.compiler_so):
        if option in optlist:
            optlist.remove(option)


class MyBuildExt (build_ext, object):
    """Custom build extension command."""

    def build_extensions (self):
        """Add -std=gnu99 to build options if supported."""
        # For gcc >= 3 we can add -std=gnu99 to get rid of warnings.
        extra = []
        if self.compiler.compiler_type == 'unix':
            option = "-std=gnu99"
            if cc_supports_option(self.compiler.compiler, option):
                extra.append(option)
                if platform.machine() == 'm68k':
                    # work around ICE on m68k machines in gcc 4.0.1
                    cc_remove_option(self.compiler, "-O3")
        # First, sanity-check the 'extensions' list
        self.check_extensions_list(self.extensions)
        for ext in self.extensions:
            for opt in extra:
                if opt not in ext.extra_compile_args:
                    ext.extra_compile_args.append(opt)
            self.build_extension(ext)


def list_message_files (package, suffix=".po"):
    """Return list of all found message files and their installation paths."""
    for fname in glob.glob("po/*" + suffix):
        # basename (without extension) is a locale name
        localename = os.path.splitext(os.path.basename(fname))[0]
        yield (fname, os.path.join(
            "share", "locale", localename, "LC_MESSAGES", "%s.mo" % package))


def check_manifest ():
    """Snatched from roundup.sf.net.
    Check that the files listed in the MANIFEST are present when the
    source is unpacked."""
    try:
        f = open('MANIFEST')
    except Exception:
        print '\n*** SOURCE WARNING: The MANIFEST file is missing!'
        return
    try:
        manifest = [l.strip() for l in f.readlines()]
    finally:
        f.close()
    err = [line for line in manifest if not os.path.exists(line)]
    if err:
        n = len(manifest)
        print '\n*** SOURCE WARNING: There are files missing (%d/%d found)!'%(
            n-len(err), n)
        print 'Missing:', '\nMissing: '.join(err)


class MyBuild (build, object):
    """Custom build command."""

    def build_message_files (self):
        """For each po/*.po, build .mo file in target locale directory."""
        # msgfmt.py is in the po/ subdirectory
        sys.path.append('po')
        import msgfmt
        for (src, dst) in list_message_files(self.distribution.get_name()):
            build_dst = os.path.join("build", dst)
            self.mkpath(os.path.dirname(build_dst))
            self.announce("Compiling %s -> %s" % (src, build_dst))
            msgfmt.make(src, build_dst)

    def run (self):
        check_manifest()
        self.build_message_files()
        build.run(self)


class MyClean (clean, object):
    """Custom clean command."""

    def run (self):
        if self.all:
            # remove share directory
            directory = os.path.join("build", "share")
            if os.path.exists(directory):
                remove_tree(directory, dry_run=self.dry_run)
            else:
                log.warn("'%s' does not exist -- can't clean it", directory)
        clean.run(self)


class MySdist (sdist, object):
    """Custom sdist command."""

    def get_file_list (self):
        """Add MANIFEST to the file list."""
        super(MySdist, self).get_file_list()
        self.filelist.append("MANIFEST")


# global include dirs
include_dirs = []
# global macros
define_macros = []
# compiler args
extra_compile_args = []
# library directories
library_dirs = []
# libraries
libraries = []
# scripts
scripts = ['linkchecker', 'linkchecker-gui']

if os.name == 'nt':
    # windows does not have unistd.h
    define_macros.append(('YY_NO_UNISTD_H', None))
else:
    extra_compile_args.append("-pedantic")

myname = "Bastian Kleineidam"
myemail = "calvin@users.sourceforge.net"

data_files = [
    ('share/linkchecker',
        ['config/linkcheckerrc', 'config/logging.conf',
        'doc/html/lccollection.qhc', 'doc/html/lcdoc.qch']),
    ('share/linkchecker/examples',
        ['cgi-bin/lconline/leer.html.en',
         'cgi-bin/lconline/leer.html.de',
         'cgi-bin/lconline/index.html',
         'cgi-bin/lconline/lc_cgi.html.en',
         'cgi-bin/lconline/lc_cgi.html.de',
         'cgi-bin/lconline/check.js',
         'cgi-bin/lc.cgi',
         'cgi-bin/lc.fcgi',
         'config/linkchecker.apache2.conf',
        ]),
]

if os.name == 'posix':
    data_files.append(('share/man/man1', ['doc/en/linkchecker.1', 'doc/en/linkchecker-gui.1']))
    data_files.append(('share/man/man5', ['doc/en/linkcheckerrc.5']))
    data_files.append(('share/man/de/man1', ['doc/de/linkchecker.1', 'doc/de/linkchecker-gui.1']))
    data_files.append(('share/man/de/man5', ['doc/de/linkcheckerrc.5']))
    data_files.append(('share/linkchecker/examples',
              ['config/linkchecker-completion',
               'doc/examples/check_blacklist.sh',
               'doc/examples/check_for_x_errors.sh',
               'doc/examples/check_urls.sh',]))


class InnoScript:
    def __init__(self, lib_dir, dist_dir, windows_exe_files=[],
                 console_exe_files=[], service_exe_files=[],
                 comserver_files=[], lib_files=[]):
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir[-1] in "\\/":
            self.dist_dir += "\\"
        self.name = AppName
        self.version = AppVersion
        self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
        self.console_exe_files = [self.chop(p) for p in console_exe_files]
        self.service_exe_files = [self.chop(p) for p in service_exe_files]
        self.comserver_files = [self.chop(p) for p in comserver_files]
        self.lib_files = [self.chop(p) for p in lib_files]

    def chop(self, pathname):
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]

    def create(self, pathname="dist\\omt.iss"):
        self.pathname = pathname
        ofi = self.file = open(pathname, "w")
        print >> ofi, "; WARNING: This script has been created by py2exe. Changes to this script"
        print >> ofi, "; will be overwritten the next time py2exe is run!"
        print >> ofi, r"[Setup]"
        print >> ofi, r"AppName=%s" % self.name
        print >> ofi, r"AppVerName=%s %s" % (self.name, self.version)
        print >> ofi, r"DefaultDirName={pf}\%s" % self.name
        print >> ofi, r"DefaultGroupName=%s" % self.name
        print >> ofi, r"OutputBaseFilename=%s-%s" % (self.name, self.version)
        print >> ofi, r"OutputDir=."
        print >> ofi

        files = self.windows_exe_files + \
                self.console_exe_files + \
                self.service_exe_files + \
                self.comserver_files + \
                self.lib_files
        print >> ofi, r"[Files]"
        for path in files:
            print >> ofi, r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion' % (path, os.path.dirname(path))
        print >> ofi

        print >> ofi, r"[Icons]"
        for path in self.windows_exe_files:
            print >> ofi, r'Name: "{group}\%s"; Filename: "{app}\%s"' % \
                  (self.name, path)
        print >> ofi, 'Name: "{group}\Uninstall %s"; Filename: "{uninstallexe}"' % self.name

    def compile(self):
        import ctypes
        res = ctypes.windll.shell32.ShellExecuteA(0, "compile",
            self.pathname, None, None, 0)
        if res < 32:
            raise RuntimeError, "ShellExecute failed, error %d" % res

try:
    from py2exe.build_exe import py2exe as py2exe_build
    class MyPy2exe (py2exe_build):
        """First builds the exe file(s), then creates a Windows installer.
        You need InnoSetup for it."""

        def run (self):
            # First, let py2exe do it's work.
            py2exe_build.run(self)
            lib_dir = self.lib_dir
            dist_dir = self.dist_dir
            # Copy needed sqlite plugin files to distribution directory.
            import PyQt4
            src = os.path.join(os.path.dirname(PyQt4.__file__), "plugins", "sqldrivers")
            dst = os.path.join(dist_dir, "sqldrivers")
            copy_tree(src, dst)
            for path in os.listdir(dst):
                self.lib_files.append(os.path.join(dst, path))
            # create the Installer, using the files py2exe has created.
            script = InnoScript(lib_dir, dist_dir, self.windows_exe_files,
                self.console_exe_files, self.service_exe_files,
                self.comserver_files, self.lib_files)
            print "*** creating the inno setup script***"
            script.create()
            print "*** compiling the inno setup script***"
            script.compile()
except ImportError:
    class MyPy2exe: pass


class MyRegister (register, object):

    def build_post_data(self, action):
        """Force application name to lower case."""
        data = super(MyRegister, self).build_post_data(action)
        data['name'] = data['name'].lower()
        return data


setup (
    name = AppName,
    version = AppVersion,
    description = "check websites and HTML documents for broken links",
    keywords = "link,url,checking,verification",
    author = myname,
    author_email = myemail,
    maintainer = myname,
    maintainer_email = myemail,
    url = "http://linkchecker.sourceforge.net/",
    download_url="http://sourceforge.net/project/showfiles.php?group_id=1913",
    license = "GPL",
    long_description = """Linkchecker features:
o recursive and multithreaded checking
o output in colored or normal text, HTML, SQL, CSV, XML or a sitemap
  graph in different formats
o HTTP/1.1, HTTPS, FTP, mailto:, news:, nntp:, Telnet and local file
  links support
o restrict link checking with regular expression filters for URLs
o proxy support
o username/password authorization for HTTP, FTP and Telnet
o honors robots.txt exclusion protocol
o Cookie support
o HTML and CSS syntax check
o Antivirus check
o a command line interface
o a (Fast)CGI web interface (requires HTTP server)
""",
    distclass = MyDistribution,
    cmdclass = {
        'install_lib': MyInstallLib,
        'install_data': MyInstallData,
        'build_ext': MyBuildExt,
        'build': MyBuild,
        'clean': MyClean,
        'sdist': MySdist,
        'py2exe': MyPy2exe,
        'register': MyRegister,
    },
    packages = [
        'linkcheck', 'linkcheck.logger', 'linkcheck.checker',
        'linkcheck.director', 'linkcheck.configuration', 'linkcheck.cache',
        'linkcheck.htmlutil', 'linkcheck.dns', 'linkcheck.dns.rdtypes',
        'linkcheck.dns.rdtypes.ANY', 'linkcheck.dns.rdtypes.IN',
        'linkcheck.HtmlParser', 'linkcheck.network', 'linkcheck.gui',
    ],
    ext_modules = [
        Extension('linkcheck.HtmlParser.htmlsax',
            sources = [
                'linkcheck/HtmlParser/htmllex.c',
                'linkcheck/HtmlParser/htmlparse.c',
                'linkcheck/HtmlParser/s_util.c',
            ],
            extra_compile_args = extra_compile_args,
            library_dirs = library_dirs,
            libraries = libraries,
            define_macros = define_macros + [('YY_NO_INPUT', None)],
            include_dirs = include_dirs + [normpath("linkcheck/HtmlParser")],
        ),
        Extension("linkcheck.network._network",
            sources = ["linkcheck/network/_network.c",],
            extra_compile_args = extra_compile_args,
            library_dirs = library_dirs,
            libraries = libraries,
            define_macros = define_macros,
            include_dirs = include_dirs,
        ),
    ],
    scripts = scripts,
    data_files = data_files,
    classifiers = [
        'Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Programming Language :: C',
    ],
    options = {"py2exe": py2exe_options},
)
