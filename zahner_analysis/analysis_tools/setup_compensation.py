from zahner_analysis.file_import.ism_import import IsmImport
from scipy.signal import savgol_filter
import numpy as np
import copy
from typing import Union, Optional


def interpolateIsmToImpedanceArray(
    ism: IsmImport, frequencyPoints: list[float]
) -> np.array:
    """
    Function for the interpolation of spectra.

    :param ism: Object with spectrum.
    :param frequencyPoints: Frequency points which are to be interpolated.
    :return: Array with interpolated impedance points.
    """
    return np.interp(
        frequencyPoints, ism.getFrequencyArray(), ism.getComplexImpedanceArray()
    )


def smoothIsm(ism: IsmImport, window_length: int, polyorder: int) -> IsmImport:
    """
    Smoothen the ism data with a savgol filter.

    https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_filter.html

    :param ism: ism data which are smoothed.
    :param window_length: Window length for smoothening.
    :param polyorder: Polynomial order must be greater than window length.
    :return: Smoothed ism data.
    """
    freqArray = ism.getFrequencyArray()
    ism.frequency = freqArray
    ism.impedance = savgol_filter(ism.getImpedanceArray(), window_length, polyorder)
    ism.phase = savgol_filter(ism.getPhaseArray(), window_length, polyorder)
    ism.fromIndex = 0
    ism.toIndex = len(ism.impedance)
    ism.swapNecessary = False
    return ism


