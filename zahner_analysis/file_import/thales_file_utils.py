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

import numpy as np
import io
import struct
import datetime
from io import BytesIO, BufferedReader
from typing import Union


def get_remaining_bytes(buffer: Union[BytesIO, BufferedReader]) -> int:
    current_pos = buffer.tell()

    if isinstance(buffer, BytesIO):
        total_size = buffer.getbuffer().nbytes
    else:  # BufferedReader
        # Save current position
        buffer.seek(0, 2)  # Seek to end
        total_size = buffer.tell()
        # Restore original position
        buffer.seek(current_pos)

    return total_size - current_pos


def readF8FromFile(file: io.BufferedReader) -> float:
    bytesRead = file.read(8)
    retval = struct.unpack(">d", bytesRead)
    return retval[0]


def readF8ArrayFromFile(file: io.BufferedReader, length: int) -> np.ndarray:
    return np.array(
        np.ndarray(shape=(length,), dtype=">f8", buffer=file.read(8 * length))
    )


def readI2FromFile(file: io.BufferedReader) -> int:
    return int.from_bytes(file.read(2), "big", signed=True)


def peekI2FromFile(file: io.BufferedReader) -> int:
    return int.from_bytes(file.peek(2), "big", signed=True)


def readI2ArrayFromFile(file: io.BufferedReader, length: int) -> np.ndarray:
    return np.array(
        np.ndarray(shape=(length,), dtype=">i2", buffer=file.read(2 * length))
    )


def readI6FromFile(file: io.BufferedReader) -> int:
    return int.from_bytes(file.read(6), "big", signed=True)


def readTimeStampDateTimeArrayFromFile(
    file: io.BufferedReader, length: int
) -> list[datetime.datetime]:
    timeArray = readF8ArrayFromFile(file, length)
    datetimeArray = []
    for time in timeArray:
        datetimeArray.append(thalesTimeStampToDateTime(time))
    return datetimeArray


def readZahnerStringFromFile(file: io.BufferedReader) -> str:
    length = readI2FromFile(file)
    content = bytearray()

    for i in range(length):
        content.append(file.read(1)[0])

    return content.decode("ASCII").swapcase()


def writeZahnerStringToBytes(input_string: str) -> bytes:
    # Convert the string to ASCII and swap case
    swapped_string = input_string.swapcase()
    ascii_bytes = swapped_string.encode("ASCII")

    # Get the length of the string and convert to 2 bytes
    length = len(ascii_bytes)
    length_bytes = length.to_bytes(2, byteorder="big", signed=True)

    # Combine the length bytes and the ASCII string bytes
    result_bytes = length_bytes + ascii_bytes
    return result_bytes


def readZahnerDate(file: io.BufferedReader) -> datetime.datetime:
    dateString = readZahnerStringFromFile(file)
    try:
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
    except:
        # fallback date
        day = 1
        month = 1
        year = 1970

    return datetime.datetime(year, month, day)


def thalesTimeStampToDateTime(timestamp: int) -> datetime.datetime:
    """Calculation of the time stamp.

    The time is in seconds related to 01.01.1980.

    :param timestamp: Seconds since 01.01.1980.
    :returns: Python datetime object.
    """
    timeZero = datetime.datetime(1980, 1, 1)
    timeDifference = datetime.timedelta(seconds=abs(timestamp))

    timestamp = timeZero + timeDifference
    return timestamp
