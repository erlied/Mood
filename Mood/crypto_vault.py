"""
Mood - Password + AES encryption + lockout + opaque folder ids
"""

import os
import time
import base64
import atexit
import hashlib
import shutil
import json
from pathlib import Path
from typing import Optional, List

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import config
from logger import log

SALT_FILE = config.APP_ROOT / ".mood_salt"
VERIFY_FILE = config.APP_ROOT / ".mood_verify"
LOCKOUT_FILE = config.APP_ROOT / ".mood_lockout"
ENC_SUFFIX = ".mood"
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
        backend=default_backend(),
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def folder_id_for_name(name: str) -> str:
    """Opaque folder name derived from performer name (not reversible without DB)."""
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
    return h


class Vault:
    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._unlocked = False
        self._temp_files: List[Path] = []

    @property
    def is_unlocked(self) -> bool:
        return self._unlocked and self._fernet is not None

    def has_password(self) -> bool:
        return SALT_FILE.exists() and VERIFY_FILE.exists()

    # ----- lockout -----
    def _load_lockout(self) -> dict:
        if not LOCKOUT_FILE.exists():
            return {"fails": 0, "until": 0}
        try:
            return json.loads(LOCKOUT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"fails": 0, "until": 0}

    def _save_lockout(self, data: dict):
        try:
            LOCKOUT_FILE.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass

    def lockout_remaining(self) -> int:
        data = self._load_lockout()
        until = data.get("until", 0)
        left = int(until - time.time())
        return max(0, left)

    def register_failed_attempt(self) -> int:
        data = self._load_lockout()
        data["fails"] = int(data.get("fails", 0)) + 1
        if data["fails"] >= MAX_ATTEMPTS:
            data["until"] = time.time() + LOCKOUT_SECONDS
            data["fails"] = 0
            self._save_lockout(data)
            return LOCKOUT_SECONDS
        self._save_lockout(data)
        return 0

    def clear_lockout(self):
        self._save_lockout({"fails": 0, "until": 0})

    def setup_password(self, password: str) -> bool:
        if len(password) < 4:
            return False
        salt = os.urandom(16)
        key = _derive_key(password, salt)
        f = Fernet(key)
        token = f.encrypt(b"MOOD_OK")
        config.APP_ROOT.mkdir(parents=True, exist_ok=True)
        SALT_FILE.write_bytes(salt)
        VERIFY_FILE.write_bytes(token)
        self._fernet = f
        self._unlocked = True
        self.clear_lockout()
        log.info("Vault password set")
        return True

    def unlock(self, password: str) -> bool:
        if not self.has_password():
            return False
        left = self.lockout_remaining()
        if left > 0:
            log.warning(f"Lockout active: {left}s left")
            return False
        try:
            salt = SALT_FILE.read_bytes()
            key = _derive_key(password, salt)
            f = Fernet(key)
            token = VERIFY_FILE.read_bytes()
            if f.decrypt(token) != b"MOOD_OK":
                self.register_failed_attempt()
                return False
            self._fernet = f
            self._unlocked = True
            self.clear_lockout()
            log.info("Vault unlocked")
            return True
        except Exception as e:
            log.warning(f"Unlock failed: {e}")
            self.register_failed_attempt()
            return False

    def lock(self):
        self.cleanup_temp()
        self._fernet = None
        self._unlocked = False
        log.info("Vault locked")

    def is_encrypted_path(self, path: Path) -> bool:
        # .mood new, .goon legacy
        return path.name.endswith(ENC_SUFFIX) or path.name.endswith(".goon")

    def encrypt_file(self, src: Path, dest_dir: Optional[Path] = None) -> Optional[Path]:
        if not self.is_unlocked:
            log.error("encrypt_file: vault locked")
            return None
        try:
            data = src.read_bytes()
            enc = self._fernet.encrypt(data)
            out_dir = dest_dir if dest_dir else src.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / (src.name + ENC_SUFFIX)
            if out.exists():
                stem = src.name
                c = 1
                while out.exists():
                    out = out_dir / f"{stem}_{c:03d}{ENC_SUFFIX}"
                    c += 1
            out.write_bytes(enc)
            log.debug(f"encrypted {src.name} → {out.name}")
            return out
        except Exception as e:
            log.error(f"encrypt_file {src}: {e}")
            return None

    def decrypt_to_bytes(self, enc_path: Path) -> Optional[bytes]:
        if not self.is_unlocked:
            return None
        try:
            return self._fernet.decrypt(enc_path.read_bytes())
        except InvalidToken:
            log.error(f"Invalid token: {enc_path}")
            return None
        except Exception as e:
            log.error(f"decrypt {enc_path}: {e}")
            return None

    def decrypt_to_temp(self, enc_path: Path) -> Optional[Path]:
        raw = self.decrypt_to_bytes(enc_path)
        if raw is None:
            return None
        temp_dir = getattr(config, "DECRYPT_TEMP", config.APP_ROOT / "decrypt_temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        name = enc_path.name
        if name.endswith(ENC_SUFFIX):
            name = name[: -len(ENC_SUFFIX)]
        elif name.endswith(".goon"):
            name = name[:-5]
        out = temp_dir / name
        if out.exists():
            return out
        out.write_bytes(raw)
        self._temp_files.append(out)
        return out

    def resolve_for_display(self, path: Path) -> Optional[Path]:
        if not path.exists():
            return None
        if self.is_encrypted_path(path):
            return self.decrypt_to_temp(path)
        return path

    def cleanup_temp(self):
        temp_dir = getattr(config, "DECRYPT_TEMP", config.APP_ROOT / "decrypt_temp")
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                log.info("decrypt_temp cleared")
            except Exception as e:
                log.warning(f"cleanup_temp: {e}")
        self._temp_files.clear()


vault = Vault()
atexit.register(vault.cleanup_temp)
