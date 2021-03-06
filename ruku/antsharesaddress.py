#! /usr/bin/env python
# -*- coding:utf-8 -*-
"""
Description:
    Cryptography Helper
Usage:
    from AntShares.Cryptography.Helper import *
"""


import os
import time
import random
import hashlib
import binascii


class ECCurveNotFound(Exception):
    """docstring for ECCurveNotFound"""
    def __init__(self, curve):
        super(ECCurveNotFound, self).__init__()
        self.curve = curve
    def __str__(self):
        return "ECC Curve '%s' cannot found." % self.curve


class ECCurve(object):
    """docstring for ECCurve"""
    def __init__(self, curve='secp256r1'):
        super(ECCurve, self).__init__()
        self.curve = curve
        self.get_curve()

    def secp256r1(self):
        self.P = int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16)
        self.N = int("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16)
        self.A = int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16)
        self.B = int("5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B", 16)
        self.Gx = int("6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296", 16)
        self.Gy = int("4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5", 16)
        self.G = (self.Gx, self.Gy)

    def secp256k1(self):
        self.P = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F", 16)
        self.N = int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16)
        self.A = 0
        self.B = 7
        self.Gx = int("6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296", 16)
        self.Gy = int("4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5", 16)
        self.G = (self.Gx, self.Gy)

    def get_curve(self):
        try:
            func = self.__getattribute__(self.curve)
            func()
        except AttributeError as e:
            raise ECCurveNotFound(self.curve)


# Elliptic curve parameters (secp256r1)
curve = ECCurve('secp256r1')

P = curve.P
N = curve.N
A = curve.A
B = curve.B
Gx = curve.Gx
Gy = curve.Gy
G = (Gx, Gy)

# Extended Euclidean Algorithm
def inv(a, n):
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high//low
        nm, new = hm-lm*r, high-low*r
        lm, low, hm, high = nm, new, lm, low
    return lm % n

def from_jacobian(p):
    z = inv(p[2], P)
    return ((p[0] * z**2) % P, (p[1] * z**3) % P)

def jacobian_double(p):
    if not p[1]:
        return (0, 0, 0)
    ysq = (p[1] ** 2) % P
    S = (4 * p[0] * ysq) % P
    M = (3 * p[0] ** 2 + A * p[2] ** 4) % P
    nx = (M**2 - 2 * S) % P
    ny = (M * (S - nx) - 8 * ysq ** 2) % P
    nz = (2 * p[1] * p[2]) % P
    return (nx, ny, nz)

def jacobian_add(p, q):
    if not p[1]:
        return q
    if not q[1]:
        return p
    U1 = (p[0] * q[2] ** 2) % P
    U2 = (q[0] * p[2] ** 2) % P
    S1 = (p[1] * q[2] ** 3) % P
    S2 = (q[1] * p[2] ** 3) % P
    if U1 == U2:
        if S1 != S2:
            return (0, 0, 1)
        return jacobian_double(p)
    H = U2 - U1
    R = S2 - S1
    H2 = (H * H) % P
    H3 = (H * H2) % P
    U1H2 = (U1 * H2) % P
    nx = (R ** 2 - H3 - 2 * U1H2) % P
    ny = (R * (U1H2 - nx) - S1 * H3) % P
    nz = (H * p[2] * q[2]) % P
    return (nx, ny, nz)

