#!/usr/bin/env python3

from Crypto.Util.number import getPrime, bytes_to_long, long_to_bytes
from hashlib import sha256
from secrets import randbits
import os


# hash length extension since we know length of secret