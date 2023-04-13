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
import io
import os
import re
from io import StringIO
from typing import Union

from zahner_analysis.file_import.thales_file_utils import *


class SeqTxtImport:
    """Class to be able to read the sequence text files.

    The following lines show a short example how to read all data tracks including ACQ channels.

    .. code-block:: python

        imp = SeqTxtImport(r"C:/THALES/sequence.txt")

        tracks = imp.getTrackTypesList()
        dataTracks = {}
        for track in tracks:
            dataTracks[track] = imp.getTrack(track)

        time = imp.getTrack("Time/s")
        u = imp.getTrack("E/V")
        i = imp.getTrack("I/A")

    :param file: The path to the txt file, or the txt file as bytes or bytearray.
    :type file: str, bytes, bytearray
    """

    def __init__(self, filename: Union[str, bytes, bytearray]):
        self._filename = "FromBytes.txt"
        if isinstance(filename, bytes) or isinstance(filename, bytearray):
            self._binaryFileContent = filename
            fileBinary = io.BytesIO(filename)
        else:
            (_, self._filename) = os.path.split(filename)
            with open(filename, "rb") as f:
                self._binaryFileContent = f.read()

            fileBinary = open(filename, "rb")

        fileString = fileBinary.read().decode("utf-8")
        fileStringIO = StringIO(fileString)
        header = fileStringIO.readline()

        singlePattern = r"[\s]+(\S+)"
        self._dataTrackNames = re.findall(singlePattern, header)

        completePattern = singlePattern * len(self._dataTrackNames) + r"[\s]+"

        self._data = dict()
        for key in self._dataTrackNames:
            self._data[key] = []

        for line in fileStringIO.readlines():
            match = re.search(completePattern, line)

            for i in range(len(self._dataTrackNames)):
                self._data[self._dataTrackNames[i]].append(float(match[i + 1]))

        return

    def getTrackTypesList(self) -> list[str]:
        """
        returns a list with the different data tracks.

        :returns: List with the track names.
        """
        return self._dataTrackNames

    def getTrack(self, track: str) -> list[float]:
        """
        returns an array with the points for the given track.

        :param track: name of the track
        :returns: Numpy array with the track.
        """
        return self._data[track]

    def save(self, filename):
        """Save the cv data.

        Only the binary file content that has been read is saved. If the data is edited, this is not saved.

        :param filename: Path and filename of the file to be saved with the extension .txt.
        """
        with open(filename, "wb") as f:
            f.write(self._binaryFileContent)
        return

    def getFileName(self) -> str:
        """
        Get the name of the file.

        :returns: The filename if the file was opened or "FromBytes.txt" if it was created from bytearrays.
        """
        return self._filename

    def getBinaryFileContent(self) -> bytearray:
        """
        Get the content of the file binary.

        Returns the file contents as a binary byte array.

        :returns: bytearray with the file content.
        """
        return self._binaryFileContent
