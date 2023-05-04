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
import datetime
import io
import os
from typing import Union

from zahner_analysis.file_import.thales_file_utils import *


class IsmImport:
    """Class to be able to read ism files (EIS data).

    This class extracts the data from the ism files.
    It returns the data for the frequency range between the reversal frequency and the end frequency.

    :param file: The path to the ism file, or the ism file as bytes or bytearray.
    :type file: str, bytes, bytearray
    """

    def __init__(self, filename: Union[str, bytes, bytearray]):
        self._filename = "FromBytes.ism"
        if isinstance(filename, bytes) or isinstance(filename, bytearray):
            self._binaryFileContent = filename
            ismFile = io.BytesIO(filename)
        else:
            (_, self._filename) = os.path.split(filename)
            with open(filename, "rb") as f:
                self._binaryFileContent = f.read()

            ismFile = open(filename, "rb")

        version = readI6FromFile(ismFile)
        self.numberOfSamples = readI6FromFile(ismFile) + 1
        self.frequency = readF8ArrayFromFile(ismFile, self.numberOfSamples)
        self.impedance = readF8ArrayFromFile(ismFile, self.numberOfSamples)
        self.phase = readF8ArrayFromFile(ismFile, self.numberOfSamples)
        self.measurementTimeStamp = readTimeStampDateTimeArrayFromFile(
            ismFile, self.numberOfSamples
        )
        self.significance = readI2ArrayFromFile(ismFile, self.numberOfSamples)

        self.acqChannels = dict()

        self.measurementDate = readZahnerDate(ismFile)

        self.system = readZahnerStringFromFile(ismFile)
        self.potential = readZahnerStringFromFile(ismFile)
        self.current = readZahnerStringFromFile(ismFile)
        self.temperature = readZahnerStringFromFile(ismFile)
        self.time = readZahnerStringFromFile(ismFile)
        self.comment_1 = readZahnerStringFromFile(ismFile)
        self.comment_2 = readZahnerStringFromFile(ismFile)
        self.comment_3 = readZahnerStringFromFile(ismFile)
        self.comment_4 = readZahnerStringFromFile(ismFile)

        self.areaForCurrentDensity = readZahnerStringFromFile(ismFile)
        serialQuantityStuff = readZahnerStringFromFile(ismFile)
        acquisition_flag = readI2FromFile(ismFile)

        kValues = readF8ArrayFromFile(ismFile, 32)

        k_value_27 = int(kValues[27])

        if acquisition_flag > 256 and (k_value_27 & 32768) == 32768:
            self.acqChannels["Voltage/V"] = np.ndarray(
                shape=(self.numberOfSamples,), dtype=">f8"
            )
            self.acqChannels["Current/A"] = np.ndarray(
                shape=(self.numberOfSamples,), dtype=">f8"
            )

            for index in range(self.numberOfSamples):
                self.acqChannels["Voltage/V"][index] = readF8FromFile(ismFile)
                self.acqChannels["Current/A"][index] = readF8FromFile(ismFile)

        self._metaData = bytearray(ismFile.read())
        ismFile.close()

        """
        The frequency range at the beginning, which is measured overlapping, is not returned,
        therefore now the array indices are determined in which range the data are, which are
        returned by the getters.
        """
        self.minFrequencyIndex = np.argmin(self.frequency)
        self.maxFrequencyIndex = np.argmax(self.frequency)

        self.swapNecessary = False
        self.fromIndex = self.minFrequencyIndex
        self.toIndex = self.maxFrequencyIndex

        if self.minFrequencyIndex > self.maxFrequencyIndex:
            self.swapNecessary = True
            self.fromIndex = self.maxFrequencyIndex
            self.toIndex = self.minFrequencyIndex

        self.toIndex += 1
        return

    def getNumberOfSamples(self):
        """Returns the complete number of samples.

        This function returns the number of samples in the ism file.
        This number can be greater than the number of elements returned in the arrays.
        For the arrays, only the largest frequency range from minimum to maximum frequency is returned,
        not the overlapping range.

        :returns: Number of total samples.
        """
        return self.numberOfSamples

    def getFrequencyArray(self):
        """Get the frequency points from the measurement.

        The frequency points between the reversal frequency and the final frequency are returned.

        :returns: Numpy array with the frequency points.
        """
        if self.swapNecessary:
            return np.flip(self.frequency[self.fromIndex : self.toIndex])
        else:
            return self.frequency[self.fromIndex : self.toIndex]

    def getImpedanceArray(self):
        """Get the impedance points from the measurement.

        The impedance points between the reversal frequency and the final frequency are returned.

        :returns: Numpy array with the impedance points.
        """
        if self.swapNecessary:
            return np.flip(self.impedance[self.fromIndex : self.toIndex])
        else:
            return self.impedance[self.fromIndex : self.toIndex]

    def getPhaseArray(self, degree=False):
        """Get the phase points from the measurement.

        The phase points between the reversal frequency and the final frequency are returned.

        :returns: Numpy array with the phase points as radiant.
        """
        radToDegree = 1.0
        if degree == True:
            radToDegree = 360 / (2 * np.pi)
        if self.swapNecessary:
            return np.flip(self.phase[self.fromIndex : self.toIndex] * radToDegree)
        else:
            return self.phase[self.fromIndex : self.toIndex] * radToDegree

    def getComplexImpedanceArray(self):
        """Get the complex impedance points from the measurement.

        The complex impedance points between the reversal frequency and the final frequency are returned.

        :returns: Numpy array with the complex impedance points.
        """
        imp = self.getImpedanceArray()
        phase = self.getPhaseArray()

        return np.cos(phase) * imp + 1j * np.sin(phase) * imp

    def getSignificanceArray(self):
        """Get the significance points from the measurement.

        The significance points between the reversal frequency and the final frequency are returned.

        :returns: Numpy array with the significance points.
        """
        if self.swapNecessary:
            return np.flip(self.significance[self.fromIndex : self.toIndex])
        else:
            return self.significance[self.fromIndex : self.toIndex]

    def getMeasurementDateTimeArray(self):
        """Get the timestamps from the measurement.

        The timestamps between the reversal frequency and the final frequency are returned.
        The smallest time is the reversal point. The start time is not included in this array because
        the overlapping points are not returned.

        :returns: Numpy array with the datetime objects.
        """
        if self.swapNecessary:
            return np.flip(self.measurementTimeStamp[self.fromIndex : self.toIndex])
        else:
            return self.measurementTimeStamp[self.fromIndex : self.toIndex]

    def getMeasurementStartDateTime(self):
        """Get the start date time of the measurement.

        Returns the start datetime of the measurement.

        :returns: datetime object with the start time of the measurement.
        """
        return min(self.measurementTimeStamp)

    def getMeasurementEndDateTime(self):
        """Get the end date time of the measurement.

        Returns the end datetime of the measurement.

        :returns: datetime object with the end time of the measurement.
        """
        return max(self.measurementTimeStamp)

    def save(self, filename):
        """Save the impedance data.

        Only the binary file content that has been read is saved. If the data is edited, this is not saved.

        :param filename: Path and filename of the file to be saved with the extension .ism.
        """
        with open(filename, "wb") as f:
            f.write(self._binaryFileContent)
        return

    def getFileName(self):
        """Get the name of the file.

        :returns: The filename if the file was opened or "FromBytes.ism" if it was created from bytearrays.
        """
        return self._filename

    def getBinaryFileContent(self):
        """Get the content of the file binary.

        Returns the file contents as a binary byte array.

        :returns: bytearray with the file content.
        """
        return self._binaryFileContent

    def getMetaData(self):
        """Get the meta data of the file binary.

        Returns the file contents as a binary byte array.

        :returns: bytearray with the file content.
        """
        return self._metaData

    def getTrackTypesList(self) -> list[str]:
        """
        returns a list with the different data tracks.

        :returns: List with the track names.
        """
        return list(map(str, self.acqChannels.keys()))

    def getTrack(self, track: str) -> np.ndarray:
        """
        returns an array with the points for the given track.

        :param track: name of the track
        :returns: Numpy array with the track.
        """
        return self.acqChannels[track]
