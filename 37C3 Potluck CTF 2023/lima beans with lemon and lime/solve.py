#!/usr/bin/env python3

from Crypto.Util.number import getPrime, bytes_to_long
from pwnlib.tubes.remote import *
from sage.all import *
# from secrets import randbelow, randbits
# from FLAG import flag

beanCount = 8
beanSize = 2048
lemonSize = beanSize // 2 * beanCount
queries = 17

# decodes a message given by eight integers modulo killerBean
def un_pkcs16(filledLimaBeans, killerBean):
	num = 0
	for i in range(beanCount):
		num += filledLimaBeans[i] * (killerBean**i)
	return num.to_bytes(beanSize, byteorder='big')


coeffs = []
ivs = []
cts = []

conn = remote('challenge18.play.potluckctf.com', 31337)

# get killerBean
p = int(conn.recvuntil('> ').decode().split('\n')[1][3:])

# get equations
for turn in range(queries-1):
	conn.send('2\n')
	response_lines = conn.recvuntil('> ').decode().split('\n')

	cts.append( int(response_lines[0][4:]) )
	ivs.append( int(response_lines[1][4:]) )
	coeffs.append([int(num) for num in response_lines[2][5:].split(',')])

conn.close()

c = matrix(GF(p), cts).transpose()
A = []
for i in range(16):
	row = [0 for _ in range(16)]
	# if the j-th bit of the IV (or "lime" in their terminology) is 0, the equation uses the j-th coefficient as a variable. If it's a 1, we use the square of the j-th coefficient
	for j in range(beanCount):
		row[ 8 * ((ivs[i] >> j) & 1) + j ] = coeffs[i][j]
	A.append(row)
A = matrix(GF(p), A)

# solve the linear system, obtaining the coefficients of the encoded flag and their squares
x = A.solve_right(c)

# we only care about the coefficients, not their squares
filled = [int(j[0]) for j in x[:8]]

plz = un_pkcs16(filled, p)

print(plz)