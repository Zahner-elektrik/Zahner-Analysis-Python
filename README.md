![Zahner-Analysis-Python](https://doc.zahner.de/github_resources/zahner_analysis.png)

[zahner_analysis](zahner_analysis) is a Python package which uses the [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis) to evaluate measured electrochemical data.

The Python package [zahner_analysis](zahner_analysis) is a client for the [REST interface](https://en.wikipedia.org/wiki/Representational_state_transfer) of the [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis) module *Remote Evaluation*. This module is optional and must be [selected for installation](https://doc.zahner.de/zahner_analysis/analysis_connection.html#basic-informations) when installing the Zahner Analysis.

A equivalent electrical circuit model for an impedance measurement can be easily developed with the graphical interface of the [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis). The *Magic Wand Preset Element Tool* tool is available to determine appropriate initial values for the fit.

![Zahner Analysis Screenshot](https://doc.zahner.de/github_resources/AnalysisScreenshot.png)

With Python the equivalent electrical circuit models, which have been created with the GUI, can be fitted to impedance spectra.
The elements and parameters of the model can be read and processed with Python.

With the Python package [thales_remote](https://github.com/Zahner-elektrik/Thales-Remote-Python) as a supplement, EIS measurements can be performed with a Zennium and immediately evaluated. The [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis) is not required for importing and plotting data with Python.

[IM7](https://zahner.de/products-details/potentiostats/im7x) measurements saved by [Zahner Lab](https://zahner.de/products-details/software/zahner-lab) as zmx files can be fitted as well. If the measurement contains several impedances, for example one per PAD4 channel, each impedance can be fitted on its own.

Additional features are the import of measurement data for CV and I/E measurements (isc and iss files). For this the [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis) is not necessary.

# 📚 Documentation

## Python Package

The complete documentation of the individual functions can be found on the [API documentation website](https://doc.zahner.de/zahner_analysis/).

## REST-API

The REST-API was documented using OpenAPI. The configuration [file](openapi.yaml) is in the repository and the generated html page can be found at the following [url](https://doc.zahner.de/zahner_analysis/analysis_remote.html).

# 🔧 Installation

The package can be installed via pip.

```text
pip install zahner_analysis
```

The [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis) must be downloaded from the [Zahner-Elektrik website](https://zahner.de/products-details/software/Zahner-Analysis) in order to be installed.

# 🔨 Basic Usage

The [Jupyter](https://jupyter.org/) notebook [BasicIntroduction.ipynb](Examples/BasicIntroduction/BasicIntroduction.ipynb) explains the fundamentals of using the library.

```python
"""
Load data and model
"""
impedanceCircuitModel = IsfxModelImport("li-ion-model.isfx")
impedanceData = IsmImport("li-ion-battery.ism")

"""
Create the EisFitting object
"""
fitting = EisFitting()

"""
Fit the equivalent electrical circuit model to the data
"""
fittingResult = fitting.fit(impedanceCircuitModel, impedanceData)

"""
Plot the result
"""
EisFittingPlotter.plotBode(fittingResult)
```

![fittingResult Screenshot](https://doc.zahner.de/github_resources/bode_fitted.png)

# 📖 Examples

The following examples are build on each other, you should read and understand them in sequence.

If measurement data are saved from the examples, they are located in the corresponding directory of the example.

## [BasicIntroduction.ipynb](https://github.com/Zahner-elektrik/Zahner-Analysis-Python/blob/main/Examples/BasicIntroduction/BasicIntroduction.ipynb)

* Load the data and the model
* Fit the model to the data
* Plot the result

## [ComplexFitConfigurations.ipynb](https://github.com/Zahner-elektrik/Zahner-Analysis-Python/blob/main/Examples/ComplexFitConfigurations/ComplexFitConfigurations.ipynb)

* Showing all configuration options
* Customize the connection to Zahner Analysis Software
* Optional fit and simulation parameters
* Optional plotting parameters

## [ImpedanceVsVoltageSeriesFit.ipynb](https://github.com/Zahner-elektrik/Zahner-Analysis-Python/blob/main/Examples/ImpedanceVsVoltageSeriesFit/ImpedanceVsVoltageSeriesFit.ipynb)

* EIS series fit
* Load all files from a directory
* Plot circuit element vs series parameter

## [ZHIT.ipynb](https://github.com/Zahner-elektrik/Zahner-Analysis-Python/blob/main/Examples/ZHIT/ZHIT.ipynb)

* Fit the model to the data
* Load the data and the model
* Perform ZHIT evaluation
* Plot the result

## [FitZmxIM7Data.ipynb](https://github.com/Zahner-elektrik/Zahner-Analysis-Python/blob/main/Examples/FitZmxIM7Data/FitZmxIM7Data.ipynb)

* Load an [IM7](https://zahner.de/products-details/potentiostats/im7x) measurement in the zmx format
* Select the impedances of the cell and of the PAD4 channels
* Fit the model to every impedance
* Compare and plot the results of all channels

## [SetupCompensation.ipynb](https://github.com/Zahner-elektrik/Zahner-Analysis-Python/blob/main/Examples/SetupCompensation/SetupCompensation.ipynb)

* Apply Short-Open-Load correction to EIS data

# 📧 Having a question?

Send an [mail](mailto:support@zahner.de?subject=Zahner-Analysis-Python%20Question&body=Your%20Message) to our support team.

# ⁉️ Found a bug or missing a specific feature?

Feel free to **create a new issue** with a respective title and description on the the [Zahner-Analysis-Python](https://github.com/Zahner-elektrik/Zahner-Analysis-Python/issues) repository.  
If you already found a solution to your problem, **we would love to review your pull request**!

# ✅ Requirements

Programming is done with the latest Python version at the time of commit.

If you work with equivalent circuits and you need the fit and simulate functions, you need the [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis) with its REST interface. To use the REST interface, you need a licensed [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis) with at least version **3.2.1**. The [Zahner Analysis Software](https://zahner.de/products-details/software/Zahner-Analysis) is **not required for importing and plotting** data.

Fitting zmx files of the IM7 requires a [Zahner Analysis](https://zahner.de/products-details/software/Zahner-Analysis) with support for the IM7 file formats. Selecting one of several impedances of a zmx file, for example a PAD4 channel, requires at least version **3.3.9**.

The packages [matplotlib](https://matplotlib.org/), [SciPy](https://scipy.org/) and [NumPy](https://numpy.org/) are used to display the measurement results. The [requests package](https://pypi.org/project/requests/) is necessary to communicate with the Zahner Analysis. The package [zahner_link](https://pypi.org/project/zahner-link/) reads the zmx files of the IM7. Jupyter is not necessary, each example is also available as a Python file.
