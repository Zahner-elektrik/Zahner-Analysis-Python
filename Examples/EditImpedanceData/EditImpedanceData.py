from zahner_analysis.file_import.ism_import import IsmImport
from zahner_analysis.plotting.impedance_plot import bodePlotter
import matplotlib.pyplot as plt
from zahner_analysis.file_export.ism_export import IsmExport
import numpy as np

impedanceData = IsmImport("li-ion-battery.ism")

frequencies = impedanceData.getFrequencyArray()
impedanceAbsolut = impedanceData.getImpedanceArray()
phase = impedanceData.getPhaseArray()

(fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(
    frequencies=frequencies,
    impedanceAbsolute=impedanceAbsolut,
    phase=phase,
    zTogetherPhase=False,
)
fig1.set_size_inches(18, 10)
plt.show()

maxFrequency = 1000
try:
    index = next(i for i, freq in enumerate(frequencies) if freq > maxFrequency)
except:
    index = len(frequencies)

frequenciesEdit = frequencies[:index]
impedanceAbsolutEdit = impedanceAbsolut[:index] * 2.0
impedanceAbsolutEdit = np.clip(impedanceAbsolutEdit, 0.08, 1)
phaseEdit = phase[:index] * 1.2

impedanceAbsolutEdit[5] = 4
impedanceAbsolutEdit[10] = 2

frequenciesEdit = np.insert(frequenciesEdit, 0, 10e-6)
impedanceAbsolutEdit = np.insert(impedanceAbsolutEdit, 0, impedanceAbsolutEdit[0])
phaseEdit = np.insert(phaseEdit, 0, phaseEdit[0])

(fig2, (impedanceAxis1, phaseAxis1)) = bodePlotter(
    frequencies=frequencies,
    impedanceAbsolute=impedanceAbsolut,
    phase=phase,
    zTogetherPhase=False,
)
(fig2, (impedanceAxis2, phaseAxis2)) = bodePlotter(
    axes=(impedanceAxis1, phaseAxis1),
    frequencies=frequenciesEdit,
    impedanceAbsolute=impedanceAbsolutEdit,
    phase=phaseEdit,
    zTogetherPhase=False,
    argsImpedanceAxis={"linestyle": "solid", "marker": None},
    argsPhaseAxis={"linestyle": "solid", "marker": None},
)

impedanceAxis2.legend(["Original Data", "Edited Data"])
phaseAxis2.legend(["Original Data", "Edited Data"])

fig2.set_size_inches(18, 10)
plt.show()

exportFile = IsmExport(
    frequency=frequenciesEdit,
    impedance=impedanceAbsolutEdit,
    phase=phaseEdit,
    system_string=impedanceData.getSystemString(),
    potential_string=impedanceData.getStartVoltageString(),
    current_string=impedanceData.getStartCurrentString() ,
    metaData=impedanceData.getMetaData(),
)
exportFile.writeToFile("li-ion-battery-edited.ism")