class SetupCompensation(object):
    r"""
    Object which contains the data and methods to compensate ism data.

    ⚠️WARNING⚠️

    * **The results must be checked for plausibility, since incorrectly performed short, open and load measurements can also degrade the measurement results.**

    * **With a second measurement of a known object it must be verified if the compensation works or if it worsens the result.**

    * **The cable routing must not change after the calibration measurement. Since the cable routing and its impedance and parasitic properties are part of the calibration data.**

    * **For the best possible correction, the point density of the calibration measurements must be greater than or equal to that of the measurement to be corrected.**

    * **The calibration data are smoothed before the calculation, for this the window length and the polynomial order must be defined.**

    * **The order of the polynomial and the length of the window must be set by the user, this affects the result.**

    The formulas for the correction were derived from a theoretical four terminal network, which corresponds to the parasitic behavior of the measuring device and the setup.
    This formula is universal. It does not depend on the instrument used:

    .. math::

        Z=\\frac{(Z_{\\text{short}}-Z_{\\text{meas}})(Z_{\\text{load}}-Z_{\\text{open}})}{(Z_{\\text{short}}-Z_{\\text{load}})(Z_{\\text{meas}}-Z_{\\text{open}})} \cdot Z_{\\text{load,ref}}

    .. list-table::
        :widths: 50 50
        :header-rows: 1

        * - Parameter
          - Description
        * - :math:`Z_{\\text{short}}`
          - Measurement without object. Short-circuited 4-wire test setup. CE, RE, WE power and WE sense are connected together.
        * - :math:`Z_{\\text{open}}`
          - Measurement without object. CE and RE as well as WE power and WE sense are connected to each other.
        * - :math:`Z_{\\text{load}}`
          - Measurement with a reference object of known defined impedance over the frequency range.
        * - :math:`Z_{\\text{load,ref}}`
          - Real impedance of the reference object of $Z_{\text{load}}$ measurement.
        * - :math:`Z_{\\text{meas}}`
          - Measurement to be corrected.
        * - :math:`Z`
          - Measurement result corrected with the short, open and load data.

    Basic Usage:

    .. code-block::


        originalData = IsmImport("./ExampleData/500uR_measurement_pro.ism")

        compensatedDataFileName = (
            "./ExampleData/500uR_measurement_pro_short_compensated.ism"
        )

        compensationData = SetupCompensation(
            shortData="./ExampleData/short_circuit_measurement_pro.ism"
        )

        compensatedData = compensationData.compensateIsm(originalData)

    :param shortData: short data for correction, defaults to None.
    :param openData: open data for correction, defaults to None.
    :param loadData: load data for correction, defaults to None.
    :param referenceData: real value of load data for correction, defaults to None. Here you can simply pass a number, for example 1 for 1 Ohm reference object.
    :param smoothingWindowLength: Length of the smoothing window, defaults to 5.
    :param smoothingPolyOrder: Length of the smoothing poly, defaults to 3.
    """

    def __init__(
        self,
        shortData: Optional[Union[IsmImport, str, complex]] = None,
        openData: Optional[Union[IsmImport, str, complex]] = None,
        loadData: Optional[Union[IsmImport, str, complex]] = None,
        referenceData: Optional[Union[IsmImport, str, complex]] = None,
        smoothingWindowLength: Optional[int] = 5,
        smoothingPolyOrder: Optional[int] = 3,
    ):
        if shortData is None:
            self.shortData = 0 + 0j
        else:
            if isinstance(shortData, str):
                self.shortData = IsmImport(shortData)
            else:
                self.shortData = shortData

        if openData is None:
            self.openData = 1e15 + 0j
        else:
            if isinstance(openData, str):
                self.openData = IsmImport(openData)
            else:
                self.openData = openData

        if loadData is None and referenceData is None:
            self.loadData = 1 + 0j
            self.referenceData = 1 + 0j

        elif loadData is not None and referenceData is not None:
            if isinstance(loadData, str):
                self.loadData = IsmImport(loadData)
            else:
                self.loadData = loadData

            if isinstance(referenceData, str):
                self.referenceData = IsmImport(referenceData)
            elif isinstance(referenceData, IsmImport):
                self.referenceData = referenceData
            else:
                self.referenceData = referenceData
        else:
            raise ValueError("loadData requiers referenceData")

        self.smoothingWindowLength = smoothingWindowLength
        self.smoothingPolyOrder = smoothingPolyOrder
        return

    def setSmoothingWindowLength(self, value: int):
        """
        Sets the length of the smoothing window. Must be smaller than the poly length.

        :param value: Length of the smoothing window.
        """
        self.smoothingWindowLength = value
        return

    def getSmoothingWindowLength(self) -> int:
        """
        Length of the smoothing window.

        :return: Length of the smoothing window.
        """
        return self.smoothingWindowLength

    def setSmoothingPolyOrder(self, value: int):
        """
        Sets the length of the smoothing polynomial. Must be greater than the window length.

        :param value: Length of the smoothing poly.
        """
        self.smoothingPolyOrder = value
        return

    def getSmoothingPolyOrder(self) -> int:
        """
        Length of the smoothing poly.

        :return: Length of the smoothing poly.
        """
        return self.smoothingPolyOrder

    def compensateIsm(
        self, ism: Union[IsmImport, str], conjugateShort: bool = False
    ) -> IsmImport:
        """
        Compensate ism Data.

        This function can be used to apply the Short Open and Load data to the passed impedance data.
        You can then call this function several times to correct different data with the same data.

        :param ism: Data which are to be compensated.
        :param conjugateShort: Conjugate the short data., defaults to False.
        :return: Impedance object which was compensated.
        """
        if isinstance(ism, str):
            ism = IsmImport(ism)

        Zism = ism.getComplexImpedanceArray()

        if isinstance(self.shortData, IsmImport):
            Zshort = interpolateIsmToImpedanceArray(
                smoothIsm(
                    self.shortData, self.smoothingWindowLength, self.smoothingPolyOrder
                ),
                ism.getFrequencyArray(),
            )
        else:
            Zshort = np.array([self.shortData for _ in ism.getFrequencyArray()])

        if isinstance(self.openData, IsmImport):
            Zopen = interpolateIsmToImpedanceArray(
                smoothIsm(
                    self.openData, self.smoothingWindowLength, self.smoothingPolyOrder
                ),
                ism.getFrequencyArray(),
            )
        else:
            Zopen = np.array([self.openData for _ in ism.getFrequencyArray()])

        if isinstance(self.loadData, IsmImport):
            Zload = interpolateIsmToImpedanceArray(
                smoothIsm(
                    self.loadData, self.smoothingWindowLength, self.smoothingPolyOrder
                ),
                ism.getFrequencyArray(),
            )
        else:
            Zload = np.array([self.loadData for _ in ism.getFrequencyArray()])

        if isinstance(self.referenceData, IsmImport):
            Zreference = interpolateIsmToImpedanceArray(
                smoothIsm(
                    self.referenceData,
                    self.smoothingWindowLength,
                    self.smoothingPolyOrder,
                ),
                ism.getFrequencyArray(),
            )
        else:
            Zreference = np.array([self.referenceData for _ in ism.getFrequencyArray()])

        if conjugateShort == True:
            Zshort = np.conjugate(Zshort)

        Zcompensated = (
            ((Zshort - Zism) * (Zload - Zopen)) / ((Zism - Zopen) * (Zshort - Zload))
        ) * Zreference

        compensatedIsm = copy.deepcopy(ism)
        compensatedIsm.frequency = ism.getFrequencyArray()
        compensatedIsm.impedance = np.abs(Zcompensated)
        compensatedIsm.phase = np.angle(Zcompensated)
        compensatedIsm.fromIndex = 0
        compensatedIsm.toIndex = len(compensatedIsm.impedance)
        compensatedIsm.swapNecessary = False

        return compensatedIsm
