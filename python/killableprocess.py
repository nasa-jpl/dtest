# killableprocess - subprocesses which can be reliably killed
# from http://svn.smedbergs.us/python-processes/trunk/killableprocess.py
#
# (Abhi) This subclasses supprocess.Popen and adds a timeout argument to
# its wait() method. Apparently the timeout only works on the main
# thread. python 3 I believe adds the timeout option to the subprocess
# Popen class directly.
#
# Parts of this module are copied from the subprocess.py file contained
# in the Python distribution.
#
# Copyright (c) 2003-2004 by Peter Astrand <astrand@lysator.liu.se>
#
# Additions and modifications written by Benjamin Smedberg
# <benjamin@smedbergs.us> are Copyright (c) 2006 by the Mozilla Foundation
# <http://www.mozilla.org/>
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and
# its associated documentation for any purpose and without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of the
# author not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission.
#
# THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
# WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""killableprocess - Subprocesses which can be reliably killed.

It adds a timeout argument to wait() for a limited period of time before
forcefully killing the process.

"""
from __future__ import division
from __future__ import print_function

from __future__ import absolute_import

import os
import sys
import signal
import subprocess
import time


class TimeoutExpired(Exception):
    """Raised if timeout occurs."""

    def __init__(self, seconds):
        self.seconds = seconds

    def __str__(self):
        return "TimeoutExpired({})".format(self.seconds)


def do_nothing(*args):
    pass


class Popen(subprocess.Popen):

    # Override __init__ to set a preexec_fn

    def __init__(self, *args, **kwargs):
        if len(args) >= 7:
            raise Exception("Arguments preexec_fn and after must be passed by " "keyword.")

        real_preexec_fn = kwargs.pop("preexec_fn", None)

        def setpgid_preexec_fn():
            os.setpgid(0, 0)
            if real_preexec_fn:
                apply(real_preexec_fn)

        kwargs["preexec_fn"] = setpgid_preexec_fn

        subprocess.Popen.__init__(self, *args, **kwargs)

    def kill(self, group=True):
        """Kill the process.

        If group=True, all sub-processes will also be killed.

        """
        if group:
            os.killpg(self.pid, signal.SIGKILL)
        else:
            os.kill(self.pid, signal.SIGKILL)
        self.returncode = -9

    def wait(self, timeout=-1, group=True):
        """Wait for the process to terminate.

        Returns returncode attribute.
        If timeout seconds are reached and the process has not terminated,
        it will be forcefully killed. If timeout is -1, wait will not
        time out.

        """

        if self.returncode is not None:
            return self.returncode

        if timeout == -1:
            subprocess.Popen.wait(self)
            return self.returncode

        starttime = time.time()

        # Make sure there is a signal handler for SIGCHLD installed
        oldsignal = signal.signal(signal.SIGCHLD, do_nothing)

        while time.time() < starttime + timeout - 0.01:
            pid, sts = os.waitpid(self.pid, os.WNOHANG)
            if pid != 0:
                self._handle_exitstatus(sts)
                signal.signal(signal.SIGCHLD, oldsignal)
                return self.returncode

            # time.sleep is interrupted by signals (good!)
            newtimeout = timeout - time.time() + starttime
            if sys.version_info[0] >= 3:
                # In python 3, need smaller times
                # (maybe signal interruption is not working?)
                newtimeout = min(0.5, newtimeout)
            time.sleep(newtimeout)

        self.kill(group)
        signal.signal(signal.SIGCHLD, oldsignal)
        subprocess.Popen.wait(self)

        raise TimeoutExpired(timeout)
