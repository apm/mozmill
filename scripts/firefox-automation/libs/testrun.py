# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is MozMill automation code.
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Henrik Skupin <hskupin@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

mozmill_tests_repository = "http://hg.mozilla.org/qa/mozmill-tests"

# Global modules
import os, sys
import datetime
import shutil
import tempfile

# Local modules
import application
import install
import mozmill_wrapper
import repository

class TestRun(object):
    """ Class to execute a Mozmill test-run. """

    def __init__(self, *args, **kwargs):
        self.addon_list = [ ]
        self.debug = False
        self.logfile = None
        self.report_url = None
        self.repository_path = ""
        self.repository_url = mozmill_tests_repository
        self.restart_tests = False
        self.test_path = ""

    def _get_addon_list(self):
        """ Returns the location of add-ons which will be installed. """
        return self._addons

    def _set_addon_list(self, value):
        """ Sets the location of add-ons which will be installed. """
        self._addons = value

    addon_list = property(_get_addon_list, _set_addon_list, None)

    def _get_binaries(self):
        """ Returns the list of binaries to test. """
        return self._binaries

    def _set_binaries(self, value):
        """ Sets the list of binaries to test. """
        self._binaries = [ ]

        if value is None:
            return

        for path in value:
            if not os.path.exists(path):
                raise Exception("Path '%s' cannot be found." % (path))

            # Check if it's an installer or an already installed build
            if self.is_installer(path) or application.is_app_folder(path):
                self._binaries.append(os.path.abspath(path))
                continue
            # Otherwise recursivily scan the folder and add existing files
            for root, dirs, files in os.walk(path):
                for file in files:
                    if not file in [".DS_Store"] and self.is_installer(file):
                        self._binaries.append(os.path.abspath(os.path.join(root, file)))

    binaries = property(_get_binaries, _set_binaries, None)

    def _get_debug(self):
        """ Returns the enabled state of the debug mode. """
        return self._debug

    def _set_debug(self, value):
        """ Sets the enabled state of the debug mode. """
        self._debug = value

    debug = property(_get_debug, _set_debug, None)

    def _get_logfile(self):
        """ Returns the path of the log file. """
        return self._logfile

    def _set_logfile(self, value):
        """ Sets the path of the log file. """
        self._logfile = value

    logfile = property(_get_logfile, _set_logfile, None)

    def _get_report_url(self):
        """ Returns the URL of the report server. """
        return self._report_url

    def _set_report_url(self, value):
        """ Sets the URL of the report server. """
        self._report_url = value

    report_url = property(_get_report_url, _set_report_url, None)

    def _get_repository_path(self):
        """ Returns the local location of the repository. """
        return self._repository_path

    def _set_repository_path(self, value):
        """ Sets the local location of the repository. """
        self._repository_path = value

    repository_path = property(_get_repository_path, _set_repository_path)

    def _get_repository_url(self):
        """ Returns the remote location of the repository. """
        return self._repository_url

    def _set_repository_url(self, value):
        """ Sets the remote location of the repository. """
        self._repository_url = value

    repository_url = property(_get_repository_url, _set_repository_url)

    def _get_restart_tests(self):
        """ Returns if a restart test-run has to be executed. """
        return self._restart_tests

    def _set_restart_tests(self, value):
        """ Sets if a restart test-run has to be executed. """
        self._restart_tests = value

    restart_tests = property(_get_restart_tests, _set_restart_tests)

    def _get_test_path(self):
        """ Returns the relative test path inside the repository. """
        return self._test_path

    def _set_test_path(self, value):
        """ Sets the relative test path inside the repository. """
        self._test_path = value

    test_path = property(_get_test_path, _set_test_path)

    def cleanup_binary(self, binary, *args, **kwargs):
        """ Remove the build when it has been installed before. """
        if self.is_installer(binary):
            install.Installer().uninstall(self._folder)

    def cleanup_repository(self, *args, **kwargs):
        """ Removes the local version of the repository. """
        self._repository.remove()

    def clone_repository(self, *args, **kwargs):
        """ Clones the repository to a local temporary location. """
        try:
            self.repository_path = tempfile.mkdtemp(".mozmill-tests")
            self._repository = repository.Repository(self.repository_url,
                                                     self.repository_path)
            self._repository.clone()
        except Exception, e:
            raise Exception("Failure in setting up the mozmill-tests repository. " +
                            e.message)

    def is_installer(self, path):
        """ Checks if a binary is an installer. """
        try:
            return os.path.splitext(path)[1] in (".bz2", ".dmg", ".exe", ".zip")
        except:
            return False

    def prepare_binary(self, binary, *args, **kwargs):
        """ Prepare the binary for the test run. """

        if self.is_installer(binary):
            install_path = tempfile.mkdtemp(".binary")
            self._folder = install.Installer().install(binary, install_path)
            self._application = application.get_binary(self._folder)
        else:
            folder = os.path.dirname(binary)
            self._folder = folder if not os.path.isdir(binary) else binary
            self._application = binary

    def prepare_repository(self, *args, **kwargs):
        """ Update the repository to the needed branch. """

        # Retrieve the Gecko branch from the application.ini file
        ini = application.ApplicationIni(self._folder)
        repository_url = ini.get('App', 'SourceRepository')

        # Update the mozmill-test repository to match the Gecko branch
        branch_name = self._repository.identify_branch(repository_url)
        self._repository.update(branch_name)

    def prepare_tests(self, *args, **kwargs):
        """ Preparation which has to be done before starting a test. """

        if self.restart_tests:
            self._mozmill = mozmill_wrapper.MozmillWrapperRestartCLI()
        else:
            self._mozmill = mozmill_wrapper.MozmillWrapperCLI()

        self._mozmill.addon_list = self.addon_list
        self._mozmill.binary = self._application
        self._mozmill.debug = self.debug
        self._mozmill.logfile = self.logfile
        self._mozmill.report_url = self.report_url
        self._mozmill.showerrors = True
        self._mozmill.test = os.path.join(self.repository_path, self.test_path)

    def run_tests(self, *args, **kwargs):
        """ Start the execution of the tests. """

        self.prepare_tests()
        self._mozmill.run()

    def run(self, *args, **kwargs):
        """ Run software update tests for all specified builds. """

        self.clone_repository()

        # Run tests for each binary
        for binary in self.binaries:
            try:
                self.prepare_binary(binary)
                self.prepare_repository()
                self.run_tests()
            except Exception, e:
                print e.message
            finally:
                self.cleanup_binary(binary)

        self.cleanup_repository()

