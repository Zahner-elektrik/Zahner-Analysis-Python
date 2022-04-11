"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2022 Zahner-Elektrik GmbH & Co. KG

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


class IsmImport():
    """ Class to be able to read ism files (EIS data).
    
    This class extracts the data from the ism files.
    It returns the data for the frequency range between the reversal frequency and the end frequency.
    
    :param file: The path to the ism file, or the ism file as bytes or bytearray.
    :type file: str, bytes, bytearray
    """

    def __init__(self, filename):
        self._filename = "FromBytes.ism"
        if isinstance(filename, bytes) or isinstance(filename, bytearray):
            self._binaryFileContent = filename
            ismFile = io.BytesIO(filename)
        else:
            (_, self._filename) = os.path.split(filename)
            with open(filename, "rb") as f:
                self._binaryFileContent = f.read()
            
            ismFile = open(filename, 'rb')
        
        version = ismFile.read(6)
        self.numberOfSamples = int.from_bytes(ismFile.read(6), "big", signed=True) + 1             
        tmpFrequency = np.ndarray(shape=(self.numberOfSamples,), dtype=">f8", buffer=ismFile.read(8 * self.numberOfSamples))
        tmpImpedance = np.ndarray(shape=(self.numberOfSamples,), dtype=">f8", buffer=ismFile.read(8 * self.numberOfSamples))
        tmpPhase = np.ndarray(shape=(self.numberOfSamples,), dtype=">f8", buffer=ismFile.read(8 * self.numberOfSamples))
        tmpTime = np.ndarray(shape=(self.numberOfSamples,), dtype=">f8", buffer=ismFile.read(8 * self.numberOfSamples))
        tmpSignificance = np.ndarray(shape=(self.numberOfSamples,), dtype=">i2", buffer=ismFile.read(2 * self.numberOfSamples))
        
        dateStringLength = int.from_bytes(ismFile.read(2), "big", signed=True)
        dateString = ismFile.read(dateStringLength)
        date = dateString[0:6].decode("ASCII")
        
        day = int(date[0:2])
        month = int(date[2:4])
        year = int(date[4:6])
        
        """
        Only the last two digits of the date are saved.
        It is assumed that the measurement was carried out between 1970 and 2070.
        A software update is necessary in the year 2070 at the latest.
        """
        if year < 70:
            year += 2000
        else:
            year += 1900
            
        self.measurementDate = datetime.datetime(year, month, day)
        
        self.frequency = np.zeros(len(tmpFrequency))
        for i in range(len(tmpFrequency)):
            self.frequency[i] = tmpFrequency[i]
        
        self.impedance = np.zeros(len(tmpImpedance))
        for i in range(len(tmpImpedance)):
            self.impedance[i] = tmpImpedance[i]
        
        self.phase = np.zeros(len(tmpPhase))
        for i in range(len(tmpPhase)):
            self.phase[i] = tmpPhase[i]
            
        self.measurementTimeStamp = []
        for i in range(len(tmpTime)):
            self.measurementTimeStamp.append(self._ismTimeStampToDateTime(tmpTime[i]))
            
        self.significance = np.zeros(len(tmpSignificance))
        for i in range(len(tmpSignificance)):
            self.significance[i] = tmpSignificance[i]
        
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
        """ Returns the complete number of samples.
        
        This function returns the number of samples in the ism file.
        This number can be greater than the number of elements returned in the arrays.
        For the arrays, only the largest frequency range from minimum to maximum frequency is returned,
        not the overlapping range.
        
        :returns: Number of total samples.
        """
        return self.numberOfSamples
    
    def getFrequencyArray(self):
        """ Get the frequency points from the measurement.
        
        The frequency points between the reversal frequency and the final frequency are returned.
        
        :returns: Numpy array with the frequency points.
        """
        if self.swapNecessary:
            return np.flip(self.frequency[self.fromIndex:self.toIndex])
        else:
            return self.frequency[self.fromIndex:self.toIndex]
    
    def getImpedanceArray(self):
        """ Get the impedance points from the measurement.
        
        The impedance points between the reversal frequency and the final frequency are returned.
        
        :returns: Numpy array with the impedance points.
        """
        if self.swapNecessary:
            return np.flip(self.impedance[self.fromIndex:self.toIndex])
        else:
            return self.impedance[self.fromIndex:self.toIndex]
        
    def getPhaseArray(self):
        """ Get the phase points from the measurement.
        
        The phase points between the reversal frequency and the final frequency are returned.
        
        :returns: Numpy array with the phase points as radiant.
        """
        if self.swapNecessary:
            return np.flip(self.phase[self.fromIndex:self.toIndex])
        else:
            return self.phase[self.fromIndex:self.toIndex]
    
    def getComplexImpedanceArray(self):
        """ Get the complex impedance points from the measurement.
        
        The complex impedance points between the reversal frequency and the final frequency are returned.
        
        :returns: Numpy array with the complex impedance points.
        """
        imp = self.getImpedanceArray()
        phase = self.getPhaseArray()
        
        return np.cos(phase) * imp + 1j * np.sin(phase) * imp
    
    def getSignificanceArray(self):
        """ Get the significance points from the measurement.
        
        The significance points between the reversal frequency and the final frequency are returned.
        
        :returns: Numpy array with the significance points.
        """
        if self.swapNecessary:
            return np.flip(self.significance[self.fromIndex:self.toIndex])
        else:
            return self.significance[self.fromIndex:self.toIndex]
    
    def getMeasurementDateTimeArray(self):
        """ Get the timestamps from the measurement.
        
        The timestamps between the reversal frequency and the final frequency are returned.
        The smallest time is the reversal point. The start time is not included in this array because
        the overlapping points are not returned.
        
        :returns: Numpy array with the datetime objects.
        """
        if self.swapNecessary:
            return np.flip(self.measurementTimeStamp[self.fromIndex:self.toIndex])
        else:
            return self.measurementTimeStamp[self.fromIndex:self.toIndex]
    
    def getMeasurementEndDateTime(self):
        """ Get the end date time of the measurement.
        
        Returns the end datetime of the measurement.
        
        :returns: datetime object with the end time of the measurement.
        """
        return max(self.measurementTimeStamp)
    
    def save(self, filename):
        """ Save the impedance data.
        
        Only the binary file content that has been read is saved. If the data is edited, this is not saved.
        
        :param filename: Path and filename of the file to be saved with the extension .ism.
        """
        with open(filename, 'wb') as f:
            f.write(self._binaryFileContent)
        return
    
    def getFileName(self):
        """ Get the name of the file.
        
        :returns: The filename if the file was opened or "FromBytes.ism" if it was created from bytearrays.
        """
        return self._filename
    
    def getBinaryFileContent(self):
        """ Get the content of the file binary.
        
        Returns the file contents as a binary byte array.
        
        :returns: bytearray with the file content.
        """
        return self._binaryFileContent
        
    def _ismTimeStampToDateTime(self, timestamp):
        """ Calculation of the time stamp.
        
        The time is in seconds related to 01.01.1980.
        
        :param timestamp: Seconds since 01.01.1980.
        :returns: Python datetime object.
        """
        timeZero = datetime.datetime(1980, 1, 1)
        timeDifference = datetime.timedelta(seconds=abs(timestamp))
        
        timestamp = timeZero + timeDifference
        return timestamp
    
