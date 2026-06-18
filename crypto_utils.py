from __future__ import annotations

import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

if getattr(sys, 'frozen', False):
    _BASE = Path(sys.executable).resolve().parent
else:
    _BASE = Path(__file__).resolve().parent
DATA_DIR = _BASE / "data"
_PRIVATE_KEY_PATH = DATA_DIR / "teacher_private.pem"
_PUBLIC_KEY_PATH = DATA_DIR / "teacher_public.pem"

_KEY_SIZE = 2048
_AES_KEY_BYTES = 32
_IV_BYTES = 16

def _ensure_keys() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if _PRIVATE_KEY_PATH.exists() and _PUBLIC_KEY_PATH.exists():
        return
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=_KEY_SIZE)
    public_key = private_key.public_key()

    _PRIVATE_KEY_PATH.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    _PUBLIC_KEY_PATH.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

def _load_private_key() -> rsa.RSAPrivateKey:
    _ensure_keys()
    return serialization.load_pem_private_key(
        _PRIVATE_KEY_PATH.read_bytes(), password=None
    )

def _load_public_key() -> rsa.RSAPublicKey:
    _ensure_keys()
    return serialization.load_pem_public_key(_PUBLIC_KEY_PATH.read_bytes())

def encrypt_bytes(plaintext: bytes) -> bytes:
    public_key = _load_public_key()

    aes_key = os.urandom(_AES_KEY_BYTES)
    iv = os.urandom(_IV_BYTES)

    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len] * pad_len)
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    encrypted_key = public_key.encrypt(
        aes_key + iv,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    key_len = len(encrypted_key)
    return key_len.to_bytes(2, "big") + encrypted_key + ciphertext

def decrypt_bytes(data: bytes) -> bytes:
    private_key = _load_private_key()

    key_len = int.from_bytes(data[:2], "big")
    encrypted_key = data[2 : 2 + key_len]
    ciphertext = data[2 + key_len :]

    aes_key_iv = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    aes_key = aes_key_iv[:_AES_KEY_BYTES]
    iv = aes_key_iv[_AES_KEY_BYTES : _AES_KEY_BYTES + _IV_BYTES]

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    pad_len = plaintext[-1]
    return plaintext[:-pad_len]

_PBKDF2_ITERATIONS = 600_000

def derive_key(password: str, salt: bytes) -> bytes:
    import hashlib
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))

def encrypt_with_password(plaintext: bytes, password: str) -> bytes:
    import hashlib

    salt = os.urandom(16)
    key = derive_key(password, salt)
    verify_hash = hashlib.sha256(password.encode("utf-8")).digest()
    iv = os.urandom(_IV_BYTES)

    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len] * pad_len)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return salt + verify_hash + iv + ciphertext

def decrypt_with_password(data: bytes, password: str) -> bytes:
    import hashlib

    salt = data[:16]
    verify_hash = data[16:48]
    iv = data[48:64]
    ciphertext = data[64:]

    if hashlib.sha256(password.encode("utf-8")).digest() != verify_hash:
        raise ValueError("密码错误")

    key = derive_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    pad_len = plaintext[-1]
    return plaintext[:-pad_len]

def encrypt_question_bank(plaintext: bytes, password: str) -> bytes:
    pwd_encrypted = encrypt_with_password(plaintext, password)
    rsa_encrypted_password = encrypt_bytes(password.encode("utf-8"))
    rsa_len = len(rsa_encrypted_password)
    return rsa_len.to_bytes(2, "big") + rsa_encrypted_password + pwd_encrypted

def decrypt_question_bank_as_teacher(data: bytes) -> bytes:
    rsa_len = int.from_bytes(data[:2], "big")
    rsa_encrypted_password = data[2 : 2 + rsa_len]
    pwd_encrypted = data[2 + rsa_len :]
    password = decrypt_bytes(rsa_encrypted_password).decode("utf-8")
    return decrypt_with_password(pwd_encrypted, password)

def decrypt_question_bank_as_student(data: bytes, password: str) -> bytes:
    rsa_len = int.from_bytes(data[:2], "big")
    pwd_encrypted = data[2 + rsa_len :]
    return decrypt_with_password(pwd_encrypted, password)