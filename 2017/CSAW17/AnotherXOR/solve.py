##### Taken from challenge cipher.py #####
def xor(s1,s2):
        return ''.join(chr(ord(a) ^ ord(b)) for a,b in zip(s1,s2))

def repeat(s, l):
        return (s*(int(l/len(s))+1))[:l]
##########################################


key_prefix = 'A qua'
with  open('encrypted', 'r') as cipher_file:
    cipher = cipher_file.read().decode('hex')

def guess_key_length():
    for i in range(94):
        k = key_prefix + ('A'*i)
        decryption = xor(cipher, repeat(k, len(cipher)))
        hopefully_hex = ''
        for j in range(105, len(decryption)):
            if j%len(k) < 5:
                hopefully_hex += decryption[j]
        try:
            num = int(hopefully_hex, 16)
            print(str(len(k)))
        except:
            pass

def decrypt():
    key = key_prefix + ('~' * 62) #key probably doesn't contain ~
    while '~' in key:
        plaintext = ''
        for i in range(len(cipher)):
            if key[i%67] == '~':
                plaintext += '~'
            else:
                plaintext += chr(ord(cipher[i]) ^ ord(key[i%67]))
        key = key_prefix + plaintext[43:105]
        

    print key
    message = xor(cipher, repeat(key, len(cipher)))[:38]
    print message