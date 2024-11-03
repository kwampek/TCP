"""
Defines constants used throughout the program.
"""
from enum import Enum

LONG_MAX = 0xffff

MAX_PACKAGE_SIZE = 65536
MAX_DATA_SIZE = 65516
HEADER_SIZE = 20
RESEND_LIMIT = 20

TIMEOUT = 2

CWR = 1
ECE = (1 << 1)
URG = (1 << 2)
ACK = (1 << 3)
PSH = (1 << 4)
RST = (1 << 5)
SYN = (1 << 6)
FIN = (1 << 7)


class Errors(Enum):
    CONNECTION_ERROR = 1
    CONNECTION_TIMEOUT = 2

    INVALID_PACKET_SIZE = 3
    INVALID_PACKET = 4
