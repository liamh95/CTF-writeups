from Crypto.Util.number import long_to_bytes, bytes_to_long
import random
from secret import flag

mod = 0x225fd
flag = bytes_to_long(flag)
e_values = [97491, 14061, 55776]
S = (lambda f=[flag], sk=[]: ([sk.append(f[0] % mod) or f.__setitem__(0, f[0] // mod) for _ in iter(lambda: f[0], 0)],sk)[1])()
S = vector(GF(mod), S)

A_save = []
b_save = []

for i in range(52):
    A = VectorSpace(GF(mod), 44).random_element()
    e = random.choice(e_values)
    b = A * S + e
    #print(b)

    A_save.append(A)
    b_save.append(b)

open('out.txt', 'w').write('A_values = ' + str(A_save) + ' ; b_values = ' + str(b_save))