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
from zahner_analysis.file_import.ism_import import IsmImport
from typing import Optional


class IsmExport:
    """
    Class for saving ism data.

    With this class only impedances to different frequency points can be stored.

    However, the ism files are not complete and can no longer be loaded in Thales, nor do they contain any meta data.
    ACQ data is also lost.

    :param frequency: Array with the frequency data.
    :param impedance: Array with the impedance data.
    :param phase: Array with the phase data.
    :param metaData: Binary metadata.
    """

    def __init__(
        self,
        ism: Optional[IsmImport] = None,
        frequency: Optional[list[float]] = None,
        impedance: Optional[list[float]] = None,
        phase: Optional[list[float]] = None,
        metaData: bytearray = bytearray(),
    ):
        self.startOfFile = bytearray(b"\x00\x00\xff\xff\xff\xfe")
        self._binaryFileContent = bytearray()

        if ism is not None:
            frequency = ism.getFrequencyArray()
            impedance = np.abs(ism.getComplexImpedanceArray())
            phase = np.angle(ism.getComplexImpedanceArray())
            metaData = ism.getMetaData()

        self.numberOfElements = min([len(frequency), len(impedance), len(phase)])

        significance = np.ones(shape=(self.numberOfElements,), dtype=">i2") * 1000
        time = [i for i in range(self.numberOfElements)]

        self.tmpFrequency = np.array(frequency, dtype=">f8")
        self.tmpImpedance = np.array(impedance, dtype=">f8")
        self.tmpPhase = np.array(phase, dtype=">f8")
        self.tmpTime = np.array(time, dtype=">f8")
        self.tmpSig = np.array(significance, dtype=">i2")

        self._binaryFileContent += self.startOfFile
        numberToWrite = self.numberOfElements - 1
        self._binaryFileContent += numberToWrite.to_bytes(6, "big")
        self._binaryFileContent += self.tmpFrequency.tobytes()
        self._binaryFileContent += self.tmpImpedance.tobytes()
        self._binaryFileContent += self.tmpPhase.tobytes()
        self._binaryFileContent += self.tmpTime.tobytes()
        self._binaryFileContent += self.tmpSig.tobytes()
        self._binaryFileContent += metaData
        return

    def getBinaryFileContent(self):
        """
        Get the content of the file binary.

        Returns the file contents as a binary byte array.

        :returns: bytearray with the file content.
        """
        return self._binaryFileContent

    def writeToFile(self, file):
        """
        Writing the file to the hard disk.

        :param file: Path to the file to be written.
        """
        with open(file, "wb") as file:
            file.write(self._binaryFileContent)
        return
