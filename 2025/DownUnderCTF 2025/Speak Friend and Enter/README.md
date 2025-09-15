# Speak Friend, and Enter (Crypto - 195)

> I made a new cipher, can you help me test it? I'll give you the key, please use it to decrypt my ciphertext.Dear player,

> I will happily give you the flag... if you can sign my challenge!

> Regards,

> cybears:cipher

---
## What we're given
We're given a single file, `server.py` that does the following.

1. Sets up a 2048-bit RSA modulus.
2. Sets up a [CMAC](https://en.wikipedia.org/wiki/One-key_MAC) object using a key that can be found in a NIST [reference document](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-38B.pdf).
3. Computes the MAC of the RSA modulus. In order for everyone to have the same value for this, steps 1 and 2 are omitted and the value of this MAC is hard-coded in the challenge file.
4. Randomly generates a 48 ASCII character challenge string and sends it to us.
5. Prompts us to enter a public key (an RSA modulus) and corresponding signature for the challenge string.
6. Checks that MAC of our public key matches the MAC of their RSA modulus, that our public key is 2048 bits long, and that we produced a valid signature on the challenge string.
7. Output the flag if we pass all of those checks.


Rather than checking if the RSA modulus we provide matches theirs by directly comparing them, they compare the CMACs of the two moduli.
Basically, the CMAC check asks us "hey, are you signing with the secret RSA modulus we made?"
If we convince them that we have their modulus, they check the validity of the signature we provide.

We have pretty much no chance of guessing the secret RSA modulus, so it seems like we need to come up with our own modulus that passes the CMAC check.
```
CMAC(known_key, their_modulus) == CMAC(known_key, our_modulus)
```
If we can do this, we need to create a valid signature with it, which requires some number-theoretic knowledge of our modulus.
```
(our_signature)^(65537) == challenge_string (mod our_modulus)
```
We know the CMAC that we're aiming for and we need to cook up a preimage for it.
Inverting hashes is usually hard, but we know the key and the hashing algorithm isn't terribly complicated.
Maybe we can exploit this to beat the CMAC check.

Even if we figure that out, we still have to solve a number theory problem, namely inverting `65537 ( mod phi(our_modulus) )`, in order to create a signing key.
Knowing `phi(our_modulus)` is (sort of, but not really) equivalent to knowing the factorization of `our_modulus`.
If we can cook up a modulus that happens to be a prime (which is easy to check with great certainty), then this easy.

---
## Background - CMAC
![CMAC schematic](cmac.jpg "From Wikipedia")
CMAC works by performing a modified CBC encryption of the plaintext.
If our plaintext has 16 blocks `m_1, ..., m_16`, then we do the following.
1. Derive subkeys `k_1` and `k_2` from the key`k`.
2. For `i = 1, ..., 15`, set `c_i = ENC_k(c_(i-1) ^ m_i)` (where `c_0` is the all zero block)
3. Output `ENC_k(c_15 ^ m_16 ^ k_i)`, where `i` is 1 or 2 dependign on whether `m_16` is a full block.




---
## Vulnerability - default key used in hash

CMAC consists (more or less) of chaining together the outputs of a block cipher applied to the blocks of the input.
Since we know the key, for any given input, we can step through the entire chaining process that produces the MAC for that input.
The key insight is that if we have a target MAC, we can randomly generate the first 15 blocks of input and then choose the 16th block.
If we insist that `m_16` is a full block, then
```
target_cmac = ENC_k(c_15 ^ m_16 ^ k_1).
```
So solving for `m_16`, we obtain
```
m_16 = DEC_k(target_mac) ^ k_1 ^ c_15.
```
We simply keep repeating this process until the concatenation `m_1 ||...||m_16` is a 2048-bit prime.


---

## Conclusion
Even when a secure hashing algorithm is used, if it's used with a default key, we can solve usually-hard problems like producing preimages.