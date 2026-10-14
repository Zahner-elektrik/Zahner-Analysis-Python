from zahner_analysis.analysis_tools.eis_fitting import EisFitting, EisFittingPlotter
from zahner_analysis.file_import.impedance_model_import import IsfxModelImport
from zahner_analysis.file_import.zmx_import import ZmxImport
import matplotlib.pyplot as plt
import re

impedanceCircuitModel = IsfxModelImport("randles.isfx")
zmxData = ZmxImport("randles_pad42.zmx")

print(impedanceCircuitModel)

for impedance in zmxData.getImpedances():
    print(f"{impedance.getDimensionName():22} {impedance.getName()}")

cellImpedance = zmxData.getImpedance()
padImpedance = zmxData["padx[1].ch1/current"]

print(f"Cell: {cellImpedance.getDimensionName()}")
print(f"PAD4 channel: {padImpedance.getDimensionName()}")
print(f"Number of frequencies: {len(padImpedance.getFrequencyArray())}")
print(
    f"Frequency range: {min(padImpedance.getFrequencyArray())} Hz to {max(padImpedance.getFrequencyArray())} Hz"
)
print(f"Tracks: {padImpedance.getTrackTypesList()}")

fitting = EisFitting()

fittingResults = {}

for impedance in zmxData.getImpedances():
    fittingResult = fitting.fit(impedanceCircuitModel, impedance)
    fittingResults[impedance.getDimensionName()] = fittingResult

    print(f"Fitted impedance: {fittingResult.getImpedanceName()}")

    foldername = re.sub(r"[^A-Za-z0-9]+", "_", impedance.getDimensionName()).strip("_")
    fittingResult.save(path="fit_results", foldername=foldername)

print(
    f"{'Impedance':22} {'R0':>10} {'R1':>10} {'R2':>10} {'C0':>10} {'C1':>10} {'Error':>8}"
)

for name, fittingResult in fittingResults.items():
    fittedModel = fittingResult.getFittedModel()
    overallError = fittingResult.getFitResultJson()["overall"]["overall_error"]
    print(
        f"{name:22}"
        f" {fittedModel['R0']['R'].getValue():8.3f} Ω"
        f" {fittedModel['R1']['R'].getValue():8.3f} Ω"
        f" {fittedModel['R2']['R'].getValue():8.3f} Ω"
        f" {fittedModel['C0']['C'].getValue():10.3e}"
        f" {fittedModel['C1']['C'].getValue():10.3e}"
        f" {overallError:8.3f}"
    )

fig, (impedanceAxis, phaseAxis) = EisFittingPlotter.plotBode(
    fittingResults["padx[1].ch1/current"], impedanceData=padImpedance
)
impedanceAxis.legend(
    impedanceAxis.get_lines() + phaseAxis.get_lines(),
    2 * ["Measured Data", "Fitted Model"],
)
fig.suptitle("padx[1].ch1/current")
fig.set_size_inches(18, 10)
plt.show()
fig.savefig("fit_results/bode_padx_1_ch1.svg")

fig, axes = plt.subplots(3, 3)

for ax, (name, fittingResult) in zip(axes.flat, fittingResults.items()):
    EisFittingPlotter.plotNyquist(fittingResult, impedanceData=zmxData[name], ax=ax)
    ax.set_title(name)
    ax.legend(["Measured Data", "Fitted Model"])

fig.set_size_inches(18, 8)
fig.tight_layout()
plt.show()
fig.savefig("fit_results/nyquist_all_channels.svg")
