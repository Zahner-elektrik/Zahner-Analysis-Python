from zahner_analysis.analysis_tools.eis_fitting import EisFitting
from zahner_analysis.file_import.impedance_model_import import IsfxModelImport
from zahner_analysis.file_import.ism_import import IsmImport
from zahner_analysis.plotting.impedance_plot import bodePlotter
import matplotlib.pyplot as plt

if __name__ == "__main__":
    fitting = EisFitting()

    dataWithDrift = IsmImport("drift.ism")
    dataWithZHIT = fitting.zhit(dataWithDrift)

    (fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(impedanceObject=dataWithDrift)
    (fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(
        (impedanceAxis1, phaseAxis1),
        impedanceObject=dataWithZHIT,
        argsImpedanceAxis={"linestyle": "solid", "marker": None},
        argsPhaseAxis={"linestyle": "solid", "marker": None},
    )
    phaseAxis1.legend(["Original", "ZHIT"])
    fig1.set_size_inches(18, 10)

    fitParams = {
        "DataSource": "zhit",
        "Smoothness": 0.0002,
        "NumberOfSamples": 40,
    }

    impedanceCircuitModel = IsfxModelImport("RC-R-L.isfx")
    fittingResult = fitting.fit(
        impedanceCircuitModel, dataWithDrift, fitParams=fitParams
    )
    print(fittingResult)

    (fig2, (impedanceAxis2, phaseAxis2)) = bodePlotter(impedanceObject=dataWithDrift)
    (fig2, (impedanceAxis2, phaseAxis2)) = bodePlotter(
        (impedanceAxis2, phaseAxis2),
        impedanceObject=fittingResult.getFittedSimulatedData(),
        argsImpedanceAxis={"linestyle": "solid", "marker": None},
        argsPhaseAxis={"linestyle": "solid", "marker": None},
    )
    (fig2, (impedanceAxis2, phaseAxis2)) = bodePlotter(
        (impedanceAxis2, phaseAxis2),
        impedanceObject=fittingResult.getFitInputData(),
        argsImpedanceAxis={"linestyle": "None", "marker": "x"},
        argsPhaseAxis={"linestyle": "None", "marker": "x"},
    )

    phaseAxis2.legend(["Original", "Fitted", "ZHIT"])
    fig2.set_size_inches(18, 10)

    fittingResult.getFitInputData().save("ZHIT.ism")

    plt.show()
