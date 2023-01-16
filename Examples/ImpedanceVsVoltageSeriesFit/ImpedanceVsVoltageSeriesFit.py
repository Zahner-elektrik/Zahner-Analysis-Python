from zahner_analysis.analysis_tools.eis_fitting import EisFitting
from zahner_analysis.file_import.impedance_model_import import IsfxModelImport
from zahner_analysis.file_import.ism_import import IsmImport
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter

import os
import glob
import re

if __name__ == "__main__":
    impedanceCircuitModel = IsfxModelImport(r"diode-ac-model.isfx")
    print(impedanceCircuitModel)

    print(f"Resistance initial value: {impedanceCircuitModel['R0']['R'].getValue()}\n")

    fitting = EisFitting()

    spectras = glob.glob(os.path.join("measured_spectras", "*_mvdc.ism"))

    measuredVoltageValues = []
    fittedResistanceValues = []

    for spectra in spectras:
        # Fitting the spectra in a loop
        print(f"File: {spectra}")
        fittingResult = fitting.fit(impedanceCircuitModel, IsmImport(spectra))

        # Append arrys with fit results
        voltagePattern = r"(\d+)_mvdc.ism"
        voltage = float(re.search(voltagePattern, spectra)[1]) / 1000.0
        measuredVoltageValues.append(voltage)
        fittedResistanceValue = fittingResult.getFittedModel()["R0"]["R"].getValue()
        fittedResistanceValues.append(fittedResistanceValue)

        voltageFormatter = EngFormatter(unit="V", sep=" ")
        resistanceFormatter = EngFormatter(unit="Ω", sep=" ")
        print(
            f"Voltage: {voltageFormatter.format_data(voltage)} Fitted Resistance: {resistanceFormatter.format_data(fittedResistanceValue)}"
        )

        # Save the fit results
        filename = os.path.splitext(os.path.split(spectra)[1])[0]
        fittingResult.save(path="fitted_spectras", foldername=filename)

        # Setting the new model for the next fit
        impedanceCircuitModel = fittingResult.getFittedModel()

    fig, (ax) = plt.subplots(1, 1)

    ax.semilogy(measuredVoltageValues, fittedResistanceValues)
    ax.xaxis.set_major_formatter(EngFormatter(unit="V"))
    ax.yaxis.set_major_formatter(EngFormatter(unit="Ω"))
    ax.set_xlabel(r"Voltage across the diode")
    ax.set_ylabel(r"Differential Resistance")
    ax.grid(which="both", linestyle="--", linewidth=0.5)
    fig.set_size_inches(12, 10)
    fig.savefig("RvsU.svg")
    plt.show()
