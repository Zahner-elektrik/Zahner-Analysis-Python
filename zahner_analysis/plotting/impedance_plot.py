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
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter
import numpy as np
from zahner_analysis.file_import.ism_import import IsmImport


def bodePlotter(
    axes=None,
    frequencies=None,
    Z=None,
    impedanceAbsolute=None,
    phase=None,
    impedanceObject=None,
    zTogetherPhase=True,
    absPhase=True,
    argsImpedanceAxis={},
    argsPhaseAxis={},
):
    """Plot of an impedance spectrum in Bode representation

    If no axes are passed, a new figure is created. Here you can decide whether impedance and phase are to be displayed in the same plot.
    The figure object and the axis objects are always returned.

    Either the complex impedance can be transferred with the parameter Z or impedance and phase can be transferred separately.
    The phase must be passed in radians, not in degrees. By default, the amount of the phase is displayed - this can be switched off.

    With argsImpedanceAxis and argsPhaseAxis the appearance of the lines and the plot can be influenced.
    These values are dictionaries which are parameterised like the matplotlib plotting functions.
    The possible configurations can be found in the Matplotlib `Line2D properties documentation <https://matplotlib.org/3.5.0/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D>`_.

    The following code section shows the dictionaries with the default axis configuration, which can be overwritten and extended.

    .. code-block:: python

        defaultImpedanceFormat = {"linestyle":'dashed',
                              "linewidth":1,
                              "marker":"o",
                              "markersize":5,
                              "fillstyle":"none",
                              "color":"blue"}

        defaultPhaseFormat = {"linestyle":'dashed',
                                "linewidth":1,
                                "marker":"o",
                                "markersize":5,
                                "fillstyle":"none",
                                "color":"red"}


    The application could look like the following example, in which two spectra are plotted in bode representation and a legend is added.

    .. code-block:: python

        (fig, axes) = bodePlotter(None, frequencies, Z=firstImpedances)
        (fig, axes) = bodePlotter(axes, frequencies, Z=secondImpedances,
                               argsImpedanceAxis={"color": "green"}, argsPhaseAxis={"marker": "x"})

        (impedanceAxis, phaseAxis) = axes
        impedanceAxis.legend(["first spectra", "second spectra"])

        plt.show()

        (fig, (impedanceAxis, phaseAxis)) = bodePlotter(impedanceObject=IsmImport(r"path/to/file"))

        plt.show()


    :param axes: Tuple of impedance and phase axis (impedanceAxis, phaseAxis). If None is passed, a new figure with corresponding axes is created.
    :param frequencies: Array with the frequency points.
    :param Z: Array with the complex impedances. Either the parameter Z must be passed or impedanceAbsolute and phase must be passed.
    :param impedanceAbsolute: Array with the impedance absolute values. Either the parameter Z must be passed or impedanceAbsolute and phase must be passed.
    :param phase: Array with the phase values in radians. Either the parameter Z must be passed or impedanceAbsolute and phase must be passed.
    :param zTogetherPhase: If this parameter is True, impedance and phase are displayed in a plot. If False, impedance and phase are shown in separate subplots.
        This parameter only has meaning if the parameter axes is None.
    :param absPhase: If True, the absolute value of the phase is displayed.
    :param argsImpedanceAxis: Standard Matplotlib `Line2D properties <https://matplotlib.org/3.5.0/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D>`_ as dictionary,
        which are passed into the plotting functions, for example to adjust colours and line widths.
    :param argsPhaseAxis: Standard Matplotlib `Line2D properties <https://matplotlib.org/3.5.0/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D>`_ as dictionary,
        which are passed into the plotting functions, for example to adjust colours and line widths.
    :return: A tuple with a figure and a tuple of axis objects is returned. figure, (impedanceAxis, phaseAxis)
    """

    if axes is None:
        if zTogetherPhase:
            fig, (impedanceAxis) = plt.subplots(1, 1)
            phaseAxis = impedanceAxis.twinx()
        else:
            fig, (impedanceAxis, phaseAxis) = plt.subplots(2, 1, sharex=True)
    else:
        (impedanceAxis, phaseAxis) = axes
        fig = impedanceAxis.get_figure()

    frequencies, Z, impedanceAbsolute, phase = _impedanceParameterAssociation(
        frequencies=frequencies,
        Z=Z,
        impedanceAbsolute=impedanceAbsolute,
        phase=phase,
        impedanceObject=impedanceObject,
    )

    defaultImpedanceFormat = {
        "linestyle": "dashed",
        "linewidth": 1,
        "marker": "o",
        "markersize": 5,
        "fillstyle": "none",
        "color": "blue",
    }

    for key in defaultImpedanceFormat.keys():
        if key not in argsImpedanceAxis:
            argsImpedanceAxis[key] = defaultImpedanceFormat[key]

    impedanceAxis.loglog(frequencies, np.abs(impedanceAbsolute), **argsImpedanceAxis)
    impedanceAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    impedanceAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    impedanceAxis.set_xlabel(r"f")
    impedanceAxis.set_ylabel(r"|Z|")
    if zTogetherPhase:
        impedanceAxis.yaxis.label.set_color(argsImpedanceAxis["color"])
    impedanceAxis.grid(which="both", linestyle="dashed", linewidth=0.5)
    impedanceAxis.set_xlim([min(frequencies) * 0.8, max(frequencies) * 1.2])

    if absPhase:
        phaseToPlot = np.abs(phase * (360 / (2 * np.pi)))
        phaseLabel = r"|Phase|"
    else:
        phaseToPlot = phase * (360 / (2 * np.pi))
        phaseLabel = r"Phase"

    defaultPhaseFormat = {
        "linestyle": "dashed",
        "linewidth": 1,
        "marker": "o",
        "markersize": 5,
        "fillstyle": "none",
        "color": "red",
    }

    for key in defaultPhaseFormat.keys():
        if key not in argsPhaseAxis:
            argsPhaseAxis[key] = defaultPhaseFormat[key]

    phaseAxis.semilogx(frequencies, phaseToPlot, **argsPhaseAxis)
    phaseAxis.yaxis.set_major_formatter(EngFormatter(unit="$°$", sep=""))
    phaseAxis.xaxis.set_major_formatter(EngFormatter(unit="Hz"))
    phaseAxis.set_xlabel(r"f")
    phaseAxis.set_ylabel(phaseLabel)

    if _checkForTwinAx(phaseAxis) is False:
        phaseAxis.grid(which="both", linestyle="dashed", linewidth=0.5)
    else:
        phaseAxis.yaxis.label.set_color(argsPhaseAxis["color"])

    if absPhase is True:
        phaseAxis.set_ylim([0, 90])

    return fig, (impedanceAxis, phaseAxis)


