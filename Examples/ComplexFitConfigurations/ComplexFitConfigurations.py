from zahner_analysis.analysis_tools.eis_fitting import EisFitting, EisFittingPlotter
from zahner_analysis.file_import.impedance_model_import import IsfxModelImport
from zahner_analysis.file_import.ism_import import IsmImport
from zahner_analysis.analysis_tools.analysis_connection import AnalysisConnection
from zahner_analysis.plotting.impedance_plot import bodePlotter
import matplotlib.pyplot as plt

if __name__ == "__main__":
    conn = AnalysisConnection(
        ip="127.0.0.1",
        port=8085,
        tryToConnect=True,
        tryToStart=True,
        onlineCheckUrl="/id",
        apiKey="MyKeyToPreventSomeoneElseRemotelyUsingMyAnalysis",
        buffer_size=32768,
        keep_jobs=10,
        timeToWaitForOnline=10,
        keepOpen=True,
    )

    fitting = EisFitting(conn)

    fitParams = {
        "UpperFrequencyLimit": 100000,
        "LowerFrequencyLimit": 1e-6,
        "DataSource": "zhit",  # "original", "smoothed" or "zhit"
        "Smoothness": 0.0002,
        "NumberOfSamples": 20,
    }

    simulationParams = {
        "UpperFrequencyLimit": 10e3,
        "LowerFrequencyLimit": 1e-6,
        "NumberOfSamples": 150,
    }

    impedanceCircuitModel = IsfxModelImport("li-ion-model.isfx")
    impedanceData = IsmImport("li-ion-battery.ism")

    simulatedData = fitting.simulate(impedanceCircuitModel, simulationParams)

    (fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(impedanceObject=impedanceData)
    (fig1, (impedanceAxis1, phaseAxis1)) = bodePlotter(
        (impedanceAxis1, phaseAxis1),
        impedanceObject=simulatedData,
        argsImpedanceAxis={"linestyle": "solid", "marker": None},
        argsPhaseAxis={"linestyle": "solid", "marker": None},
    )
    phaseAxis1.legend(["Measured Data", "Simulated Model with start values"])
    fig1.set_size_inches(18, 10)
    plt.show()

    foldername = "fit_result"

    fig1.savefig(f"{foldername}/bode_not_fitted.png")

    fittingResult = fitting.fit(
        impedanceCircuitModel,
        impedanceData,
        fitParams=fitParams,
        simulationParams=simulationParams,
    )

    print(fittingResult)

    fittingResult.save(
        path="",
        foldername=foldername,
        exist_ok=True,
        saveFitResultJson=True,
        saveFittedModel=True,
        saveFittedSimulatedSamples=True,
        saveFitInputSamples=True,
        fitResultJsonFilename="fit_result.json",
        fittedModelFilename="fitted.isfx",
        fittedSimulatedDataFilename="fitted_simulated.ism",
        fitInputDataFilename="fit_samples.ism",
    )

    (fig2, (impedanceAxis2, phaseAxis2)) = EisFittingPlotter.plotBode(
        fittingResult, impedanceData
    )
    impedanceAxis2.legend(
        impedanceAxis2.get_lines() + phaseAxis2.get_lines(),
        2 * ["Measured Data", "Fitted Model"],
    )
    fig2.set_size_inches(18, 10)
    plt.show()
    fig2.savefig(f"{foldername}/bode_fitted.pdf")

    (fig3, (impedanceAxis3, phaseAxis3)) = EisFittingPlotter.plotBode(
        fittingResult, impedanceData, zTogetherPhase=False, absPhase=False
    )
    impedanceAxis3.legend(["Measured Data", "Fitted Model"])
    phaseAxis3.legend(["Measured Data", "Fitted Model"])
    fig3.set_size_inches(18, 10)
    plt.show()
    fig3.savefig(f"{foldername}/bode.svg")

    (fig4, ax) = EisFittingPlotter.plotNyquist(
        fittingResult, impedanceData, minusNyquist=False, maximumAbsImpedance=0.8
    )
    ax.legend(["Measured Data", "Fitted Model"])
    fig4.set_size_inches(15, 15)
    plt.show()

    fig4.savefig(f"{foldername}/nyquist.jpg")

    simulated = fittingResult.getFittedSimulatedData()

    fig5, (axis) = plt.subplots(1, 1)
    axis.loglog(
        simulated.getFrequencyArray(),
        simulated.getImpedanceArray(),
        marker="o",
        linewidth=0,
        fillstyle="none",
    )
    axis.loglog(
        impedanceData.getFrequencyArray(),
        impedanceData.getImpedanceArray(),
        marker="x",
        linewidth=0,
        fillstyle="none",
    )
    axis.grid("both")
    axis.set_xlabel(r"f")
    axis.set_ylabel(r"|Z|")
    fig5.set_size_inches(18, 10)
    plt.show()
