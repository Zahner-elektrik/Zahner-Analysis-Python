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
import numpy as np
import io
import re
import os
import datetime

from zahner_analysis.file_import.thales_file_utils import *


class IssImport:
    """Class to be able to read out iss files (I/E, Current Voltage Curves).

    This class extracts the data from the iss files.

    :param file: The path to the iss file, or the iss file as bytes or bytearray.
    :type file: str, bytes, bytearray
    """

    def __init__(self, filename):
        self._filename = "FromBytes.iss"
        if isinstance(filename, bytes) or isinstance(filename, bytearray):
            self._binaryFileContent = filename
            issFile = io.BytesIO(filename)
        else:
            (_, self._filename) = os.path.split(filename)
            with open(filename, "rb") as f:
                self._binaryFileContent = f.read()

            issFile = open(filename, "rb")

        self.EdgePotential0 = readF8FromFile(issFile)
        self.EdgePotential1 = readF8FromFile(issFile)
        self.EdgePotential2 = readF8FromFile(issFile)
        self.EdgePotential3 = readF8FromFile(issFile)
        self.Resolution = readF8FromFile(issFile)
        self.variable_a = readF8FromFile(issFile)
        self.variable_b = readF8FromFile(issFile)
        self.RelativeTolerance = readF8FromFile(issFile)
        self.AbsoluteTolerance = readF8FromFile(issFile)
        self.OhmicDrop = readF8FromFile(issFile)

        numberOfElements = readI6FromFile(issFile) + 1

        intVoltageRead = readI2ArrayFromFile(issFile, numberOfElements)
        self.current = readF8ArrayFromFile(issFile, numberOfElements)
        self.time = readF8ArrayFromFile(issFile, numberOfElements)

        self.Date = readZahnerStringFromFile(issFile)
        self.System = readZahnerStringFromFile(issFile)
        self.Temperature = readZahnerStringFromFile(issFile)
        self.Time = readZahnerStringFromFile(issFile)
        self.Slew_Rate = readZahnerStringFromFile(issFile)
        self.Comment_1 = readZahnerStringFromFile(issFile)
        self.Comment_2 = readZahnerStringFromFile(issFile)
        self.Comment_3 = readZahnerStringFromFile(issFile)
        self.Comment_4 = readZahnerStringFromFile(issFile)
        self.Comment_5 = readZahnerStringFromFile(issFile)
        self.ElectrodeArea = readZahnerStringFromFile(issFile)
        self.POPF = readZahnerStringFromFile(issFile)

        starttime, endtime = self.Time.split("-")

        try:
            self.measurementStartDateTime = datetime.datetime.strptime(
                self.Date + starttime, "%d%m%y%H:%M:%S"
            )
            self.measurementEndDateTime = datetime.datetime.strptime(
                self.Date + endtime, "%d%m%y%H:%M:%S"
            )
        except:
            # something is incorrect with the file format.
            self.measurementStartDateTime = None
            self.measurementEndDateTime = None

        offset = 0.0
        factor = 1.0

        popfPattern = "^\s*(.*?),\s*(.*?)\s*PO.PF.*Ima.*?,(.*?), *(.*)$"

        popfMatch = re.search(popfPattern, self.POPF)

        if popfMatch:
            offset = float(popfMatch.group(1))
            factor = float(popfMatch.group(2))
            PowerOfPotentialScaling = float(popfMatch.group(3))
            ExtraOffsetX = float(popfMatch.group(4))
        else:
            # fallback to old format for older ISC files:

            popfPattern = "^\s*(.*?),\\s*(.*?)\s*PO.PF.*"
            popfMatch = re.search(popfPattern, self.POPF)

            if popfMatch:
                offset = float(popfMatch.group(1))
                factor = float(popfMatch.group(2))

        self.voltage = intVoltageRead * (factor / 8000.0) + offset
        return

    def getMeasurementStartDateTime(self):
        """Get the start date time of the measurement.

        Returns the start datetime of the measurement.

        :returns: datetime object with the start time of the measurement.
        """
        return self.measurementStartDateTime

    def getMeasurementEndDateTime(self):
        """Get the end date time of the measurement.

        Returns the end datetime of the measurement.

        :returns: datetime object with the end time of the measurement.
        """
        return self.measurementEndDateTime

    def getTimeArray(self):
        """Reading the measurement time stamps.

        :returns: Numpy array with the time points.
        """
        return self.time

    def getCurrentArray(self):
        """Reading the measurement current points.

        :returns: Numpy array with the current points.
        """
        return self.current

    def getVoltageArray(self):
        """Reading the measurement voltage points.

        :returns: Numpy array with the voltage points.
        """
        return self.voltage

    def save(self, filename):
        """Save the cv data.

        Only the binary file content that has been read is saved. If the data is edited, this is not saved.

        :param filename: Path and filename of the file to be saved with the extension .ism.
        """
        with open(filename, "wb") as f:
            f.write(self._binaryFileContent)
        return

    def getFileName(self):
        """Get the name of the file.

        :returns: The filename if the file was opened or "FromBytes.isc" if it was created from bytearrays.
        """
        return self._filename

    def getBinaryFileContent(self):
        """Get the content of the file binary.

        Returns the file contents as a binary byte array.

        :returns: bytearray with the file content.
        """
        return self._binaryFileContent
