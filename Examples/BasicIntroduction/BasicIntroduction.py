from zahner_analysis.analysis_tools.eis_fitting import EisFitting, EisFittingPlotter
from zahner_analysis.file_import.impedance_model_import import IsfxModelImport
from zahner_analysis.file_import.ism_import import IsmImport
import matplotlib.pyplot as plt

impedanceCircuitModel = IsfxModelImport("rc-model.isfx")
impedanceData = IsmImport("rc-data.ism")

print(impedanceCircuitModel)

fitting = EisFitting()

fittingResult = fitting.fit(impedanceCircuitModel, impedanceData)

print(fittingResult)

foldername = "fit_results"
fittingResult.save(foldername=foldername)

(fig2, (impedanceAxis2, phaseAxis2)) = EisFittingPlotter.plotBode(fittingResult)

impedanceAxis2.legend(
    impedanceAxis2.get_lines() + phaseAxis2.get_lines(),
    2 * ["Measured Data", "Fitted Model"],
)

fig2.set_size_inches(18, 10)
plt.show()

fig2.savefig(f"{foldername}/bode.svg")

fittetModel = fittingResult.getFittedModel()

print(
    f"{fittetModel['C0'].getType()}: {fittetModel['C0']['C'].getValue():1.3e} {fittetModel['C0']['C'].getUnit()}"
)
print(
    f"{fittetModel['R0'].getType()}: {fittetModel['R0']['R'].getValue():1.3e} {fittetModel['R0']['R'].getUnit()}"
)

print(f"System: {impedanceData.getSystemString()}")
print(f"Voltage: {impedanceData.getStartVoltageString()}")
print(f"Current: {impedanceData.getStartCurrentString()}")
print(f"Temperature: {impedanceData.getStartTemperatureString()}")
print(f"Time window: {impedanceData.getTimeWindowString()}")
print(f"Comment: {impedanceData.getCommentStrings()}")
print(f"Amplitude: {impedanceData.getAmplitude()}")

for track in impedanceData.getTrackTypesList():
    print(track)
    print(impedanceData.getTrack(track)[0:3])

