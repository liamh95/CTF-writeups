#!/usr/bin/env python3

from Crypto.Hash import CMAC, SHA512
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Util.strxor import *
from Crypto.Util.number import long_to_bytes, bytes_to_long, isPrime
from binascii import unhexlify
import random, json, string



challenge_string = bytes(input("challenge string: ").strip(), 'ascii')
s = bytes_to_long(SHA512.new(challenge_string).digest())


server_cmac_publickey = unhexlify('9d4dfd27cb483aa0cf623e43ff3d3432')

#NIST test key
NIST_SP_800_38B_Appendix_D1_K = unhexlify('2B7E151628AED2A6ABF7158809CF4F3C') 

# CMAC uses CBC, but we're manually stepping through the MAC process, so we use ECB and do the chaining manually
cipher = AES.new(NIST_SP_800_38B_Appendix_D1_K, AES.MODE_ECB) 

# first derive the two subkeys used in CMAC from the NIST key (see wiki page for One-key MAC)
k0 = bytes_to_long(cipher.encrypt(b'\x00' * 16))
k1 = (k0 << 1) & (2**128 - 1) if k0 < 2**127 else ((k0 << 1) & (2**128 - 1)) ^ 0x87
k2 = long_to_bytes((k1 << 1) & (2**128 - 1)) if k1 < 2**127 else long_to_bytes(((k1 << 1) & (2**128 - 1)) ^ 0x87)
k1 = long_to_bytes(k1)

# brute force a modulus of the right length that MAC's to the target MAC
p = 2
while True:
	# need bit length of modulus = 2048 bits = 16 16-byte blocks
	# start with 15 random blocks, then manip the last block to get the right MAC
	blocks = [bytearray(random.randbytes(16)) for _ in range(15)]

	c = b'\x00' * 16
	for i in range(15):
		c = cipher.encrypt(strxor(c, blocks[i]))

	# need to manip the last block so that resulting MAC is what we need
	# need ENC(c ^ k1 ^ block) = t
	# so need block = DEC(t) ^ k1 ^ c

	b16 = strxor(cipher.decrypt(server_cmac_publickey), strxor(k1, c))
	blocks.append(b16)

	# pray that we got a 2048-bit prime out of it
	p = bytes_to_long(b''.join(blocks))

	if p.bit_length() == 2048 and isPrime(p):
		break

# now just sign hash(challenge string)
e = 65537
d = pow(e, -1, p-1)
sig = pow(s, d, p)
print(f"{{\"public_key\": {p}, \"signature\" : {sig}}}")

