r"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2026 Zahner-Elektrik GmbH & Co. KG

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

import os
import numpy as np
from typing import Optional, Union

import zahner_link


class ZmxImpedance:
    """
    One impedance of a .zmx measurement.

    A measurement made with an IM7 can contain more than one impedance.
    A PAD4 card, for example, adds one impedance per channel to the impedance of the cell.
    Objects of this class are created by :class:`ZmxImport`, they are not created by the user.

    The getters for frequency, impedance and phase are the same as those of
    :class:`~zahner_analysis.file_import.ism_import.IsmImport`, so the object can be fitted
    and plotted like .ism data.

    :param zmxFile: The file which contains the impedance.
    :param impedanceData: The impedance data from zahner_link.
    :param frequency: The frequencies of the dataset that contains the impedance.
    :param times: The measurement times of the dataset in seconds.
    """

    def __init__(
        self,
        zmxFile: "ZmxImport",
        impedanceData: zahner_link.ImpedanceData,
        frequency: np.ndarray,
        times: np.ndarray,
    ):
        self._zmxFile = zmxFile
        self._name = impedanceData.get_impedance_name()
        self._numeratorDimension = impedanceData.get_numerator_dimension()
        self._denominatorDimension = impedanceData.get_denominator_dimension()

        self.frequency = frequency
        self.times = times
        self.impedance = np.array(impedanceData.get_track("|impedance|"))
        self.phase = np.array(impedanceData.get_track("phase"))
        self._tracks = {
            name: np.array(track) for name, track in impedanceData.get_tracks().items()
        }

        # The frequency range at the beginning, which is measured overlapping, is not returned,
        # therefore the array indices are determined in which range the data are, which are
        # returned by the getters.
        minFrequencyIndex = int(np.argmin(self.frequency))
        maxFrequencyIndex = int(np.argmax(self.frequency))
        self._fromIndex = min(minFrequencyIndex, maxFrequencyIndex)
        self._toIndex = max(minFrequencyIndex, maxFrequencyIndex) + 1
        self._swapNecessary = minFrequencyIndex > maxFrequencyIndex
        return

    def getName(self) -> str:
        """
        Get the name of the impedance.

        The name is the impedance name stored in the file. If nobody named the impedance, the
        name is made of the signal paths, for example
        "2557874741.POT.U~43043.PAD_U/2557874741.POT.I~43043.PAD_I".

        This name is sent to the Zahner Analysis as ImpedanceName when the impedance is fitted.

        :returns: The name of the impedance.
        """
        return self._name

    def getNumeratorDimension(self) -> str:
        """
        Get the dimension of the numerator of the impedance.

        :returns: The dimension, for example "voltage" or "padx[1].ch1".
        """
        return self._numeratorDimension

    def getDenominatorDimension(self) -> str:
        """
        Get the dimension of the denominator of the impedance.

        :returns: The dimension, for example "current".
        """
        return self._denominatorDimension

    def getDimensionName(self) -> str:
        """
        Get the dimensions of the impedance as readable name.

        :returns: Numerator and denominator dimension, for example "padx[1].ch1/current".
        """
        return f"{self._numeratorDimension}/{self._denominatorDimension}"

    def getZmxFile(self) -> "ZmxImport":
        """
        Get the file which contains the impedance.

        :returns: The :class:`ZmxImport` object.
        """
        return self._zmxFile

    def getNumberOfSamples(self) -> int:
        """
        Get the number of samples.

        :returns: Number of total samples, including the overlapping frequency range.
        """
        return len(self.frequency)

    def getFrequencyArray(self, includeDoubleFrequencies: bool = False) -> np.ndarray:
        """
        Get the frequency points from the measurement.

        :param includeDoubleFrequencies: If True, all measurement data are returned, if False, only the largest non-overlapping area is returned. Defaults to False.
        :returns: Numpy array with the frequency points.
        """
        return self._arraySlice(self.frequency, includeDoubleFrequencies)

    def getImpedanceArray(self, includeDoubleFrequencies: bool = False) -> np.ndarray:
        """
        Get the impedance points from the measurement.

        :param includeDoubleFrequencies: If True, all measurement data are returned, if False, only the largest non-overlapping area is returned. Defaults to False.
        :returns: Numpy array with the impedance points.
        """
        return self._arraySlice(self.impedance, includeDoubleFrequencies)

    def getPhaseArray(
        self, degree: bool = False, includeDoubleFrequencies: bool = False
    ) -> np.ndarray:
        """
        Get the phase points from the measurement.

        :param degree: True for phase in degree, default radiant.
        :param includeDoubleFrequencies: If True, all measurement data are returned, if False, only the largest non-overlapping area is returned. Defaults to False.
        :returns: Numpy array with the phase points as radiant.
        """
        phase = self._arraySlice(self.phase, includeDoubleFrequencies)
        if degree:
            return np.degrees(phase)
        return phase

    def getComplexImpedanceArray(
        self, includeDoubleFrequencies: bool = False
    ) -> np.ndarray:
        """
        Get the complex impedance points from the measurement.

        :param includeDoubleFrequencies: If True, all measurement data are returned, if False, only the largest non-overlapping area is returned. Defaults to False.
        :returns: Numpy array with the complex impedance points.
        """
        imp = self.getImpedanceArray(includeDoubleFrequencies)
        phase = self.getPhaseArray(includeDoubleFrequencies=includeDoubleFrequencies)
        return np.cos(phase) * imp + 1j * np.sin(phase) * imp

    def getMeasurementTimeArray(
        self, includeDoubleFrequencies: bool = False
    ) -> np.ndarray:
        """
        Get the time of each measurement point.

        :param includeDoubleFrequencies: If True, all measurement data are returned, if False, only the largest non-overlapping area is returned. Defaults to False.
        :returns: Numpy array with the time in seconds since the start of the measurement.
        """
        return self._arraySlice(self.times, includeDoubleFrequencies)

    def getTrackTypesList(self) -> list[str]:
        """
        Get the names of the tracks of the impedance.

        These are for example ``|impedance|``, ``phase``, ``impedance error`` and ``phase error``.

        :returns: List with the track names.
        """
        return list(self._tracks.keys())

    def getTrack(
        self, track: str, includeDoubleFrequencies: bool = False
    ) -> np.ndarray:
        """
        Get a track of the impedance.

        The names of the tracks are returned by :meth:`getTrackTypesList`.

        :param track: name of the track.
        :param includeDoubleFrequencies: If True, all measurement data are returned, if False, only the largest non-overlapping area is returned. Defaults to False.
        :returns: Numpy array with the track.
        """
        return self._arraySlice(self._tracks[track], includeDoubleFrequencies)

    def getFileName(self) -> str:
        """
        Get the name of the file which contains the impedance.

        :returns: The filename if the file was opened or "FromBytes.zmx" if it was created from bytes.
        """
        return self._zmxFile.getFileName()

    def getBinaryFileContent(self) -> bytes:
        """
        Get the content of the file which contains the impedance.

        The whole file is returned, with all impedances.

        :returns: bytes with the file content.
        """
        return self._zmxFile.getBinaryFileContent()

    def save(self, filename: str):
        """
        Save the file which contains the impedance.

        The whole file is saved, with all impedances.

        :param filename: Path and filename of the file to be saved with the extension .zmx.
        """
        self._zmxFile.save(filename)
        return

    def _arraySlice(
        self, array: np.ndarray, includeDoubleFrequencies: bool = False
    ) -> np.ndarray:
        """
        Can return the array range without duplicate frequency support points.

        For numpy and other libraries there must not be any duplicate frequency support points,
        therefore this function trims the array range and sorts it by ascending frequency.

        :param array: Array that is processed.
        :param includeDoubleFrequencies: If True, all measurement data are returned, if False, only the largest non-overlapping area is returned. Defaults to False.
        :return: The eventually trimmed array.
        """
        if includeDoubleFrequencies:
            return array

        retval = array[self._fromIndex : self._toIndex]
        if self._swapNecessary:
            return np.flip(retval)
        return retval

    def __str__(self) -> str:
        return f"{self.getDimensionName()} ({self._name})"


