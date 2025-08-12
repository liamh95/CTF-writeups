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


I spent way too much time on this challenge because I didn't know that the compiled python file could be decompiled.
It  wasn't until after the competition that I found [PyLingual](https://pylingual.io/).
Still, even without the source code, it was evident that we're trying find the nonce and/or counter that were used to encrypt the flag (using some block cipher in [counter mode](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#Counter_(CTR))) since we can still encrypt messages by running the compiled python file.

Looking at the output in `ctf_challenge_package.json`, one thing that jumps out is that all of the ciphertexts look pretty similar even though they all have different nonce-counter pairs -- something that shouldn't happen when using a secure cipher.
Even more, it looks like some of the flag plaintext leaks through the ciphertext.
```python
    >>> flag_ct = bytes.fromhex('692f09e677335f6152655f67304e6e40141fa702e7e5b95b46756e63298d80a9bcbbd95465795f21ef0a')
    >>> flag_ct
    b'i/\t\xe6w3_aRe_g0Nn@\x14\x1f\xa7\x02\xe7\xe5\xb9[Func)\x8d\x80\xa9\xbc\xbb\xd9Tey_!\xef\n'
```

---
## Background - CMAC
Looking over the (decompiled) source file, we see something that closely resembles the [ChaCha cipher](https://en.wikipedia.org/wiki/Salsa20#ChaCha_variant).
Briefly, ChaCha is a stream cipher that generates 64-byte blocks of keystream and XORs them with blocks of the plaintext.
Each keystream block in this variant starts as a 4 by 4 matrix of 4-byte words like this.
```
[00000000] [00000000] [00000000] [00000000]
[   K0   ] [   K1   ] [   K2   ] [   K3   ]
[   K4   ] [   K5   ] [   K6   ] [   K7   ]
[  CTR   ] [   N1   ] [   N2   ] [   N3   ]
```
Here, the `K_i` words are derived from an expanded version of the key using `construct_structured_key()`, `CTR` is a 32-bit integer that gets incremented with each new block and the `N_i` words come from the 96-bit nonce (the key and nonce words are actually little-endian via the `bytes_to_words()` function -- missing this was a time sink).

This block gets jumbled up by performing a sequence of mixing operations called quarter-rounds that act alternately on the columns and rows of the block.
Finally, each word in the resulting block is added (mod 2^(32)) to the corresponding word in the block's intial state.


---
## Vulnerability - only one quarter-round of mixing

When we look at the `init.sh` file, we see that the flag is encrypted using just one round of this cipher.
When we check out the `make_block()` function, we see that this one round corresponds to calling `mix_bits()` on the first column of the above figure -- no other parts of the block are touched (except when the individual words are added to themselves, mod 2^32).
We make the following observations.

1. Since the flag ciphertext (and therefore, the flag itself) is only 42 bytes long, only the first 11 chunks of the keystream block are used.
Since the bits in only the first column are mixed, we conclude that the secret nonce is never used in encrypting the flag.

From this, we can conclude that all we need is the 32-bit counter.
This can be brute-forced in a non-stupid amount of time, but we can do better because of the following observation.

2. The operations performed in `mix_bits()` are reverisible and we know all of the 32-bit words in the first column except for the counter.
Since we know that the flag begins with `CTF{`, we can XOR this with the ciphertext to get the first 4 bytes of the keystream.
We can then reverse the action of the quarter round to recover the value of the counter.

Once we have the counter, we can recreate the keystream and then XOR with the ciphertext to get the flag.

---
## Reversing the quarter-round
After calling `mix_bits(state, 0, 4, 8, 12)`, the value of the first 32-bit word in the keystream is `rotl32(add32(K4, rotl32(CTR, 16)), 12)`.
Then we add this to 0 mod 2^32 to get the first 32 bits of keystream, so we can just work with this.
Since `rotl123(rotl(a, k), 32-k) = a`, we can easily undo the quarter round to recover `CTR`.
The `solve.py` script does this, and then recreates the keystream block using the given key and an arbitrary nonce.
Then just XOR with the ciphertext to get the flag.
This is all done with the provied `get_bytes()` function.

## Conclusion
When few rounds are used in a cipher that uses reversible operations on its internal state, with a bit of extra information, we might be able to recover the keystream.