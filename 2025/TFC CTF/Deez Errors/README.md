# Deez Errorz (Crypto)

---
## What we're given
We're given two files: a `source.sage` file and its resulting output in `out.txt`.
The source file is pretty short, so here it is.
```Python
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
```
It does the following.
1. Sets `S` to a vector whose entries are the base-`mod` coefficients of `bytes_to_long(flag)` (that's what the impenetrable-looking lambda function is doing). The least-significant coefficient is the first entry and there are 44 entries in total.
2. Generates a random `44 x 42` matrix `A` over the field `GF(mod)`.
3. Computes the vector `b = A*S + e`, where each entry of `e` is chosen at random from `e_values = [97491, 14061, 55776]`.
4. Writes `A` and `b` to `out.txt`.




---
## Background - Learning with Errors and Short Vectors in Lattices
Recovering the flag amounts to solving an instance of the [learning with errors](https://en.wikipedia.org/wiki/Learning_with_errors) problem: find $\mathbf x \in \mathbb F^n$ such that $A\mathbf x + \mathbf e = \mathbf b$ for a given matrix $A\in \mathbb{F}^{m\times n}$ and given vector $\mathbf b \in \mathbb F^m$, where $\mathbf e\in \mathbb F^m$ is some random noise.
For certain distributions of the noise $\mathbf e$, this problem is believed to be hard -- as hard as some other lattice problems (even for quantum computers!).