def nyquistPlotter(
    ax=None,
    Z=None,
    impedanceAbsolute=None,
    phase=None,
    impedanceObject=None,
    frequenciesToAnnotate=None,
    minusNyquist=True,
    maximumAbsImpedance=None,
    argsNyquistAxis={},
):
    """Plot of an impedance spectrum in Nyquist representation

    If no axis is passed, a new figure is created, otherwise, it is plotted on this axis.
    The figure object and the axis objects are always returned.

    Either the complex impedance can be transferred with the parameter Z or impedance and phase can be transferred separately.
    The phase must be passed in radians, not in degrees.
    minusNyquist is True by default and the graph with conjugate complex data is displayed as a -Nyquist plot.

    It is also possible to write text in the diagram, for example to label selected points in the Nyquist diagram with the frequency.
    The following is an excerpt from an application example.

    .. code-block:: python

        annotations = []
        for i in [0, 5, 15, 40, 44]:
            annotations.append([frequencies[i], Z[i], {"fontsize":8}])

        (fig, ax) = nyquistPlotter(None, frequenciesToAnnotate=annotations, Z=Z, maximumAbsImpedance=0.005)
        plt.show()

        (fig, ax) = nyquistPlotter(None, frequenciesToAnnotate=annotations, Z=Z,
                                minusNyquist=False, maximumAbsImpedance=0.005)

        (fig, ax) = nyquistPlotter(ax, Z=Z2,
                                argsNyquistAxis={"color": "blue", "marker": "x"},
                                minusNyquist=False, maximumAbsImpedance=0.005)
        ax.legend(["first impedance Z1", "second impedance Z2"])
        plt.show()

        (fig, axes) = nyquistPlotter(impedanceObject=IsmImport(r"path/to/file"))

        plt.show()

    :param axes: Axis on which to plot or None.. If None is passed, a new figure with corresponding axes is created.
    :param Z: Array with the complex impedances. Either the parameter Z must be passed or impedanceAbsolute and phase must be passed.
    :param impedanceAbsolute: Array with the impedance absolute values. Either the parameter Z must be passed or impedanceAbsolute and phase must be passed.
    :param phase: Array with the phase values in radians. Either the parameter Z must be passed or impedanceAbsolute and phase must be passed.
    :param frequenciesToAnnotate: Points with labels in the diagram for frequencies, for example. [[text,Z,formattingDict],[],...]
        For formatting the points with the formattingDict can be found in the  `Matplotlib annotate documentation <https://matplotlib.org/3.5.0/api/_as_gen/matplotlib.pyplot.annotate.html#matplotlib.pyplot.annotate>`_ .
        This parameter can also be omitted and an array can be passed with text and complex impedance only.
    :param minusNyquist: If this value is True, the imaginary part is displayed inverted -Nyquist plot. This is the default.
    :param maximumAbsImpedance: Maximum absolute impedance up to which the data points are plotted.
    :param argsNyquistAxis: Standard Matplotlib `Line2D properties <https://matplotlib.org/3.5.0/api/_as_gen/matplotlib.lines.Line2D.html#matplotlib.lines.Line2D>`_ as dictionary,
        which are passed into the plotting functions, for example to adjust colours and line widths.
    :return: A tuple with a figure and a tuple of axis objects is returned. figure, nyquistAxis
    """

    if ax is None:
        fig, (nyquistAxis) = plt.subplots(1, 1)
    else:
        nyquistAxis = ax
        fig = nyquistAxis.get_figure()

    _, Z, impedanceAbsolute, phase = _impedanceParameterAssociation(
        frequencies=None,
        Z=Z,
        impedanceAbsolute=impedanceAbsolute,
        phase=phase,
        impedanceObject=impedanceObject,
        frequenciesRequired=False,
    )

    defaultImpedanceFormat = {
        "linestyle": "dashed",
        "linewidth": 1,
        "marker": "o",
        "markersize": 5,
        "fillstyle": "none",
        "color": "#2e8b57",
    }

    for key in defaultImpedanceFormat.keys():
        if key not in argsNyquistAxis:
            argsNyquistAxis[key] = defaultImpedanceFormat[key]

    if minusNyquist:
        Z = np.conj(Z)

    if maximumAbsImpedance is not None:
        Z = [x for x in Z if np.abs(x) < maximumAbsImpedance]

    nyquistAxis.plot(np.real(Z), np.imag(Z), **argsNyquistAxis)
    nyquistAxis.grid(which="both", linestyle="dashed", linewidth=0.5)
    nyquistAxis.set_aspect("equal")
    nyquistAxis.xaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    nyquistAxis.yaxis.set_major_formatter(EngFormatter(unit="$\Omega$"))
    nyquistAxis.set_xlabel(r"$Z_{\rm re}$")

    if minusNyquist:
        nyquistAxis.set_ylabel(r"$-Z_{\rm im}$")
    else:
        nyquistAxis.set_ylabel(r"$Z_{\rm im}$")

    formatter = EngFormatter(places=2, unit="Hz")

    if frequenciesToAnnotate is not None:
        for anon in frequenciesToAnnotate:
            if len(anon) == 3:
                additionalArgs = anon[2]
            else:
                additionalArgs = {}

            if minusNyquist:
                factor = -1.0
            else:
                factor = 1.0
            nyquistAxis.annotate(
                formatter.format_data(anon[0]),
                (np.real(anon[1]), factor * np.imag(anon[1])),
                **additionalArgs
            )

    return fig, nyquistAxis