class ZmxImport:
    """
    Class to be able to read .zmx files with Python.

    .zmx files are written by the Zahner Lab software for measurements with the IM7.
    The file is read with the Python package `zahner_link <https://pypi.org/project/zahner-link/>`_.

    A measurement can contain more than one impedance, for example one per PAD4 channel in
    addition to the impedance of the cell. Each impedance is available as
    :class:`ZmxImpedance` object.

    .. code-block:: python

        zmxData = ZmxImport("randles_pad42.zmx")

        for impedance in zmxData.getImpedances():
            print(impedance.getDimensionName(), impedance.getName())

    :param filename: The path to the zmx file, or the zmx file as bytes or bytearray.
    """

    def __init__(self, filename: Union[str, bytes, bytearray]):
        self._filename = "FromBytes.zmx"
        if isinstance(filename, (bytes, bytearray)):
            self._binaryFileContent = bytes(filename)
        else:
            _, self._filename = os.path.split(filename)
            with open(filename, "rb") as f:
                self._binaryFileContent = f.read()

        imported = zahner_link.xml.ZXmlImporter().import_from_memory_as_measurement(
            self._binaryFileContent
        )
        if isinstance(imported, zahner_link.ErrorObject):
            raise ValueError(f"{self._filename} can not be read: {imported}")

        self._impedances: list[ZmxImpedance] = []
        for dataset in imported.object.get_datasets():
            if not isinstance(dataset, zahner_link.EisDataset):
                continue

            frequency = np.array(dataset.get_frequencies())
            times = np.array(dataset.get_times())
            for name in dataset.get_impedances_names():
                self._impedances.append(
                    ZmxImpedance(
                        self,
                        dataset.get_impedance_data_by_name(name),
                        frequency,
                        times,
                    )
                )

        if len(self._impedances) == 0:
            raise ValueError(f"{self._filename} contains no impedance spectrum")
        return

    def getImpedances(self) -> list[ZmxImpedance]:
        """
        Get all impedances of the measurement.

        :returns: List with the impedances.
        """
        return list(self._impedances)

    def getImpedanceNames(self) -> list[str]:
        """
        Get the names of all impedances of the measurement.

        These are the names which are passed to :meth:`getImpedance`.

        :returns: List with the names.
        """
        return [impedance.getName() for impedance in self._impedances]

    def getImpedance(self, name: Optional[str] = None) -> ZmxImpedance:
        """
        Get one impedance of the measurement.

        The impedance can be selected by its name, see :meth:`ZmxImpedance.getName`, or by its
        dimensions, see :meth:`ZmxImpedance.getDimensionName`, for example "padx[1].ch1/current".
        If the measurement contains more than one spectrum, the first impedance found is returned,
        which is also the one the Zahner Analysis fits.

        Without a name, the only impedance is returned. If there are several, the impedance of the
        cell "voltage/current" is returned.

        :param name: The name of the impedance or None.
        :returns: The impedance.
        """
        if name is None:
            if len(self._impedances) == 1:
                return self._impedances[0]
            name = "voltage/current"

        for impedance in self._impedances:
            if impedance.getName() == name:
                return impedance
        for impedance in self._impedances:
            if impedance.getDimensionName() == name:
                return impedance

        names = ", ".join(f'"{n}"' for n in self.getImpedanceNames())
        raise KeyError(
            f'There is no impedance called "{name}" in {self._filename}. It holds: {names}'
        )

    def getFileName(self) -> str:
        """
        Get the name of the file.

        :returns: The filename if the file was opened or "FromBytes.zmx" if it was created from bytes.
        """
        return self._filename

    def getBinaryFileContent(self) -> bytes:
        """
        Get the content of the file binary.

        :returns: bytes with the file content.
        """
        return self._binaryFileContent

    def save(self, filename: str):
        """
        Save the file.

        Only the file content that has been read is saved.

        :param filename: Path and filename of the file to be saved with the extension .zmx.
        """
        with open(filename, "wb") as f:
            f.write(self._binaryFileContent)
        return

    def __getitem__(self, name: str) -> ZmxImpedance:
        """
        Get one impedance by its name with the []-operator.

        :param name: The name of the impedance, see :meth:`getImpedance`.
        :returns: The impedance.
        """
        return self.getImpedance(name)

    def __iter__(self):
        return iter(self._impedances)

    def __len__(self) -> int:
        return len(self._impedances)
