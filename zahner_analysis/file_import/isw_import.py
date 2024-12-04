r"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2024 Zahner-Elektrik GmbH & Co. KG

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

import numpy as np
import datetime
import io
import re
import os

from zahner_analysis.file_import.thales_file_utils import *


class IswImport:
    """Class to be able to read out Isw files (POL).

    This class extracts the data from the Isw files.

    :param file: The path to the Isw file, or the Isw file as bytes or bytearray.
    :type file: str, bytes, bytearray
    """

    def __init__(self, filename):
        self._filename = "FromBytes.isw"
        if isinstance(filename, bytes) or isinstance(filename, bytearray):
            self._binaryFileContent = filename
            iswFile = io.BytesIO(filename)
        else:
            (_, self._filename) = os.path.split(filename)
            with open(filename, "rb") as f:
                self._binaryFileContent = f.read()

            iswFile = open(filename, "rb")

        self.version = readI6FromFile(iswFile)
        self.tmp = readI6FromFile(iswFile)
        self.length = readI6FromFile(iswFile) + 1

        self.voltage = np.zeros(self.length)
        self.current = np.zeros(self.length)
        self.time = np.zeros(self.length)

        for i in range(self.length):
            self.voltage[i] = readF8FromFile(iswFile) / 1000.0
            self.current[i] = readF8FromFile(iswFile) / 1000.0
            self.time[i] = readF8FromFile(iswFile) / 1000.0

        return

    def getTimeArray(self) -> np.ndarray:
        """Reading the measurement time stamps.

        :returns: Numpy array with the time points.
        """
        return self.time

    def getCurrentArray(self) -> np.ndarray:
        """Reading the measurement current points.

        :returns: Numpy array with the current points.
        """
        return self.current

    def getVoltageArray(self) -> np.ndarray:
        """Reading the measurement voltage points.

        :returns: Numpy array with the voltage points.
        """
        return self.voltage

    def getFileName(self) -> str:
        """Get the name of the file.

        :returns: The filename if the file was opened or "FromBytes.isw" if it was created from bytearrays.
        """
        return self._filename
