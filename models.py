from flask_sqlalchemy import SQLAlchemy
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# SQLAlchemy nesnesi
db = SQLAlchemy()
# Argon2 Parola Özetleyici nesnesi
ph = PasswordHasher()

class User(db.Model):
    # Veritabanı sütunları
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    totp_secret = db.Column(db.String(32), nullable=True)
    # YENİ: Kurtarma kodlarını JSON formatında saklayacak alan
    recovery_codes = db.Column(db.Text, nullable=True) # veya db.String(1000)

    def __init__(self, email, password):
        self.email = email
        # Parolayı oluşturma anında Argon2 ile özetle
        self.password_hash = ph.hash(password)

    def verify_password(self, password):
        """Kullanıcının girdiği parolayı depolanan özetle karşılaştırır."""
        try:
            # Argon2 ile doğrulama
            ph.verify(self.password_hash, password)
            return True
        except VerifyMismatchError:
            return False
        except Exception:
            # Format veya diğer hatalar
            return False