def jacobian_multiply(a, n):
    if a[1] == 0 or n == 0:
        return (0, 0, 1)
    if n == 1:
        return a
    if n < 0 or n >= N:
        return jacobian_multiply(a, n % N)
    if (n % 2) == 0:
        return jacobian_double(jacobian_multiply(a, n//2))
    if (n % 2) == 1:
        return jacobian_add(jacobian_double(jacobian_multiply(a, n//2)), a)

def to_jacobian(p):
    o = (p[0], p[1], 1)
    return o

def fast_multiply(a, n):
    return from_jacobian(jacobian_multiply(to_jacobian(a), n))

#Curve end
code_strings = {
    2: '01',
    10: '0123456789',
    16: '0123456789abcdef',
    32: 'abcdefghijklmnopqrstuvwxyz234567',
    58: '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz',
    256: ''.join([chr(x) for x in range(256)])
}

def get_code_string(base):
    if base in code_strings:
        return code_strings[base]
    else:
        raise ValueError("Invalid base!")

def decode(string, base):
    base = int(base)
    code_string = get_code_string(base)
    result = 0
    if base == 16:
        string = string.lower()
    while len(string) > 0:
        result *= base
        result += code_string.find(string[0])
        string = string[1:]
    return result

def decode_privkey(priv,formt=None):
    if not formt: formt = get_privkey_format(priv)
    if formt == 'decimal': return priv
    elif formt == 'bin': return decode(priv, 256)
    elif formt == 'bin_compressed': return decode(priv[:32], 256)
    elif formt == 'hex': return decode(priv, 16)
    elif formt == 'hex_compressed': return decode(priv[:64], 16)
    elif formt == 'wif': return decode(b58check_to_bin(priv),256)
    elif formt == 'wif_compressed':
        return decode(b58check_to_bin(priv)[:32],256)
    else: raise Exception("WIF does not represent privkey")

def get_privkey_format(priv):
    if isinstance(priv, int): return 'decimal'
    elif len(priv) == 32: return 'bin'
    elif len(priv) == 33: return 'bin_compressed'
    elif len(priv) == 64: return 'hex'
    elif len(priv) == 66: return 'hex_compressed'
    else:
        bin_p = b58check_to_bin(priv)
        if len(bin_p) == 32: return 'wif'
        elif len(bin_p) == 33: return 'wif_compressed'
        else: raise Exception("WIF does not represent privkey")

def encode_privkey(priv, formt, vbyte=0):
    if not isinstance(priv, int):
        return encode_privkey(decode_privkey(priv), formt, vbyte)
    if formt == 'decimal': return priv
    elif formt == 'bin': return encode(priv, 256, 32)
    elif formt == 'bin_compressed': return encode(priv, 256, 32)+b'\x01'
    elif formt == 'hex': return encode(priv, 16, 64)
    elif formt == 'hex_compressed': return encode(priv, 16, 64)+'01'
    elif formt == 'wif':
        return bin_to_b58check(encode(priv, 256, 32), 128+int(vbyte))
    elif formt == 'wif_compressed':
        return bin_to_b58check(encode(priv, 256, 32)+b'\x01', 128+int(vbyte))
    else: raise Exception("Invalid format!")

def encode(val, base, minlen=0):
    base, minlen = int(base), int(minlen)
    code_string = get_code_string(base)
    result = ""
    while val > 0:
        result = code_string[val % base] + result
        val //= base
    return code_string[0] * max(minlen - len(result), 0) + result

def encode_pubkey(pub, formt):
    if not isinstance(pub, (tuple, list)):
        pub = decode_pubkey(pub)
    if formt == 'decimal': return pub
    elif formt == 'bin': return b'\x04' + encode(pub[0], 256, 32) + encode(pub[1], 256, 32)
    elif formt == 'bin_compressed':
        return from_int_to_byte(2+(pub[1] % 2)) + encode(pub[0], 256, 32)
    elif formt == 'hex': return '04' + encode(pub[0], 16, 64) + encode(pub[1], 16, 64)
    elif formt == 'hex_compressed':
        return '0'+str(2+(pub[1] % 2)) + encode(pub[0], 16, 64)
    elif formt == 'bin_electrum': return encode(pub[0], 256, 32) + encode(pub[1], 256, 32)
    elif formt == 'hex_electrum': return encode(pub[0], 16, 64) + encode(pub[1], 16, 64)
    else: raise Exception("Invalid format!")

def privkey_to_pubkey(privkey):
    f = get_privkey_format(privkey)
    privkey = decode_privkey(privkey, f)
    if privkey >= N:
        raise Exception("Invalid privkey")
    return encode_pubkey(fast_multiply(G, privkey), 'hex_compressed')

def from_int_to_byte(a):
    return chr(a)

def pubkey_to_redeem(pubkey):
    return binascii.unhexlify('21'+ pubkey) + from_int_to_byte(int('ac',16))

def redeem_to_scripthash(redeem):
    return binascii.hexlify(bin_hash160(redeem))

def scripthash_to_address(scripthash):
    return bin_to_b58check(binascii.unhexlify(scripthash),int('17',16))

def bin_to_b58check(inp,magicbyte=0):
    inp_fmtd = chr(int(magicbyte)) + inp
    checksum = bin_dbl_sha256(inp_fmtd)[:4]
    return changebase(inp_fmtd+checksum, 256, 58)

def changebase(string, frm, to, minlen=0):
    if frm == to:
        return lpad(string, get_code_string(frm)[0], minlen)
    return encode(decode(string, frm), to, minlen)

def from_string_to_bytes(a):
    return a

def bin_dbl_sha256(s):
    bytes_to_hash = from_string_to_bytes(s)
    return hashlib.sha256(hashlib.sha256(bytes_to_hash).digest()).digest()

def random_string(x):
    s = os.urandom(x)
    ss=len(s)
    sss=str(os.urandom(x))
    ssss=len(sss)
    a=binascii.b2a_hex(s)
    aa=len(a)
    z=str(a)[2:34]
    zz=len(z)
    return str(a)[2:34]

def bytes_to_hex_string(b):
    if isinstance(b, str):
        return b
    return ''.join('{:02x}'.format(y) for y in b)

def bin_hash160(string):
    intermed = hashlib.sha256(string).digest()
    return hashlib.new('ripemd160', intermed).digest()

def bin_sha256(string):
    binary_data = string if isinstance(string, bytes) else bytes(string, 'utf-8')
    s=hashlib.sha256(binary_data).digest()
    return hashlib.sha256(binary_data).digest()

def sha256(string):
    return bytes_to_hex_string(bin_sha256(string))

def random_key():
    s1 = random_string(16)
    s11 = len(s1)
    s2 = str(random.randrange(2 ** 256))
    s22 = len(s2)
    s3 = str(int(time.time() * 1000000))
    s33 = len(s3)
    entropy = random_string(16) + str(random.randrange(2**256)) + str(int(time.time() * 1000000))
    s=len(entropy)
    return sha256(entropy)

def random_to_priv(key):
    print(key)
    s=bytes(key, encoding='utf8')
    print(s)
    return binascii.hexlify(s)
    # return key

def shengchengcanshu():
    random = random_key()
    ss=len(random)
    privkey = random_to_priv(random)
    s=len(privkey)
    pubkey = privkey_to_pubkey(privkey)
    redeemscript = pubkey_to_redeem(pubkey)
    scripthash = redeem_to_scripthash(redeemscript)
    address = scripthash_to_address(scripthash)
    return {'address':address,'privkey':privkey,'pubkey':pubkey}

if __name__=='__main__':

    # random = random_key()
    # privkey = random_to_priv(random)
    # pubkey = privkey_to_pubkey(privkey)
    # redeemscript = pubkey_to_redeem(pubkey)
    # scripthash = redeem_to_scripthash(redeemscript)
    # address = scripthash_to_address(scripthash)

    print (shengchengcanshu())