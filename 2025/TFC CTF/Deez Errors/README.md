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
Recovering the flag amounts to solving an instance of the [learning with errors](https://en.wikipedia.org/wiki/Learning_with_errors) problem: find $\mathbf s \in \mathbb F_p^n$ such that $A\mathbf s + \mathbf e = \mathbf b$ for a given matrix $A\in \mathbb{F}_p^{m\times n}$ and given vector $\mathbf b \in \mathbb F_p^m$, where $\mathbf e\in \mathbb F_p^m$ is some random noise.
For certain distributions of the noise $\mathbf e$, this problem is believed to be hard -- as hard as some other lattice problems (even for quantum computers!).


If the vector $\mathbf e$ is in some sense "small", then it seems reasonable to hope that $\mathbf b$ is the closest vector to a vector in the lattice spanned by the columns of $A$.
Put differently, we hope that $\mathbf e$ is the smallest vector in the lattice spanned by the columns of $A$ and the vector $\mathbf b$.

One complication is that this problem is formulated in $\mathbb F_p^n$, where we don't have a notion of distance.
Our way out is to map elements of $\mathbb F_p$ to the integers $0, ..., p-1$ and then add on multiples of $p$.
That is, we seek a small nonzero vector $\mathbf e$ in the lattice spanned by the colums of the block matrix $[A\ \mathbf b\ pI_m]$, where we take the entries of $A$ and $\mathbf b$ to live in $\mathbb Z$.

Now the [BKZ algorithm](https://en.wikipedia.org/wiki/Korkine%E2%80%93Zolotarev_lattice_basis_reduction_algorithm) takes a spanning set for a lattice and outputs a basis whose vectors are short and mutually nearly-orthogonal.
Our hope is that if the error vector $\mathbf e$ is short and "sticks out", then the BKZ algorithm, when handed the columns of $[A\ \mathbf b\ p\mathbf I_m]$ as a spanning set, will output $\pm \mathbf e$ as one of its basis vectors.


## Applying it here

Things seem grim for us because the error vector is not short: the entries of `e` all live in `[97491, 14061, 55776]`, each of which is pretty comparable to `mod`, so it seems unlikely that a short vector in our lattice has the form of such an error vector. The trick here is that we can _make_ the error vector short by applying the right affine transformation.
Our errors happen to form an arithmetic progression modulo `mod`: `[97491, 14061, 55776] = [55776 - 41715, 55776, 55776 + 41715]`.
This lets us transform our learning with errors equation: if we let $\mathbf 1$ be the vector of all 1's in $\mathbb Z^{52}$, then

$A\mathbf s + \mathbf e = \mathbf b \implies (41715)^{-1}(A\mathbf s + \mathbf e- 55776\cdot \mathbf 1) = (41715)^{-1}(\mathbf b - 55776\cdot \mathbf 1) \implies \tilde A\mathbf s + \tilde{\mathbf e} = \tilde{\mathbf b}$,

where $\tilde A = (41715)^{-1}A$, $\tilde{\mathbf e} = (41715)^{-1}(\mathbf e - 55776\cdot \mathbf 1)$ and $\tilde{\mathbf b} = (41715)^{-1}(\mathbf b - 55776\cdot \mathbf 1)$ and all arithmetic is modulo `mod`.
Things look a lot better for us here because now each entry in the error vector $\tilde{\mathbf e}$ lives in `[-1, 0, 1]`, so now $\tilde{\mathbf e}$ is much more likely to be a short vector in our lattice.

We simply feed $[\tilde A\ \tilde{\mathbf b}\ pI_{52}]$ to the BKZ algorithm and read off the first nonzero vector all of whose entries are in `[-1, 0, 1]`.

```Python
from sage.all import *
from Crypto.Util.number import long_to_bytes, bytes_to_long

p = 0x225fd

# arithmetic progression
e_values = [97491, 14061, 55776]
# = [55776 − 41715, 55776, 55776 + 41715]
inv = pow(41715, -1, p)


# b = A * S + e
print('Loading matrices...')
A_values = ...
b_values = ...


print('Shifting matrices...')
A_tilde_values = [tuple((i * inv) % p for i in row) for row in A_values]
b_tilde_values = [(i - 55776) * inv % p for i in b_values]


A_tilde= matrix(ZZ, A_tilde_values)
b_tilde = vector(ZZ, b_tilde_values)

M_aug = A_tilde.augment(matrix(ZZ, b_tilde).T).augment(p * identity_matrix(ZZ, 52))

print('Running BKZ...')
M = M_aug.T.BKZ(block_size=15)

# hopefully, e_tilde is the shortest vector in the rows of M
# find it by looking for a row whose only entries are in {-1, 0, 1}

print('Looking for e_tilde...')
for row in M:
    if all(x == 0 for x in row):
         continue
    if all(x in [-1, 0, 1] for x in row):
        plus_minus_e_tilde =  vector(ZZ, row)
        break


print('Solving for s...')
F = GF(p)
diff = vector(F, b_tilde) - vector(F, plus_minus_e_tilde)
s = A_tilde.change_ring(F).solve_right(diff)

# reconstruct flag from s
print('Reconstructing flag from s...')
flag_long = 0
for i in range(len(s)):
	flag_long += int(s[i]) * (p**i)

print(long_to_bytes(flag_long))
```
