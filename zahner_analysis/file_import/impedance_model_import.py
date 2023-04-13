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
import xml.etree.ElementTree as et
import re
import os


class IsfxModelImport:
    """Class to import model/circuits.

    The models must be in zahner isfx xml format.
    Either you pass the filename of the model you want to open or you pass the content of the file as a string.

    :param xmlFilePath: The file path of the isfx model file.
    :param xmlString: The model as a string or the content of an isfx file.
    """

    def __init__(self, xmlFilePath=None, xmlString=None):
        self._filename = "FromString.isfx"
        if xmlString is not None:
            self._xmlString = xmlString
            self._completeXmlTree = et.fromstring(xmlString)
        elif xmlFilePath is not None:
            (_, self._filename) = os.path.split(xmlFilePath)
            with open(xmlFilePath, "r", encoding="utf-8") as filename:
                self._xmlString = filename.read()
            with open(xmlFilePath, "r", encoding="utf-8") as filename:
                self._completeXmlTree = et.parse(filename).getroot()

        self.parsed_tree_elements = self._completeXmlTree.find("parsed-tree")

        pattern = r"<([\S]+)\s*name=\"[\S ]+?\"\s*>"
        matched = re.findall(
            pattern, str(et.tostring(self.parsed_tree_elements, encoding="utf-8"))
        )
        self.existingElementTypesInModel = list(set(matched))

        self._elements = []
        for element in self.existingElementTypesInModel:
            foundElements = self._completeXmlTree.findall(".//" + element)
            self._elements.extend(
                [IsfxModelElement(element) for element in foundElements]
            )
        return

    def __str__(self):
        """Create string with all circuit elements of the model.

        :return: String with all circuit elements.
        """
        retval = ""
        for element in self._elements:
            retval += str(element)
        return retval

    def toString(self):
        """Create string with all circuit elements of the model.

        print(IsfxModelImport(...)) generates for example the following string:

        .. code-block::

            Model: li-ion-model - fitted:
            inductor : L0
                  L:  7.940e-07 H        fixed: False
            finite-diffusion : FI0
                  W:  4.073e-02 Ωs^(-½)  fixed: False
                  k:  1.385e-03 1/s      fixed: False
            constant-phase-element : CPE0
               C_eq:  6.733e-02 F        fixed: False
                  α:  7.361e-01          fixed: False
             f_norm:  1.000e+03 Hz       fixed: True
            capacitor : C0
                  C:  5.025e-02 F        fixed: False
            resistor : R0
                  R:  3.603e-03 Ω        fixed: False
            resistor : R1
                  R:  2.683e-02 Ω        fixed: False
            resistor : R2
                  R:  3.597e-02 Ω        fixed: False

        :return: String with all circuit elements.
        """
        return self.__str__()

    def __getitem__(self, key):
        """Access to elements of the model.

        This function is used to access circuit elements via the [] operator.

        Then the elements can be accessed as in the following example.

        .. code-block:: python

            impedanceCircuitModel = IsfxModelImport(r"diode-ac-model.isfx")
            print(impedanceCircuitModel["R0"]["R"].getValue())

        :returns: The circuit element.
        :rtype: IsfxModelElement
        """
        return self.getCircuitElementByName(key)

    def getCircuitElementByName(self, name):
        """Returns an element of the circuit.

        This function is used by the [] operator. Instead of this getter you can also use the []
        operator wi in the following example.

        .. code-block:: python

            impedanceCircuitModel = IsfxModelImport(r"diode-ac-model.isfx")
            print(impedanceCircuitModel["R0"]["R"].getValue())

        :returns: The circuit element.
        :rtype: IsfxModelElement
        """
        retval = None
        for element in self._elements:
            if element.getName() == name:
                retval = element
                break
        return retval

    def getCircuitElements(self):
        """Returns all circuit elements as an array.

        :returns: The circuit elements.
        """
        return self._elements

    def save(self, filename):
        """Save the model.

        The model is saved with this function. The isfx file format contains xml.

        :param filename: Path and filename of the file to be saved with the extension .isfx.
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self._xmlString)
        return

    def getFileName(self):
        """Returns the filename.

        If the model was created from the disk, then the filename is returned,
        otherwise the name attribute from the xml is returned.
        If the xml name attribute is an empty string "FromString.isfx" is returned.

        :returns: The name.
        """
        return self._filename

    def getBinaryFileContent(self):
        """Get the content of the file binary.

        Returns the file contents as a binary byte array.

        :returns: bytearray with the file content.
        """
        return self._xmlString.encode(encoding="utf-8")


class IsfxModelElement:
    """Classe which represents the circuit elements.

    This constructor is only used by the class IsfxModelImport.

    :param xmlElement: The circuit element.
    """

    def __init__(self, xmlElement):
        self.xml = xmlElement

        xmlParameters = self.xml.findall(".//parameter")
        if len(xmlParameters) == 0:
            # for the user element it is called user-parameter
            xmlParameters = self.xml.findall(".//user-parameter")
        self.parameters = [
            IsfxModelElementParameter(param, self.xml.tag) for param in xmlParameters
        ]
        return

    def __str__(self):
        """Creates a string with the circuit element and its parameters.

        :return: String with the element and its parameters.
        """
        retval = f"{self.getType()} : {self.getName()}\n"
        for param in self.getParameters():
            retval += str(param) + "\n"
        return retval

    def __getitem__(self, key):
        """Returns an parameter of an circuit element.

        This function is used to access circuit elements and its parameters via the [] operator.

        Then the elements can be accessed as in the following example.

        .. code-block:: python

            impedanceCircuitModel = IsfxModelImport(r"diode-ac-model.isfx")
            print(impedanceCircuitModel["R0"]["R"].getValue())

        Each resistor has a parameter R. Young Goehr impedances, for example, have the parameters C, p and T.

        :returns: The circuit element parameter.
        :rtype: IsfxModelElementParameter
        """
        return self.getParameterByName(key)

    def getParameterByName(self, name):
        """Returns an parameter of an circuit element.

        This function is used by the [] operator. Instead of this getter you can also use the []
        operator with in the following example.

        .. code-block:: python

            impedanceCircuitModel = IsfxModelImport(r"diode-ac-model.isfx")
            print(impedanceCircuitModel["R0"]["R"].getValue())

        Each resistor has a parameter "R". Young Goehr impedances, for example, have the parameters C, p and T.

        :returns: The circuit element parameter.
        :rtype: IsfxModelElementParameter
        """
        retval = None
        parameters = self.getParameters()
        for parameter in parameters:
            if parameter.getName() == name:
                retval = parameter
                break
        return retval

    def getParameters(self):
        """Returns all parameters of the circuit element as an array.

        :returns: The parameters.
        """
        return self.parameters

    def getName(self):
        """Returns the name of the circuit element.

        The name is the one assigned in the GUI, for example R0 or CPE7.

        :returns: Name of the circuit element.
        """
        return self.xml.attrib["name"]

    def getType(self):
        """Returns the type of the circuit element.

        :returns: Type of the circuit element.
        """
        return self.xml.tag


class IsfxModelElementParameter:
    """Class which represents a parameter of a circuit element.

    This constructor is only used by the class IsfxModelElement.

    :param xmlElement: The parameter.
    :param xmlParentTag: The parent circuit element tag.
    """

    elementParameterIndex = {
        "resistor": {
            "0": {"name": "R", "unit": "Ω"},
        },
        "inductor": {
            "0": {"name": "L", "unit": "H"},
        },
        "capacitor": {
            "0": {"name": "C", "unit": "F"},
        },
        "spherical-diffusion": {
            "0": {"name": "W", "unit": "Ωs^(-½)"},
            "1": {"name": "k", "unit": "1/s"},
        },
        "young-goehr-impedance": {
            "0": {"name": "C", "unit": "F"},
            "1": {"name": "p", "unit": ""},
            "2": {"name": "T", "unit": "s"},
        },
        "warburg-impedance": {
            "0": {"name": "W", "unit": "Ωs^(-½)"},
        },
        "nernst-diffusion": {
            "0": {"name": "W", "unit": "Ωs^(-½)"},
            "1": {"name": "k", "unit": "1/s"},
        },
        "finite-diffusion": {
            "0": {"name": "W", "unit": "Ωs^(-½)"},
            "1": {"name": "k", "unit": "1/s"},
        },
        "homogenous-reaction-impedance": {
            "0": {"name": "W", "unit": "Ωs^(-½)"},
            "1": {"name": "k", "unit": "1/s"},
        },
        "constant-phase-element": {
            "0": {"name": "C_eq", "unit": "F"},
            "1": {"name": "α", "unit": ""},
            "2": {"name": "f_norm", "unit": "Hz"},
        },
    }

    def __init__(self, elementXML, xmlParentTag=None):
        self.xml = elementXML
        self.xmlParentTag = xmlParentTag
        return

    def getName(self):
        """Returns the name of the parameter.

        :returns: The name.
        """
        if self.xml.find("name"):
            return self.xml.attrib["name"]
        else:
            return IsfxModelElementParameter.elementParameterIndex[self.xmlParentTag][
                self.xml.attrib["index"]
            ]["name"]

    def getUnit(self):
        """Returns the unit of the parameter.

        :returns: The unit.
        """
        if self.xml.find("unit"):
            return self.xml.attrib["unit"]
        else:
            return IsfxModelElementParameter.elementParameterIndex[self.xmlParentTag][
                self.xml.attrib["index"]
            ]["unit"]

    def getValue(self):
        """Returns the value of the parameter.

        :returns: The value.
        """
        return float(self.xml.attrib["value"])

    def isFixed(self):
        """Returns the fixed state of the parameter.

        If the parameter is fixed, then it is no longer changed by the fitter.

        :returns: True when the value is fixed, else False.
        """
        retval = False
        fixedState = self.xml.attrib["fitterFixed"]
        if fixedState == "0":
            retval = True
        return retval

    def __str__(self):
        """Returns informations about the parameter as string.

        :returns: A string with informations.
        """
        return self._parameterToString()

    def _parameterToString(self):
        """Returns informations about the parameter as string.

        :returns: A string with informations.
        """
        paramDict = self.xml.attrib
        try:
            reply = f" {self.getName():>6}: {self.getValue():>10.3e} {self.getUnit():<8} fixed: {self.isFixed()}"
        except:
            reply = " "
            for key in paramDict.keys():
                reply += f"{key}: {paramDict[key]} "
        return reply
