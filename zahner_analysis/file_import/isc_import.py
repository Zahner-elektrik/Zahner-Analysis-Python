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


class IscImport:
    r"""Class to be able to read out isc files (CV).

    This class extracts the data from the isc files.

    The following code example shows how the ACQ data can be read out:

    .. code-block:: python

        cvData = IscImport(r".\CV_32_acq_channels.isc")  # read the file

        print(cvData.getAcqChannelNamesList())  # print available channels
        print(cvData.getAcqChannelUnitsList())  # print available units

        print(cvData.getAcqDecoded())  # read the flag for the ACQ status
        desiredAcqChannel = cvData.getAcqChannelNamesList()[
            1
        ]  # pick one acq channel by ChannelName
        print(f"data for channel: {desiredAcqChannel}")
        print(
            cvData.getAcqChannel(desiredAcqChannel)[0:10]
        )  # get the data for this channel


    Output of the previous snippet:

    .. code-block:: bash

        ['TC: K; V= 201', 'TC: K; V= 201-1', 'Pot1', 'Pot2', 'Reference', 'NTC', 'Voltage', 'Voltage-1', 'voltage', 'TC: K; V= 201-2', 'TC: K; V= 201-3', 'Pot1-1', 'Pot2-1', '', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8', '-9', '-10', '-11', '-12', '-13', '-14', '-15', '-16', '-17', '-18']
        ['CC', 'C', 'V', 'V', 'C', 'C', 'V', 'V', 'V', 'CC', 'C', 'V', 'V', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
        True
        data for channel: TC: K; V= 201-1
        [8.554705   8.44567554 8.4188244  8.40748142 8.41311547 8.41441981
        8.4115903  8.40405186 8.39793716 8.40518822]

    :param file: The path to the isc file, or the isc file as bytes or bytearray.
    :type file: str, bytes, bytearray
    """

    def __init__(self, filename):
        self._filename = "FromBytes.isc"
        if isinstance(filename, bytes) or isinstance(filename, bytearray):
            self._binaryFileContent = filename
            iscFile = io.BytesIO(filename)
        else:
            (_, self._filename) = os.path.split(filename)
            with open(filename, "rb") as f:
                self._binaryFileContent = f.read()

            iscFile = open(filename, "rb")

        self.Pstart = readF8FromFile(iscFile)
        self.Tstart = readF8FromFile(iscFile)
        self.Pupper = readF8FromFile(iscFile)
        self.Plower = readF8FromFile(iscFile)
        self.Tend = readF8FromFile(iscFile)
        self.Pend = readF8FromFile(iscFile)
        self.Srate = readF8FromFile(iscFile)
        self.Periods = readF8FromFile(iscFile)
        self.PpPer = readF8FromFile(iscFile)
        self.Imi = readF8FromFile(iscFile)
        self.Ima = readF8FromFile(iscFile)
        self.Odrop = readF8FromFile(iscFile)
        self.Sstart = readF8FromFile(iscFile)
        self.Send = readF8FromFile(iscFile)
        self.AZeit = readF8FromFile(iscFile)
        self.ZpMp = readF8FromFile(iscFile)
        self.delay = readF8FromFile(iscFile)

        self.numberOfElements = readI6FromFile(iscFile) + 1
        intVoltageRead = readI2ArrayFromFile(iscFile, self.numberOfElements)
        self.current = readF8ArrayFromFile(iscFile, self.numberOfElements)

        self.Date = readZahnerStringFromFile(iscFile)
        self.System = readZahnerStringFromFile(iscFile)
        self.Temperature = readZahnerStringFromFile(iscFile)
        self.Time = readZahnerStringFromFile(iscFile)
        self.Slew_Rate = readZahnerStringFromFile(iscFile)
        self.Comment_1 = readZahnerStringFromFile(iscFile)
        self.Comment_2 = readZahnerStringFromFile(iscFile)
        self.Comment_3 = readZahnerStringFromFile(iscFile)
        self.Comment_4 = readZahnerStringFromFile(iscFile)
        self.Comment_5 = readZahnerStringFromFile(iscFile)
        self.ElecArea = readZahnerStringFromFile(iscFile)
        self.POPF = readZahnerStringFromFile(iscFile)

        starttime, endtime = self.Time.split("-")

        self.measurementStartDateTime = datetime.datetime.strptime(
            self.Date + starttime, "%d%m%y%H:%M:%S"
        )
        self.measurementEndDateTime = datetime.datetime.strptime(
            self.Date + endtime, "%d%m%y%H:%M:%S"
        )

        offset = 0.0
        factor = 1.0

        popfPattern = r"^\s*(.*?),\s*(.*?)\s*PO.PF *(.*?), *(.*)$"

        popfMatch = re.search(popfPattern, self.POPF)

        if popfMatch:
            offset = float(popfMatch.group(1))
            factor = float(popfMatch.group(2))
            PowerOfPotentialScaling = float(popfMatch.group(3))
            ExtraOffsetX = float(popfMatch.group(4))
        else:
            # fallback to old format for older ISC files:

            popfPattern = r"^\s*(.*?),\\s*(.*?)\s*PO.PF.*"
            popfMatch = re.search(popfPattern, self.POPF)

            if popfMatch:
                offset = float(popfMatch.group(1))
                factor = float(popfMatch.group(2))

        self.voltage = intVoltageRead * (factor / 8000.0) + offset
        self.time = np.array(range(self.numberOfElements)) * self.ZpMp + self.Sstart

        """
        only new CV format with 32 ACQ channels
        """
        remainingBytes = get_remaining_bytes(iscFile)
        self.acqDecoderSuccess = None

        self.acqChannelNames = []
        self.acqChannelUnits = []
        self.acqData = dict()
        if remainingBytes > 400:
            self.acqDecoderSuccess = True
            try:
                maximumNumberOfAcqChannels = 32
                self.acqChannelNumbers = readI2ArrayFromFile(
                    iscFile, maximumNumberOfAcqChannels
                )
                self.acqChannelNames = []
                for i in range(maximumNumberOfAcqChannels):
                    channelName = readZahnerStringFromFile(iscFile)
                    if channelName in self.acqChannelNames:
                        index = 1
                        newName = f"{channelName}-{index}"
                        while newName in self.acqChannelNames:
                            index += 1
                            newName = f"{channelName}-{index}"
                        channelName = newName
                    self.acqChannelNames.append(channelName)
                self.acqChannelUnits = []
                for i in range(maximumNumberOfAcqChannels):
                    self.acqChannelUnits.append(readZahnerStringFromFile(iscFile))
                for i in range(maximumNumberOfAcqChannels):
                    # drop coefficients never tested in Zahner Analysis
                    readF8ArrayFromFile(iscFile, 11)

                numberOfAcqRows = readI6FromFile(iscFile) + 1
                numberOfAcqChannels = readI6FromFile(iscFile) + 1

                numberOfRowsToAdd = self.numberOfElements - numberOfAcqRows
                numberOfRowsToDrop = 0
                if numberOfRowsToAdd < 0:
                    numberOfRowsToDrop = abs(numberOfRowsToAdd)
                    numberOfRowsToAdd = 0

                self.acqData = dict()
                for channel in range(numberOfAcqChannels):
                    print(f"{self.acqChannelNames[channel]}")
                    self.acqData[self.acqChannelNames[channel]] = readF8ArrayFromFile(
                        iscFile, numberOfAcqRows - numberOfRowsToDrop
                    )
                    readF8ArrayFromFile(iscFile, numberOfRowsToDrop)
                    for i in range(numberOfRowsToAdd):
                        self.acqData[self.acqChannelNames[channel]].append(
                            self.acqData[self.acqChannelNames[channel]][-1]
                        )
            except:
                """
                Something does not match the acq format in the file, therefore the ACQ data cannot be decoded.
                """
                self.acqDecoderSuccess = False
                self.acqChannelNames = []
                self.acqChannelUnits = []
                self.acqData = dict()
                pass
        return

    def getAcqDecoded(self) -> Union[None, bool]:
        """
        returns the status of the decoded ACQ data, for debugging purposes, as the ACQ format is complex and could cause problems.

        :returns: None if no ACQ data is available, or True if it could be decoded or False if not.
        """
        return self.acqDecoderSuccess

    def getAcqChannelNamesList(self) -> list[str]:
        """
        returns a list with the different data tracks.

        :returns: List with the track names.
        """
        return self.acqChannelNames

    def getAcqChannelUnitsList(self) -> list[str]:
        """
        returns a list with the different data tracks.

        :returns: List with the track names.
        """
        return self.acqChannelUnits

    def getAcqChannel(self, track: str) -> list[float]:
        """
        returns an array with the points for the given track.

        :param track: name of the track
        :returns: Numpy array with the track.
        """
        return self.acqData[track]

    def getMeasurementStartDateTime(self) -> datetime.datetime:
        """Get the start date time of the measurement.

        Returns the start datetime of the measurement.

        :returns: datetime object with the start time of the measurement.
        """
        return self.measurementStartDateTime

    def getMeasurementEndDateTime(self) -> datetime.datetime:
        """Get the end date time of the measurement.

        Returns the end datetime of the measurement.

        :returns: datetime object with the end time of the measurement.
        """
        return self.measurementEndDateTime

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

    def getScanRate(self) -> np.ndarray:
        """Read the scan rate or slew rate.

        :returns: The scan rate in V/s.
        """
        return self.Srate / 1000.0

    def save(self, filename):
        """Save the cv data.

        Only the binary file content that has been read is saved. If the data is edited, this is not saved.

        :param filename: Path and filename of the file to be saved with the extension .ism.
        """
        with open(filename, "wb") as f:
            f.write(self._binaryFileContent)
        return

    def getFileName(self) -> str:
        """Get the name of the file.

        :returns: The filename if the file was opened or "FromBytes.isc" if it was created from bytearrays.
        """
        return self._filename

    def getBinaryFileContent(self) -> bytearray:
        """Get the content of the file binary.

        Returns the file contents as a binary byte array.

        :returns: bytearray with the file content.
        """
        return self._binaryFileContent
