"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2023 Zahner-Elektrik GmbH & Co. KG

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import requests
import subprocess
import os
import logging
import time


class AnalysisConnection:
    """Class which manages the connection to the Zahner Analysis Software.

    The Zahner Analysis Software performs all calculations.
    The Python library communicates with the Zahner Analysis via a REST interface.

    Various optional settings are possible. In the standard configuration it is checked if a
    Zahner Analysis with server is running, if this is not the case the Zahner Analysis is automatically
    started and automatically closed again.

    :param ip: IP address under which the server is found. 127.0.0.1 if it is running on the same computer.
    :param port: Port of the server.
    :param tryToConnect: True to test if the Zahner Analysis Server is reachable.
    :param tryToStart: If tryToConnect is True and tryToStart is True, then the Zahner Analysis is tried to start under windows systems.
    :param onlineCheckUrl: This URL is used to check if the Zahner Analysis can be reached.
    :param apiKey: The key is used as a security feature to prevent others from accessing the Zahner Analysis.
    :param buffer_size: Optimization parameter: The buffer for incomming file uploads. If too small the server has to reallocate bigger amounts of memory more often. Bigger amount means more memory allocation even if not needed.
    :param keep_jobs: Number of finished fitting jobs to keep for the client to download results and check the status.
    :param timeToWaitForOnline: This is the time for which is waited until the Zahner Analysis is online after it has been started. This time varies depending on the speed of the computer.
    :param keepOpen: If this parameter is True, the Zahner Analysis will not be closed when it is no longer needed.
    """

    def __init__(
        self,
        ip="127.0.0.1",
        port=8081,
        tryToConnect=True,
        tryToStart=True,
        onlineCheckUrl="/id",
        apiKey="PyAnalysis",
        buffer_size=32768,
        keep_jobs=3,
        timeToWaitForOnline=10,
        keepOpen=False,
    ):
        self._ip = ip
        self._port = port
        self._ip = f"http://{self._ip}:{self._port}"
        self._onlineCheckUrl = onlineCheckUrl
        self._apiKey = apiKey
        self._subprocess = None
        self._keepOpen = keepOpen

        if tryToConnect:
            if self.isOnline() is False:
                if tryToStart:
                    self.tryToStartAnalysis(buffer_size, keep_jobs, timeToWaitForOnline)
        return

    def tryToStartAnalysis(self, buffer_size=32768, keep_jobs=3, timeToWaitForCheck=10):
        """Function which tries to start the Zahner Analysis.

        This function writes information with the logging module.

        :param buffer_size: Optimization parameter: The buffer for incomming file uploads. If too small the server has to reallocate bigger amounts of memory more often. Bigger amount means more memory allocation even if not needed.
        :param keep_jobs: Number of finished fitting jobs to keep for the client to download results and check the status.
        :param timeToWaitForOnline: This is the time for which is waited until the Zahner Analysis is online after it has been started. This time varies depending on the speed of the computer.
        """
        opened = False
        if os.name == "nt":
            # Try to start Zahner Analysis only on Windows.
            opened = True
            try:
                try:
                    logging.debug("Zahner Analysis 64 bit registry search")
                    import winreg

                    reg_key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        "SOFTWARE\\Zahner\\Analysis",
                        0,
                        winreg.KEY_READ,
                    )
                except:
                    logging.debug("Zahner Analysis 32 bit registry search")
                    reg_key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        "SOFTWARE\\Zahner\\Analysis",
                        0,
                        winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
                    )
                finally:
                    path = winreg.QueryValueEx(reg_key, "Path")[0]
                    reg_key.Close()

                path += " --remoteEval"
                path += f",port={self._port}"
                path += f",key={self._apiKey}"
                path += f",buffer_size={buffer_size}"
                path += f",keep_jobs={keep_jobs}"
                self._subprocess = subprocess.Popen(path)
                time.sleep(1)  # wait one second default
            except:
                opened = False

        if opened:
            logging.info("Zahner Analysis launched")
            startTime = time.time()
            # Wait up to timeToWaitForCheck seconds until the server is online.
            while (
                timeToWaitForCheck > (time.time() - startTime)
                and self.isOnline() is False
            ):
                print("Zahner Analysis server offline retry")
                time.sleep(0.5)
            if self.isOnline() is False:
                logging.error("Zahner Analysis launched but server is offline")
        else:
            logging.error("Zahner Analysis can not be launched")
        return opened

    def isOnline(self, timeout=0.5):
        """Returns the online state

        This function returns true if the Zahner Analysis can be reached.
        This function writes information with the logging module.

        :param timeout: Timeout, for the get command.
        :returns: True if the Zahner Analysis is online.
        """
        retval = True
        try:
            self.get(self._onlineCheckUrl, timeout=timeout)
            logging.info("Zahner Analysis server online")
        except:
            logging.info("Zahner Analysis server offline")
            retval = False
        return retval

    def get(self, url=None, *args, **kwargs):
        """get request wrapper

        This function wraps the get request. Only the relative URL path to the root must be specified.
        This function automatically adds ip, port and api key.

        If a full path with http is specified, then this path will be used and will not be edited.

        :param url: url for request.
        :returns: Reply from requests.get
        """
        return requests.get(self._urlComposer(url), *args, **kwargs)

    def post(self, url=None, *args, **kwargs):
        """post request wrapper

        This function wraps the post request. Only the relative URL path to the root must be specified.
        This function automatically adds ip, port and api key.

        If a full path with http is specified, then this path will be used and will not be edited.

        :param url: URL for request.
        :returns: Reply from requests.post
        """
        return requests.post(self._urlComposer(url), *args, **kwargs)

    def _urlComposer(self, url):
        """Composition of the URL

        This function composes the URL with IP, port and api key if there is no "http" in the url parameter.

        :param url: URL relative or absolute.
        :returns: Composed URL.
        """
        if url is None:
            url = self._ip
        elif "http" in url:
            pass
        else:
            url = f"{self._ip}{url}?key={self._apiKey}"
        return url

    def __del__(self):
        """Destructor

        If the library has opened the Zahner Analysis, then it will be closed again. If keepOpen is set, it will not be closed.
        """
        if self._subprocess is not None:
            if self._keepOpen is False:
                self._subprocess.kill()
        return
