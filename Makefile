# This Makefile is only used by developers.
PYVER:=2.7
PYTHON:=python$(PYVER)
VERSION:=$(shell $(PYTHON) setup.py --version)
PLATFORM:=$(shell $(PYTHON) -c "from distutils.util import get_platform; print get_platform()")
FILESCHECK_URL:=http://localhost/~calvin/
PYTHONSRC:=${HOME}/src/cpython-hg/Lib
#PYTHONSRC:=/usr/lib/$(PYTHON)
PY_FILES_DIRS:=linkcheck tests *.py linkchecker linkchecker-gui cgi-bin config doc
TESTS ?= tests/
# set test options, eg. to "--nologcapture"
TESTOPTS=
PAGER ?= less
# build dir for debian package
BUILDDIR:=$(HOME)/packages/official
DEB_ORIG_TARGET:=$(BUILDDIR)/linkchecker_$(VERSION).orig.tar.bz2
# original dnspython repository module
DNSPYTHON:=$(HOME)/src/dnspython-git
# options to run the pep8 utility
PEP8OPTS:=--repeat --ignore=E211,E501,E225,E301,E302,E241 \
   --exclude="gzip2.py,httplib2.py,robotparser2.py,reindent.py"
PY2APPOPTS ?=
ifeq ($(shell uname),Darwin)
  NUMPROCESSORS:=$(shell sysctl -a | grep machdep.cpu.core_count | cut -d " " -f 2)
else
  NUMPROCESSORS:=$(shell grep -c processor /proc/cpuinfo)
endif


.PHONY: all
all:
	@echo "Read the file doc/install.txt to see how to build and install this package."

.PHONY: clean
clean:
	-$(PYTHON) setup.py clean --all
	rm -f linkchecker-out.* *-stamp*
	$(MAKE) -C po clean
	$(MAKE) -C doc/html clean
	$(MAKE) -C linkcheck/HtmlParser clean
	rm -f linkcheck/network/_network*.so
	find . -name '*.py[co]' -exec rm -f {} \;

.PHONY: distclean
distclean: clean cleandeb
	rm -rf build dist linkchecker.egg-info
	rm -f _LinkChecker_configdata.py MANIFEST Packages.gz
# clean aborted dist builds and -out files
	rm -f linkchecker-out* linkchecker.prof
	rm -rf LinkChecker-$(VERSION)
	rm -rf coverage dist-stamp python-build-stamp*

