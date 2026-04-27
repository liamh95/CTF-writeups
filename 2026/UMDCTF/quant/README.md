# quant? (misc. 72 pts)
> it's all math anyways. I heard predicting the future has been in vogue recently, so I hid the flag in a black-box oracle.
> Connect to the service and submit one OpenQASM-like circuit ending with END.
> `nc challs.umdctf.io 30309`
> The circuit has 16 input qubits q[0] through q[15], one ancilla qubit q[16], and a 16-bit classical register c[0] through c[15].
> Supported instructions:

    h q[i];
    x q[i];
    z q[i];
    mcx q[i],...,q[j];
    oracle q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15],q[16];
    diffuse q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15];
    measure q[i] -> c[i];
> You may include the usual OPENQASM 2.0;, include "qelib1.inc";, qreg q[17];, and creg c[16]; lines. Measure every input qubit as q[i] -> c[i].
> Limits: at most 250 oracle calls, 200000 bytes of input, and 512 shots. If your circuit places enough probability mass on the hidden marked state, the service prints the flag.
---

## What we're given
Connecting to the challenge server prints basically the same instructions given in the challenge description.
In short, we need to find a marked state given oracle access to some quantum circuit, 16 quantum registers, one ancilla register, 16 classical registers and some standard quantum gates.
We're allowed to submit an OpenQASM program (basically, write a program that applies gates to the registers and then measure) with the restriction that we can only call the oracle 250 times and our program can't be insanely long.
The challenge server runs our program 512 shots and we find the marked state "enough" times.



---
## Background - qubits and quantum computation
While a classical bit can only take the value 0 or 1, a quantum bit, or _qubit_, is a _superposition_ (linear combination) of the orthogonal basis states $|0\rangle$ and $|1\rangle$, with unit length.
That is, the qubit $|\psi\rangle$ can be written $|\psi\rangle = \alpha |0\rangle + \beta |1\rangle$ where the complex numbers $\alpha, \beta$ satisfy $|\alpha|^2 + |\beta|^2 = 1$.

We can do two things with qubits: apply unitary linear transformations to them and measure them.

- **Unitary time evolution**: If $|\psi_1\rangle$ is the state of our qubit at time $t = t_1$ and $|\psi_2\rangle$ is the state at time $t=t_2$, then there is some unitary transformation such that $|\psi_2\rangle = U|\psi_1\rangle$.
It's not tremendously important for us to define unitarity right now, but you can think of them as linear transformations that preserve length, like rotations and reflections.

    One example of a unitary transformation that will be helpful to us here is the _Hadamard gate_, $H$, defined by $H|0\rangle = \frac{1}{\sqrt 2}|0\rangle + \frac{1}{\sqrt 2}|1\rangle$ and $H|1\rangle = \frac{1}{\sqrt 2}|0\rangle - \frac{1}{\sqrt 2}|1\rangle$. 

- **Measurement**: There's a pretty general way to formulate measurement of a quantum state, but in the context of this problem, measuring the state $|\psi\rangle = \alpha |0\rangle + \beta |1\rangle$ yields the state $|0\rangle$ with probability $|\alpha|^2$ and the state $|1\rangle$ with probability $|\beta|^2$.
This is an instance of what people sometimes call "collapsing the wave function".

    Measuring 0 or 1 is obvious. Then Hadamard. It's uniform wow.

Okay, that's one qubit, but what if we have a bunch of them?
The pithy answer is "just [tensor](https://en.wikipedia.org/wiki/Tensor_product) them together", but if you aren't familiar with tensor products, then you can think about the $n$-qubit system as a unit vector in the space spanned by by _all_ $n$-bit strings.
So a two-quibit state looks like $\alpha_{00}|00\rangle + \alpha_{01}|01\rangle + \alpha_{10}|10\rangle + \alpha_{11}|11\rangle$, where these basis vectors are orthogonal and $|\alpha_{00}|^2 + |\alpha_{01}|^2 + |\alpha_{10}|^2 + |\alpha_{11}|^2 = 1$.
Our other two axioms still apply here: you can hit a multi-qubit state with unitary transformations or measure them by collapsing them to a basis state with the corresponding probability (this is still a simplified view of measurement - it doesn't have answers for questions like "what if I only measure _one_ qubit in a multi-quibit system?", but it's good enough for this problem).


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