class BftTestRun(TestRun):
    """ Class to execute a Firefox BFT test-run """

    def run_tests(self, *args, **kwargs):
        """ Execute the normal and restart tests in sequence. """

        try:
            self.restart_tests = False
            self.test_path = os.path.join('firefox')
            TestRun.run_tests(self)
        except Exception, e:
            print e

        try:
            self.restart_tests = True
            self.test_path = os.path.join('firefox','restartTests')
            TestRun.run_tests(self)
        except Exception, e:
            print e

class UpdateTestRun(TestRun):
    """ Class to execute software update tests """

    def __init__(self, *args, **kwargs):
        TestRun.__init__(self, *args, **kwargs)

        self.channel = None
        self.no_fallback = False
        self.results = [ ]

    def _get_channel(self):
        """ Returns the current update channel. """
        return self._channel

    def _set_channel(self, value):
        """ Sets the current update channel. """
        self._channel = value

    channel = property(_get_channel, _set_channel, None)

    def _get_no_fallback(self):
        """ Returns the current update no_fallback. """
        return self._no_fallback

    def _set_no_fallback(self, value):
        """ Sets the current update no_fallback. """
        self._no_fallback = value

    no_fallback = property(_get_no_fallback, _set_no_fallback, None)

    def _get_results(self):
        """ Returns the update results. """
        return self._results

    def _set_results(self, value):
        """ Sets the update results. """
        self._results = value

    results = property(_get_results, _set_results, None)

    def build_wiki_entry(self, results):
        entry = "* %s => %s, %s, %s, %s, %s, %s, '''%s'''\n" \
                "** %s ID:%s\n** %s ID:%s\n" \
                "** Passed %d :: Failed %d :: Skipped %d\n" % \
                (results.get("preVersion", ""),
                 results.get("postVersion", ""),
                 results.get("type"),
                 results.get("preLocale", ""),
                 results.get("updateType", "unknown type"),
                 results.get("channel", ""),
                 datetime.date.today(),
                 "PASS" if results.get("success", False) else "FAIL",
                 results.get("preUserAgent", ""), results.get("preBuildId", ""),
                 results.get("postUserAgent", ""), results.get("postBuildId", ""),
                 len(results.get("passes")),
                 len(results.get("fails")),
                 len(results.get("skipped")))
        return entry

    def prepare_binary(self, binary, *args, **kwargs):
        TestRun.prepare_binary(self, binary, *args, **kwargs)

        # If a fallback update has to be performed, create a second copy
        # of the application to avoid running the installer twice
        if not self.no_fallback:
            try:
                self._backup_folder = tempfile.mkdtemp(".binary_backup")

                print "Creating backup of binary (%s => %s)" % (self._folder,
                                                                self._backup_folder)
                shutil.rmtree(self._backup_folder)
                shutil.copytree(self._folder, self._backup_folder)
            except Exception, e:
                print "Failure while creating the backup of the binary."

    def prepare_channel(self):
        update_channel = application.UpdateChannel()
        update_channel.folder = self._folder
    
        if self.channel is None:
            self.channel = update_channel.channel
        else:
            update_channel.channel = self.channel

    def prepare_tests(self, *args, **kwargs):
        self.prepare_channel()
        self.restart_tests = True

        TestRun.prepare_tests(self)
        self._mozmill.persisted["channel"] = self.channel
        #XXX: remove temporary folder
        self._mozmill.test = os.path.join('/data','testing','mozmill','mozilla1.9.2', self.test_path)

    def restore_binary(self, *args, **kwargs):
        """ Restores the backup of the application binary. """

        try:
            print "Restoring backup of binary (%s => %s)" % (self._backup_folder,
                                                             self._folder)
            shutil.rmtree(self._folder)
            shutil.move(self._backup_folder, self._folder)
        except:
            print "Failure while restoring the backup of the binary."

    def run_tests(self, *args, **kwargs):
        """ Start the execution of the tests. """

        # Run direct update test
        direct_data = self.run_update_tests(False)
        direct_result = direct_data.get("success", False)
            
        # Restoring application backup and run fallback update tests
        if not self.no_fallback:
            self.restore_binary()

            # Run fallback update test
            fallback_data = self.run_update_tests(True)
            fallback_result = fallback_data.get("success", False)

        if not (direct_result and fallback_result):
            self.results.append(self.build_wiki_entry(direct_data))
        if not self.no_fallback:
            self.results.append(self.build_wiki_entry(fallback_data))

    def run_update_tests(self, is_fallback, *args, **kwargs):
        try:
            folder = 'testFallbackUpdate' if is_fallback else 'testDirectUpdate'
            self.test_path = os.path.join('firefox', 'softwareUpdate', folder)
            TestRun.run_tests(self)
        except Exception, e:
            print e
        finally:
            data = self._mozmill.persisted

            # If a Mozmill test fails the update has to be also marked as failed
            if self._mozmill.fails:
                data["success"] = False

            data["passes"] = self._mozmill.passes
            data["fails"] = self._mozmill.fails
            data["skipped"] = self._mozmill.skipped

            return data

    def run(self, *args, **kwargs):
        self.results = [ ]
        TestRun.run(self, *args, **kwargs)

        # Print results to the console
        print "\nResults:\n========"
        for result in self.results:
            print result