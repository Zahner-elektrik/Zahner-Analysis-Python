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
import numpy as np
import io
import struct
import datetime


def readF8FromFile(file):
    bytesRead = file.read(8)
    retval = struct.unpack(">d", bytesRead)
    return retval[0]


def readF8ArrayFromFile(file, length):
    return np.ndarray(shape=(length,), dtype=">f8", buffer=file.read(8 * length))


def readI2FromFile(file):
    return int.from_bytes(file.read(2), "big", signed=True)


def peekI2FromFile(file):
    return int.from_bytes(file.peek(2), "big", signed=True)


def readI2ArrayFromFile(file, length):
    return np.ndarray(shape=(length,), dtype=">i2", buffer=file.read(2 * length))


def readI6FromFile(file):
    return int.from_bytes(file.read(6), "big", signed=True)


def readTimeStampDateTimeArrayFromFile(file, length):
    timeArray = readF8ArrayFromFile(file, length)
    datetimeArray = []
    for time in timeArray:
        datetimeArray.append(thalesTimeStampToDateTime(time))
    return datetimeArray


def readZahnerStringFromFile(file):
    length = readI2FromFile(file)
    content = bytearray()

    for i in range(length):
        content.append(file.read(1)[0])

    return content.decode("ASCII").swapcase()


def readZahnerDate(file):
    dateString = readZahnerStringFromFile(file)
    date = dateString[0:6]

    day = int(date[0:2])
    month = int(date[2:4])
    year = int(date[4:6])

    """
    Only the last two digits of the date are saved.
    It is assumed that the measurement was carried out between 1970 and 2070.
    A software update is necessary in the year 2070 at the latest.
    """
    if year < 70:
        year += 2000
    else:
        year += 1900

    return datetime.datetime(year, month, day)


def thalesTimeStampToDateTime(timestamp):
    """Calculation of the time stamp.

    The time is in seconds related to 01.01.1980.

    :param timestamp: Seconds since 01.01.1980.
    :returns: Python datetime object.
    """
    timeZero = datetime.datetime(1980, 1, 1)
    timeDifference = datetime.timedelta(seconds=abs(timestamp))

    timestamp = timeZero + timeDifference
    return timestamp