.PHONY: cleandeb
cleandeb:
	rm -rf debian/linkchecker debian/tmp
	rm -f debian/*.debhelper debian/{files,substvars}
	rm -f configure-stamp build-stamp

MANIFEST: MANIFEST.in setup.py
	$(PYTHON) setup.py sdist --manifest-only

.PHONY: locale
locale:
	$(MAKE) -C po

# to build in the current directory
.PHONY: localbuild
localbuild: MANIFEST
	$(MAKE) -C doc/html
	$(MAKE) -C linkcheck/HtmlParser
	$(PYTHON) setup.py build
	cp -f build/lib.$(PLATFORM)-$(PYVER)/linkcheck/HtmlParser/htmlsax*.so linkcheck/HtmlParser
	cp -f build/lib.$(PLATFORM)-$(PYVER)/linkcheck/network/_network*.so linkcheck/network

.PHONY: deb_orig
deb_orig:
	if [ ! -e $(DEB_ORIG_TARGET) ]; then \
	  $(MAKE) dist-stamp && \
	  cp dist/LinkChecker-$(VERSION).tar.bz2 $(DEB_ORIG_TARGET); \
	fi

.PHONY: upload
upload:
	rsync -avP -e ssh dist/* calvin,linkchecker@frs.sourceforge.net:/home/frs/project/l/li/linkchecker/$(VERSION)/


.PHONY: release
release: distclean releasecheck dist-stamp sign_distfiles upload
	git tag v$(VERSION)
	@echo "Updating LinkChecker Homepage..."
	sed -i -e "s/version = '.*'/version = '$(VERSION)'/" ~/public_html/linkchecker.sf.net/source/conf.py
	$(MAKE) -C ~/public_html/linkchecker.sf.net update upload
	@echo "Register at Python Package Index..."
	$(PYTHON) setup.py register
	wget -O - http://pypants.org/projects/linkchecker/update/ > /dev/null
	freshmeat-submit < linkchecker.freshmeat

.PHONY: chmod
chmod:
	-chmod -R a+rX,u+w,go-w -- *
	find . -type d -exec chmod 755 {} \;

.PHONY: dist
dist: locale MANIFEST chmod
	$(PYTHON) setup.py sdist --formats=bztar
# no rpm buildable with bdist_rpm, presumable due to this bug:
# https://bugzilla.redhat.com/show_bug.cgi?id=236535
# too uninvolved to fix it

dist-stamp: changelog
	$(MAKE) dist
	touch $@

# Build OSX installer
.PHONY: app
app: distclean localbuild chmod
	$(PYTHON) setup.py py2app $(PY2APPOPTS)

# The check programs used here are mostly local scripts on my private system.
# So for other developers there is no need to execute this target.
.PHONY: check
check:
	[ ! -d .svn ] || check-nosvneolstyle -v
	check-copyright
	check-pofiles -v
	py-tabdaddy
	py-unittest2-compat tests/
	$(MAKE) doccheck
	$(MAKE) pyflakes

doccheck:
	py-check-docstrings --force linkcheck/HtmlParser linkcheck/checker \
	  linkcheck/cache linkcheck/configuration linkcheck/director \
	  linkcheck/htmlutil linkcheck/logger linkcheck/network \
	  linkcheck/bookmarks \
	  linkcheck/gui/__init__.py \
	  linkcheck/gui/checker.py \
	  linkcheck/gui/contextmenu.py \
	  linkcheck/gui/debug.py \
	  linkcheck/gui/editor.py \
	  linkcheck/gui/editor_qsci.py \
	  linkcheck/gui/editor_qt.py \
	  linkcheck/gui/lineedit.py \
	  linkcheck/gui/help.py \
	  linkcheck/gui/logger.py \
	  linkcheck/gui/options.py \
	  linkcheck/gui/properties.py \
	  linkcheck/gui/settings.py \
	  linkcheck/gui/statistics.py \
	  linkcheck/gui/syntax.py \
	  linkcheck/gui/updater.py \
	  linkcheck/gui/urlmodel.py \
	  linkcheck/gui/urlsave.py \
	  linkcheck/__init__.py \
	  linkcheck/ansicolor.py \
	  linkcheck/clamav.py \
	  linkcheck/containers.py \
	  linkcheck/cookies.py \
	  linkcheck/decorators.py \
	  linkcheck/dummy.py \
	  linkcheck/fileutil.py \
	  linkcheck/ftpparse.py \
	  linkcheck/geoip.py \
	  linkcheck/httputil.py \
	  linkcheck/i18n.py \
	  linkcheck/lc_cgi.py \
	  linkcheck/lock.py \
	  linkcheck/log.py \
	  linkcheck/mem.py \
	  linkcheck/robotparser2.py \
	  linkcheck/socketutil.py \
	  linkcheck/strformat.py \
	  linkcheck/threader.py \
	  linkcheck/trace.py \
	  linkcheck/updater.py \
	  linkcheck/url.py \
	  linkcheck/winutil.py \
	  *.py

filescheck:
	for out in text html gml sql csv xml gxml dot; do \
	  ./linkchecker -o$$out -F$$out --complete -r1 -C $(FILESCHECK_URL) || exit 1; \
	done

update-copyright:
	update-copyright --holder="Bastian Kleineidam"

.PHONY: releasecheck
releasecheck: check
	@if egrep -i "xx\.|xxxx|\.xx" doc/changelog.txt > /dev/null; then \
	  echo "Could not release: edit doc/changelog.txt release date"; false; \
	fi
	@if ! grep "Version: $(VERSION)" linkchecker.freshmeat > /dev/null; then \
	  echo "Could not release: edit linkchecker.freshmeat version"; false; \
	fi
#	$(MAKE) -C doc test

.PHONY: sign_distfiles
sign_distfiles:
	for f in $(shell find dist -name *.bz2 -o -name *.exe -o -name *.zip -o -name *.dmg); do \
	  [ -f $${f}.asc ] || gpg --detach-sign --armor $$f; \
	done

.PHONY: test
test:	localbuild
	$(PYTHON) $(shell which nosetests) --processes=$(NUMPROCESSORS) \
	  -v -m "^test_.*" $(TESTOPTS) $(TESTS)

.PHONY: pyflakes
pyflakes:
	pyflakes --force $(PY_FILES_DIRS) 2>&1 | \
          grep -v "redefinition of unused 'linkcheck'" | \
          grep -v "undefined name '_'" | \
	  grep -v "undefined name '_n'" | cat

.PHONY: pep8
pep8:
	pep8 $(PEP8OPTS) $(PY_FILES_DIRS)

.PHONY: reindent
reindent:
	$(PYTHON) config/reindent.py -r -v linkcheck

# Compare custom Python files with the original ones from subversion.
.PHONY: diff
diff:
	@for f in gzip robotparser httplib; do \
	  echo "Comparing $${f}.py"; \
	  diff -u linkcheck/$${f}2.py $(PYTHONSRC)/$${f}.py | $(PAGER); \
	done

# Compare dnspython files with the ones from upstream repository
.PHONY: dnsdiff
dnsdiff:
	@(for d in dns tests; do \
	  diff -BurN --exclude=*.pyc third_party/dnspython/$$d $(DNSPYTHON)/$$d; \
	done) | $(PAGER)

.PHONY: changelog
changelog:
	sftrack_changelog linkchecker calvin@users.sourceforge.net doc/changelog.txt $(DRYRUN)

.PHONY: gui
gui:
	$(MAKE) -C linkcheck/gui

.PHONY: count
count:
	@sloccount linkchecker linkchecker-gui linkcheck | grep "Total Physical Source Lines of Code"

# run eclipse ide
.PHONY: ide
ide:
	eclipse-3.6 -data $(CURDIR)/..