def _impedanceParameterAssociation(
    frequencies=None,
    Z=None,
    impedanceAbsolute=None,
    phase=None,
    impedanceObject=None,
    frequenciesRequired=True,
):

    if impedanceObject is not None:
        # Impedance file is preferred.
        frequencies = impedanceObject.getFrequencyArray()
        Z = impedanceObject.getComplexImpedanceArray()
        impedanceAbsolute = impedanceObject.getImpedanceArray()
        phase = impedanceObject.getPhaseArray()
    elif Z is not None:
        # Second possibility Z and frequency is available.
        impedanceAbsolute = np.abs(Z)
        phase = np.angle(Z)
    elif impedanceAbsolute is not None and phase is not None:
        Z = np.cos(phase) * impedanceAbsolute + 1j * np.sin(phase) * impedanceAbsolute
    else:
        raise ValueError(
            "impedanceObject or Z or (impedanceAbsolute and phase) required"
        )

    if frequenciesRequired is True and frequencies is None:
        raise ValueError("frequency parameter is required")

    return frequencies, Z, impedanceAbsolute, phase


def _checkForTwinAx(axis):
    retval = False
    for ax in axis.figure.axes:
        if ax is axis:
            continue
        if ax.bbox.bounds == axis.bbox.bounds:
            retval = True
    return retval
