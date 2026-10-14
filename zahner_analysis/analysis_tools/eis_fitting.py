r"""
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2024 Zahner-Elektrik GmbH & Co. KG

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

from zahner_analysis.file_import.ism_import import IsmImport
from zahner_analysis.file_import.zmx_import import ZmxImport, ZmxImpedance
from zahner_analysis.file_import.impedance_model_import import (
    IsfxModelImport,
    IsfxModelElement,
    IsfxModelElementParameter,
)
from zahner_analysis.plotting.impedance_plot import bodePlotter, nyquistPlotter
from zahner_analysis.analysis_tools.analysis_connection import AnalysisConnection
from zahner_analysis.analysis_tools.error import ZahnerAnalysisError

import os
import re
import json
import io
import logging
import time
from typing import Optional, Union, Any

#: Data which can be fitted: .ism data, a whole .zmx file or one impedance of a .zmx file.
ImpedanceData = Union[IsmImport, ZmxImport, ZmxImpedance]

#: Spectra returned by the Zahner Analysis: .ism data or the impedance of a .zmx file.
ImpedanceSpectrum = Union[IsmImport, ZmxImpedance]

#: Formats in which the Zahner Analysis can return the simulation and the samples.
OUTPUT_FORMATS = ("ism", "zmx")

DUMMY_MODEL = """<?xml version="1.0" encoding="UTF-8"?>
<zahner-impedance-model name="New Model">
    <zahner-fileinfo>
        <type>zahner-impedance-model</type>
        <file-version>3.0</file-version>
        <created>2023-04-13T07:51:22+02:00</created>
        <generator>Zahner Analysis</generator>
        <generator-version>3.3.5</generator-version>
        <comment></comment>
        <app-session>cef8c2e3-250d-47ff-9638-ef58933d107e</app-session>
        <file-id>e0e0c2a4-296f-40d0-9937-58cad6e47464</file-id>
    </zahner-fileinfo>
    <parsed-tree>
        <serial-connect>
            <resistor name="R0">
                <parameter index="0" value="100" fitterFixed="1"/>
            </resistor>
        </serial-connect>
    </parsed-tree>
    <schematics-graph>
        <node pos-x="0" type="1" name="R0" node-id="0" pos-y="-64">
            <parameter value="100" fitterFixed="1" index="0"/>
        </node>
    </schematics-graph>
