from zahner_analysis.analysis_tools.setup_compensation import SetupCompensation
from zahner_analysis.plotting.impedance_plot import bodePlotter
from zahner_analysis.file_import.ism_import import IsmImport
from zahner_analysis.file_export.ism_export import IsmExport
import matplotlib.pyplot as plt

if __name__ == "__main__":
    originalData = IsmImport("./ExampleData/500uR_measurement_pro.ism")

    compensatedDataFileName = (
        "./ExampleData/500uR_measurement_pro_short_compensated.ism"
    )

    compensationData = SetupCompensation(
        shortData="./ExampleData/short_circuit_measurement_pro.ism",
        openData=None,
        loadData=None,
        referenceData=None,
    )

compensationData.setSmoothingWindowLength(3)
compensationData.setSmoothingPolyOrder(2)

compensatedData = compensationData.compensateIsm(originalData)

(fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(
    impedanceObject=originalData,
    zTogetherPhase=False,
    absPhase=False,
    argsImpedanceAxis={"marker": None},
    argsPhaseAxis={"marker": None},
)

(fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(
    (impedanceAxis1, phaseAxis1),
    impedanceObject=compensatedData,
    zTogetherPhase=False,
    absPhase=False,
    argsImpedanceAxis={"linestyle": "solid", "marker": None},
    argsPhaseAxis={"linestyle": "solid", "marker": None},
)

impedanceAxis1.legend(["Measured Data", "Compensated Data"])
phaseAxis1.legend(["Measured Data", "Compensated Data"])

impedanceAxis1.set_ylim([250e-6, 1e-3])
phaseAxis1.set_ylim([-15.0, +45.0])

fig1.set_size_inches(18, 10)
plt.show()

exportFile = IsmExport(compensatedData)
exportFile.writeToFile(compensatedDataFileName)