</zahner-impedance-model>
"""


class EisFittingResult:
    """This class contains the results of the fit.

    The constructor of this class is called by the fit method.

    :param fitResult: Fit result as JSON string.
    :param fittedModel: Model with the fitted parameters.
    :param fittedSimulatedData: Data simulated from the model.
    :param fitInputData: Data used for the fit.
    :param impedanceName: Name of the fitted impedance as reported by the Zahner Analysis.
    """

    def __init__(
        self,
        fitResult: str,
        fittedModel: IsfxModelImport,
        fittedSimulatedData: ImpedanceSpectrum,
        fitInputData: ImpedanceSpectrum,
        impedanceName: str = "",
    ):
        self._fitResult = fitResult
        self._fittedModel = fittedModel
        self._fittedSimulatedData = fittedSimulatedData
        self._fitInputData = fitInputData
        self._impedanceName = impedanceName
        return

    def getFitResultJson(self, fmt="json"):
        """Get the fit result.

        This function returns the fit result as JSON or as string.

        The following is an example of the data returned. For each parameter of each element the value,
        unit, significance and error is returned. Also data for the overall fit result is returned.

        .. code-block:: json

            {
              "model": {
                "C0": {
                  "C": {
                    "error": 15.151926309121153,
                    "significance": 0.032274504286208844,
                    "value": 0.05020110574526214,
                    "value_unit": "F"
                  }
                },
                "CPE0": {
                  "C_eq": {
                    "error": 1.055031648230169,
                    "significance": 0.2519304540206341,
                    "value": 0.06756234793290997,
                    "value_unit": "F"
                  },
                  "α": {
                    "error": 0.5970910562207303,
                    "significance": 0.6845012405311864,
                    "value": 0.7366826808067263,
                    "value_unit": ""
                  }
                },
                "FI0": {
                  "W": {
                    "error": 0.48845055246742036,
                    "significance": 0.6408552251285363,
                    "value": 0.04073380256581006,
                    "value_unit": "Ωs^(-½)"
                  },
                  "k": {
                    "error": 1.9687457791834184,
                    "significance": 0.15899771929695322,
                    "value": 0.0013854241183094132,
                    "value_unit": "1/s"
                  }
                },
                "L0": {
                  "L": {
                    "error": 2.8396295426843867,
                    "significance": 0.6911809622435452,
                    "value": 7.940027736136356e-07,
                    "value_unit": "H"
                  }
                },
                "R0": {
                  "R": {
                    "error": 1.5977793098280266,
                    "significance": 0.07859404364129204,
                    "value": 0.0036204263202214014,
                    "value_unit": "Ω"
                  }
                },
                "R1": {
                  "R": {
                    "error": 0.529684672149924,
                    "significance": 0.9232302468243536,
                    "value": 0.026830261706435942,
                    "value_unit": "Ω"
                  }
                },
                "R2": {
                  "R": {
                    "error": 0.18918999015755764,
                    "significance": 0.4215958599730566,
                    "value": 0.035941054916087775,
                    "value_unit": "Ω"
                  }
                }
              },
              "overall": {
                "impedance_error_max": 1.9436053656746468,
                "impedance_error_mean": 0.14339995178171594,
                "overall_error": 1.1323929422725485,
                "phase_error_max": 0.22001396123330905,
                "phase_error_mean": 0.018250258203149725
              }
            }

        :param fmt: "json" for json, else string.
        :returns: json or string.
        """
        if fmt == "json":
            return self._fitResult
        else:
            return json.dumps(
                self._fitResult, ensure_ascii=False, sort_keys=True, indent=2
            )

    def getFittedModel(self) -> IsfxModelImport:
        """Get the fitted model.

        :returns: The model.
        """
        return self._fittedModel

    def getFittedSimulatedData(self) -> ImpedanceSpectrum:
        """Get the fitted simulated data.

        These data were generated by a simulation of the model.

        The data is an :class:`~zahner_analysis.file_import.ism_import.IsmImport` object if the
        Zahner Analysis returned an .ism file, and a
        :class:`~zahner_analysis.file_import.zmx_import.ZmxImpedance` object if it returned a .zmx file.

        :returns: The data.
        """
        return self._fittedSimulatedData

    def getFitInputData(self) -> ImpedanceSpectrum:
        """Get the samples used for fitting.

        These frequency points from the original data were used for the fit.
        These are the original measurement points used for the fit.
        These points were already smoothed or pre-processed with the ZHIT when it was set.

        The data is an :class:`~zahner_analysis.file_import.ism_import.IsmImport` object if the
        Zahner Analysis returned an .ism file, and a
        :class:`~zahner_analysis.file_import.zmx_import.ZmxImpedance` object if it returned a .zmx file.

        :returns: The data.
        """
        return self._fitInputData

    def getImpedanceName(self) -> str:
        """Get the name of the fitted impedance.

        This is the name the Zahner Analysis shows for the impedance, for example "voltage/current"
        or "padx[1].ch1/current". The name is empty for .ism data, which contains only one impedance.

        :returns: The name.
        """
        return self._impedanceName

    def save(
        self,
        path="",
        foldername="",
        exist_ok=True,
        saveFitResultJson=True,
        saveFittedModel=True,
        saveFittedSimulatedSamples=True,
        saveFitInputSamples=True,
        fitResultJsonFilename="fit_result.json",
        fittedModelFilename="fitted.isfx",
        fittedSimulatedDataFilename=None,
        fitInputDataFilename=None,
    ):
        """Save all fit data.

        With this function, all the results files of the fit can be saved to the hard disk.
        It can be selected what all can be saved with. By default, everything is saved.

        The simulated data and the samples are saved in the format in which the Zahner Analysis
        returned them. Without a filename they are saved as fitted_simulated.ism and
        fit_samples.ism, or as fitted_simulated.zmx and fit_samples.zmx.

        :param path: Path where a folder with the fit results will be created.
            This path can also be relative, as with all paths in Python.
        :param foldername: Name of the folder in which the data will be saved.
        :param exist_ok: Parameter of the os.makedirs function which is used to create the folder.
            If exist_ok is False, an FileExistsError is raised if the target directory already exists.
        :param saveFitResultJson: If true, the json is stored under the filename of the variable fitResultJsonFilename.
        :param saveFittedModel: If true, the model is stored under the filename of the variable fittedModelFilename.
        :param saveFittedSimulatedSamples: If true, the simulated fitted data is stored under the filename of the variable fittedSimulatedDataFilename.
        :param saveFitInputSamples: If true, the samples used for fit are stored under the filename of the variable fitInputDataFilename.
        :param fitResultJsonFilename: Filename for the JSON with the fit result.
        :param fittedModelFilename: Filename for the fitted model.
        :param fittedSimulatedDataFilename: Filename for the data simulated with the model, or None for the default.
        :param fitInputDataFilename: Filename for the data of the points used for the fit, or None for the default.
        """
        if fittedSimulatedDataFilename is None:
            fittedSimulatedDataFilename = "fitted_simulated" + _fileExtension(
                self._fittedSimulatedData
            )
        if fitInputDataFilename is None:
            fitInputDataFilename = "fit_samples" + _fileExtension(self._fitInputData)

        path = os.path.join(path, foldername)
        os.makedirs(path, exist_ok=exist_ok)

        if saveFitResultJson:
            with open(
                os.path.join(path, fitResultJsonFilename), "w", encoding="utf-8"
            ) as f:
                f.write(self.getFitResultJson(fmt="txt"))

        if saveFittedModel:
            self._fittedModel.save(os.path.join(path, fittedModelFilename))

        if saveFittedSimulatedSamples:
            self._fittedSimulatedData.save(
                os.path.join(path, fittedSimulatedDataFilename)
            )

        if saveFitInputSamples:
            self._fitInputData.save(os.path.join(path, fitInputDataFilename))

        return

    def __str__(self):
        """Create string with informations about the model

        When this object is converted to a string, this function is called.

        :returns: A string with the information.
        """
        retval = f"Fitted Model:\n"
        retval += self.getFittedModel().toString()
        retval += "JSON fit result:\n"
        retval += self.getFitResultJson(fmt="txt")

        return retval


class EisFitting:
    """Class which can fit models to impedance spectra.

    This class uses the REST interface of the Zahner Analysis for fitting.


    This class uses the `Python logging module <https://docs.python.org/3/library/logging.html/>`_,
    which can be enabled and output with the following sample configuration.

    .. code-block:: python

        import logging

        if __name__ == "__main__":

            logging.basicConfig(
                filename='logfile.log',
                level=logging.DEBUG,
                format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            )

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
                keepOpen=True)

            fitting = ImpedanceFitting(conn)

    :param analysisConnection: Optional connection object to the Zahner Analysis.
        Not needed if Zahner Analysis is installed locally.
    """

    classAnalysisConnection: AnalysisConnection = None

    def __init__(self, analysisConnection: AnalysisConnection = None):
        self._analysisConnection = analysisConnection

        if self._analysisConnection is None:
            if EisFitting.classAnalysisConnection is None:
                EisFitting.classAnalysisConnection = AnalysisConnection()

            self._analysisConnection = EisFitting.classAnalysisConnection
        return

    def zhit(
        self,
        data: ImpedanceData = None,
        parameters: dict = {},
        timeout: float = None,
        outputFormat: Optional[str] = None,
    ) -> ImpedanceSpectrum:
        """
        Performs the ZHIT evaluation.

        ZHIT is a software tool that uses measured phase data to reconstruct the impedance spectrum.
        The reconstructed impedance spectrum is then compared to the measured impedance spectrum to validate the measurement and identify any artifacts.

        Links to the topic ZHIT:
         * https://en.wikipedia.org/wiki/Z-HIT
         * https://doc.zahner.de/manuals/zahner_analysis.pdf

        Parameter dictionary for optional parameters:

        .. csv-table::
            :header-rows: 1

            Key , Description
            Smoothness , Factor with which smoothed. This must be determined empirically in the GUI.
            NumberOfSamples , Number of samples used for the data. Default all samples.

        .. code-block:: python

            parameters = {
                "Smoothness": 0.0002,
                "NumberOfSamples": 20
            }

        :param data: Data to which the ZHIT is applied. See :meth:`fit` for the possible types.
        :param parameters: Optional parameters for the ZHIT.
        :param timeout: Timeout for the caculation.
        :param outputFormat: Format of the returned data, see :meth:`fit`.
        :returns: The ZHIT data.
        """
        model = IsfxModelImport(xmlString=DUMMY_MODEL)
        parameters = dict(parameters)
        parameters["DataSource"] = "zhit"
        # A fit is performed and then everything is discarded except the data used for the fit.
        fitResult = self.fit(
            model, data, parameters, timeout=timeout, outputFormat=outputFormat
        )
        return fitResult.getFitInputData()

    def fit(
        self,
        model: IsfxModelImport,
        data: ImpedanceData = None,
        fitParams: dict = {},
        simulationParams: dict = {},
        timeout: float = None,
        outputFormat: Optional[str] = None,
    ) -> EisFittingResult:
        """
        Performing the fit.

        With this method the model is fitted to the data.
        The initial values and the model can be easily developed using the Zahner Analysis GUI.

        The data can be:

        * an :class:`~zahner_analysis.file_import.ism_import.IsmImport` object with .ism data,
        * a :class:`~zahner_analysis.file_import.zmx_import.ZmxImpedance` object with one impedance of a .zmx file,
          for example the impedance of one PAD4 channel. The name of the impedance is passed to the
          Zahner Analysis as ImpedanceName.
        * a :class:`~zahner_analysis.file_import.zmx_import.ZmxImport` object, then the Zahner Analysis
          fits the main impedance of the file, which is the impedance of the cell.

        The parameters are optional. You can also use only some optional parameters and omit others.
        Parameter dictionary for optional fit parameters:

        .. csv-table::
            :header-rows: 1

            Key , Description
            UpperFrequencyLimit , Upper frequency limit up to which the data is used for fitting. Default highest frequency.
            LowerFrequencyLimit , Lower frequency limit downto to which the data is used for fitting. Default lowest frequency.
            DataSource , Selection of the data to be used for the fit. "original" or "smoothed" or "zhit". Default "original".
            Smoothness , Factor with which smoothed. This must be determined empirically in the GUI.
            NumberOfSamples , Number of samples used for the fit. Default all samples.
            ImpedanceName , Name of the impedance to fit of a .zmx file. Set automatically for ZmxImpedance objects.

        .. code-block:: python

            fitParams = {
                "UpperFrequencyLimit": 100000,
                "LowerFrequencyLimit": 1e-6,
                "DataSource": "zhit",  # "original", "smoothed" or "zhit"
                "Smoothness": 0.0002,
                "NumberOfSamples": 20
            }

        Parameter dictionary for optional simulation parameters:

        .. csv-table::
            :header-rows: 1

            Key , Description
            UpperFrequencyLimit , Upper frequency limit up to which the model is simulated. Default highest frequency of data.
            LowerFrequencyLimit , Lower frequency limit downto to which the model is simulated. Default lowest frequency of data.
            NumberOfSamples , Number of samples used for the simulation. Default 100.

        .. code-block:: python

            simulationParams = {
                "UpperFrequencyLimit": 10e3,
                "LowerFrequencyLimit": 1e-6,
                "NumberOfSamples": 150
            }

        The simulated data and the samples used for the fit are returned in the format of the data,
        .ism for .ism data and .zmx for .zmx data. With the parameter outputFormat the format can be selected.

        :param model: Model which is fitted to the data.
        :param data: Data to which the model is fitted.
        :param fitParams: Explained in the previous text.
        :param simulationParams: Explained in the previous text.
        :param timeout: Timeout for the fit.
        :param outputFormat: None for the format of the data, "ism" or "zmx".
        :returns: The result of the fit.
        """
        fitParams = dict(fitParams)

        if isinstance(data, ZmxImpedance) and "ImpedanceName" not in fitParams:
            if data.getZmxFile().getImpedance(data.getName()) is not data:
                raise ZahnerAnalysisError(
                    f'The impedance "{data.getName()}" exists more than once in {data.getFileName()}. '
                    "The Zahner Analysis only fits the first one."
                )
            fitParams["ImpedanceName"] = data.getName()

        paramsDict = dict()
        paramsDict["job"] = "EvalEis.Fit"
        paramsDict["parameters"] = {"Fit": fitParams, "Simulation": simulationParams}
        if outputFormat is not None:
            paramsDict["parameters"]["Output"] = {
                "Format": _checkOutputFormat(outputFormat)
            }
        paramsDict["mode"] = "queued"

        jobId = self._startFit(model, data, paramsDict)
        logging.debug("Zahner Analysis job-id: " + jobId)
        status = self._waitForJob(jobId, timeout)

        reportedFitParams = status.get("parameters", {}).get("Fit", {})
        if fitParams.get("ImpedanceName") and "ImpedanceName" not in reportedFitParams:
            raise ZahnerAnalysisError(
                "The Zahner Analysis ignored the ImpedanceName and fitted the main impedance. "
                "Please update the Zahner Analysis to fit other impedances of a .zmx file."
            )

        fittedModel = self._readFittedModel(jobId)
        fittedSimulatedSamples = self._readSimulatedData(jobId)
        fitInputSamples = self._readFitInputData(jobId)

        return EisFittingResult(
            status.get("result"),
            fittedModel,
            fittedSimulatedSamples,
            fitInputSamples,
            reportedFitParams.get("ImpedanceName", ""),
        )

    def _startFit(
        self, model: IsfxModelImport, data: ImpedanceData, params: dict
    ) -> str:
        """
        Function which starts the fit.

        This function sends the model, data and parameters to the Zahner Analysis via HTTP post request.
        The JobId assigned by Zahner Analysis is returned.

        :param model: Model which is fitted to the data.
        :param data: Data to which the model is fitted.
        :param dict: Dictionary {"Fit":fitParams, "Simulation":simulationParams}.
        :returns: JobId
        """
        files = [
            ("eis-file", (data.getFileName(), io.BytesIO(data.getBinaryFileContent()))),
            (
                "model-file",
                (model.getFileName(), io.BytesIO(model.getBinaryFileContent())),
            ),
            ("job", (None, json.dumps(params).encode("utf-8"))),
        ]
        reply = self._analysisConnection.post("/job/start", files=files)
        return self._jobIdFromReply(reply)

    def simulate(
        self,
        model: IsfxModelImport,
        simulationParams: dict,
        timeout: float = None,
        outputFormat: Optional[str] = None,
    ) -> ImpedanceSpectrum:
        """
        Simulate the model.

        With this method, an impedance spectrum is generated from the model.

        Parameter dictionary for simulation parameters:

        .. csv-table::
            :header-rows: 1

            Key , Description
            UpperFrequencyLimit , Upper frequency limit up to which the model is simulated. Default highest frequency of data.
            LowerFrequencyLimit , Lower frequency limit downto to which the model is simulated. Default lowest frequency of data.
            NumberOfSamples , Number of samples used for the simulation. Default 100.

        .. code-block:: python

            simulationParams = {
                "UpperFrequencyLimit": 10e3,
                "LowerFrequencyLimit": 1e-6,
                "NumberOfSamples": 150
            }

        :param model: Model to be simulated.
        :param simulationParams: Explained in the previous text.
        :param timeout: Timeout for the fit.
        :param outputFormat: None or "ism" for .ism data, "zmx" for .zmx data.
        :returns: The simulated data.
        """

        paramsDict = dict()
        paramsDict["job"] = "EvalEis.Sim"
        paramsDict["parameters"] = {"Simulation": simulationParams}
        if outputFormat is not None:
            paramsDict["parameters"]["Output"] = {
                "Format": _checkOutputFormat(outputFormat)
            }
        paramsDict["mode"] = "queued"

        jobId = self._startSimulation(model, paramsDict)
        logging.debug("Zahner Analysis job-id: " + jobId)
        self._waitForJob(jobId, timeout)

        return self._readSimulatedData(jobId)

    def _startSimulation(self, model: IsfxModelImport, params: dict) -> str:
        """
        Function which starts the simulation.

        This function sends the model and parameters to the Zahner Analysis via HTTP post request.
        The JobId assigned by Zahner Analysis is returned.

        :param model: Model to be simulated.
        :param dict: Dictionary {"Simulation":simulationParams}.
        :returns: JobId
        """
        files = [
            (
                "model-file",
                (model.getFileName(), io.BytesIO(model.getBinaryFileContent())),
            ),
            ("job", (None, json.dumps(params).encode("utf-8"))),
        ]
        reply = self._analysisConnection.post("/job/start", files=files)
        return self._jobIdFromReply(reply)

    def _jobIdFromReply(self, reply) -> str:
        """
        Read the JobId from the reply to the start of a job.

        :param reply: Reply of the Zahner Analysis to the post request.
        :returns: JobId
        """
        if reply.status_code != 200:
            logging.error(f"Zahner Analysis reply: HTTP {reply.status_code}")
            raise ZahnerAnalysisError(
                f"Zahner Analysis could not start the job: HTTP {reply.status_code}"
            )

        replyContent = json.loads(reply.content)
        if replyContent.get("status") in ["failed", "error"]:
            logging.error("Zahner Analysis reply: " + str(replyContent))
            raise ZahnerAnalysisError(
                "Zahner Analysis could not start the job: "
                + " ".join(replyContent.get("messages", []))
            )

        return replyContent["job-id"]

    def _waitForJob(self, jobId: str, timeout: float = None) -> dict:
        """
        Function which is waiting for the fit result.

        This function polls the status of the fit operation until the job is done.
        If the job fails, a ZahnerAnalysisError with the messages of the Zahner Analysis is raised.

        :param jobId: JobId.
        :param timeout: Time for which polling should be done in seconds, or None for infinite.
        :returns: The status of the job, with the fit result in the key "result".
        """
        startTime = time.time()

        while True:
            reply = self._analysisConnection.get(f"/job/{jobId}/status")

            if reply.status_code != 200:
                logging.error(f"Zahner Analysis reply: HTTP {reply.status_code}")
                raise ZahnerAnalysisError(
                    f"Operation in Zahner Analysis Server failed: HTTP {reply.status_code}"
                )

            status = json.loads(reply.content)
            jobStatus = status["status"]

            if jobStatus == "done":
                return status
            elif jobStatus == "failed":
                logging.error("Zahner Analysis fitting failed")
                messages = status.get("messages", [])
                raise ZahnerAnalysisError(
                    "Operation in Zahner Analysis Server failed: "
                    + (messages[-1] if messages else "no message")
                )

            if timeout is not None and time.time() - startTime > timeout:
                logging.error("Zahner Analysis fitting timeout")
                raise ZahnerAnalysisError("Operation in Zahner Analysis Server timeout")

            time.sleep(0.02)  # poll status every 20 ms

    def _readFittedModel(self, jobId) -> IsfxModelImport:
        """
        Reading the fitted model from the Zahner Analysis.

        Reading is done via http get request.

        :param jobId: JobId.
        :returns: Object from received data.
        """
        reply = self._analysisConnection.get(f"/job/{jobId}/model")
        return IsfxModelImport(xmlString=reply.content.decode("utf-8"))

    def _readFitInputData(self, jobId) -> ImpedanceSpectrum:
        """
        Reading the Samples used for fit from the Zahner Analysis.

        Reading is done via http get request.

        :param jobId: JobId.
        :returns: Object from received data.
        """
        return self._readSpectrum(f"/job/{jobId}/samples")

    def _readSimulatedData(self, jobId) -> ImpedanceSpectrum:
        """Reading the simulation data from the Zahner Analysis.

        Reading is done via http get request.

        :param jobId: JobId.
        :returns: Object from received data.
        """
        return self._readSpectrum(f"/job/{jobId}/simulation")

    def _readSpectrum(self, url: str) -> ImpedanceSpectrum:
        """Reading a spectrum from the Zahner Analysis.

        The format is taken from the filename which the Zahner Analysis sends in the
        Content-Disposition header. Without this header the format is .ism.

        :param url: Relative URL of the download.
        :returns: Object from received data.
        """
        reply = self._analysisConnection.get(url)
        if reply.status_code != 200:
            raise ZahnerAnalysisError(
                f"Zahner Analysis download {url} failed: HTTP {reply.status_code}"
            )

        match = re.search(
            r'filename="([^"]+)"', reply.headers.get("Content-Disposition", "")
        )
        extension = os.path.splitext(match.group(1))[1].lower() if match else ".ism"

        if extension == ".ism":
            return IsmImport(reply.content)
        elif extension == ".zmx":
            return ZmxImport(reply.content).getImpedance()
        else:
            raise ZahnerAnalysisError(
                f"Zahner Analysis returned {extension} data, which can not be read"
            )


def _checkOutputFormat(outputFormat: str) -> str:
    """Check the output format.

    :param outputFormat: The format.
    :returns: The format.
    """
    if outputFormat not in OUTPUT_FORMATS:
        raise ValueError(
            f'outputFormat "{outputFormat}" is not supported, use one of {OUTPUT_FORMATS}'
        )
    return outputFormat


def _fileExtension(data: ImpedanceSpectrum) -> str:
    """Get the file extension of the data.

    :param data: The data.
    :returns: ".ism" or ".zmx".
    """
    if isinstance(data, (ZmxImport, ZmxImpedance)):
        return ".zmx"
    return ".ism"


class EisFittingPlotter:
    """
    Class with utility Nyquist and Bode plotting methods.

    This class contains methods to display the fit results in the style of Zahner Analysis.
    """

    @staticmethod
    def plotBode(
        fittingResult: EisFittingResult,
        impedanceData: ImpedanceSpectrum = None,
        axes=None,
        zTogetherPhase=True,
        absPhase=True,
    ):
        """Plotting the data in the Bode plot.

        For plotting matplotlib is used with the function :meth:`zahner_analysis.plotting.impedance_plot.bodePlot`.
        With this function or also only with matplotlib the plot can be represented adapted.
        This method displays the plot in the standard Zahner Analysis design.

        Either axes can be passed on which will be plotted, or a new figure with axes will be created
        automatically. The figure and the axes are always returned.

        If the impedanceData is not passed, then the samples used for the fit are displayed.

        The Zahner Analysis default setting impedance and phase in a plot and phase in magnitude can be deactivated with two parameters.

        The following code block shows a few snippets as an example:

        .. code-block:: python

            fig, ax = plt.subplots(2,2)

            (fig, (impedanceAxis, phaseAxis)) = EisFittingPlotter.plotBode(fittingResult, axes=(ax[0,0],ax[1,0]))
            (fig, (impedanceAxis, phaseAxis)) = EisFittingPlotter.plotBode(fittingResult, axes=(ax[0,1],ax[1,1]))
            impedanceAxis.legend(["Measured Data", "Fitted Model"])
            plt.show()

            # or

            (fig2, (impedanceAxis2, phaseAxis2)) = EisFittingPlotter.plotBode(fittingResult)
            impedanceAxis2.legend(["Measured Data", "Fitted Model"])
            fig2.set_size_inches(18, 10)
            plt.show()


        :param fittingResult: Fitting result object.
        :param impedanceData: Optional impedance data for display.
        :param axes: Tuple (impedanceAxis, phaseAxis) with impedance and phase axes object, or None if a new figure should be created.
        :param zTogetherPhase: Default True to display phase and impedance in one plot.
        :param absPhase: Default True to plot the absolute value of the phase.
        :returns: Tuple fig, axes
        """
        fig = None

        if impedanceData is not None:
            fig, axes = bodePlotter(
                axes,
                impedanceObject=impedanceData,
                zTogetherPhase=zTogetherPhase,
                absPhase=absPhase,
            )
        else:
            fig, axes = bodePlotter(
                axes,
                impedanceObject=fittingResult.getFitInputData(),
                zTogetherPhase=zTogetherPhase,
                absPhase=absPhase,
            )

        fig, axes = bodePlotter(
            axes,
            impedanceObject=fittingResult.getFittedSimulatedData(),
            zTogetherPhase=zTogetherPhase,
            absPhase=absPhase,
            argsImpedanceAxis={"linestyle": "solid", "marker": None},
            argsPhaseAxis={"linestyle": "solid", "marker": None},
        )

        return fig, axes

    @staticmethod
    def plotNyquist(
        fittingResult: EisFittingResult,
        impedanceData: ImpedanceSpectrum = None,
        ax=None,
        minusNyquist=True,
        maximumAbsImpedance: float = None,
    ):
        """
        Plotting the data in the Nyquist plot.

        For plotting matplotlib is used with the function :meth:`zahner_analysis.plotting.impedance_plot.nyquistPlot`.
        With this function or also only with matplotlib the plot can be represented adapted.
        This method displays the plot in the standard Zahner Analysis design.

        Either axes can be passed on which will be plotted, or a new figure with axes will be created
        automatically. The figure and the axes are always returned.

        If the impedanceData is not passed, then the samples used for the fit are displayed.

        The following code block shows a snippet as an example:

        .. code-block:: python

            (fig, ax) = EisFittingPlotter.plotBode(fittingResult, maximumAbsImpedance=1)
            ax.legend(["Measured Data", "Fitted Model"])
            plt.show()

        :param fittingResult: Fitting result object.
        :param impedanceData: Optional impedance data for display.
        :param ax: The axis on which to plot, or None to create a new figure.
        :param minusNyquist: Default True to invert the imaginary part of the impedance.
        :param maximumAbsImpedance: If the value is not None, only impedances whose absolute value is smaller than this value are plotted.
        :returns: Tuple fig, ax
        """
        fig = None

        if impedanceData is not None:
            fig, ax = nyquistPlotter(
                ax,
                impedanceObject=impedanceData,
                minusNyquist=minusNyquist,
                maximumAbsImpedance=maximumAbsImpedance,
            )
        else:
            fig, ax = nyquistPlotter(
                ax,
                impedanceObject=fittingResult.getFitInputData(),
                minusNyquist=minusNyquist,
                maximumAbsImpedance=maximumAbsImpedance,
            )

        fig, ax = nyquistPlotter(
            ax,
            impedanceObject=fittingResult.getFittedSimulatedData(),
            minusNyquist=minusNyquist,
            argsNyquistAxis={"linestyle": "solid", "marker": None, "color": "#40e0d0"},
            maximumAbsImpedance=maximumAbsImpedance,
        )

        return fig, ax
