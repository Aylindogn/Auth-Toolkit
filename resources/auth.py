# resources/auth.py
from flask import jsonify, request, session
from flask_smorest import Blueprint
from functools import wraps
import json
import secrets
from models import db, User, ph # db, User ve Argon2 Hash nesnesi (ph) models.py'den geldi
from argon2.exceptions import VerifyMismatchError
from zxcvbn import zxcvbn
import hashlib
import requests
import pyotp
import qrcode
from io import BytesIO
import base64

# --- Blueprint Tanımlama (Swagger için) ---
blp = Blueprint(
    "Auth", __name__, description="Kullanıcı Kayıt, Giriş ve Güvenlik İşlemleri"
)

# --- Yardımcı Fonksiyon: Oturum Kontrolü ---
def login_required(f):
    """Kullanıcının oturum açıp açmadığını kontrol eden dekoratör."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Oturum açmanız gerekiyor."}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Yardımcı Fonksiyon: HIBP Kontrolü ---
def check_hibp(password):
    """Parolayı HIBP (Have I Been Pwned) hizmetiyle k-anonimlik kullanarak kontrol eder."""
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1_password[:5] # k-anonimlik için ilk 5 karakter [cite: 79]
    suffix = sha1_password[5:]

    HIBP_API_URL = f"https://api.pwnedpasswords.com/range/{prefix}"
    
    try:
        response = requests.get(HIBP_API_URL)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        print("HIBP API'sine erişilemedi. Güvenlik kontrolü atlandı.")
        return 0

    for line in response.text.splitlines():
        hash_suffix, count = line.split(':')
        if hash_suffix == suffix:
            return int(count)
            
    return 0

# ----------------------------------------------------------------
# --- API Uç Noktaları (Blueprint Kullanılarak) ---
# ----------------------------------------------------------------

@blp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email ve parola gerekli."}), 400

    rejection_reasons = []

    # 1. HIBP SIZDIRILMIŞ PAROLA KONTROLÜ
    pwned_count = check_hibp(password)
    if pwned_count > 0:
        rejection_reasons.append({
            "type": "HIBP_LEAK",
            "message": f"Bu parola, bilinen sızıntılarda {pwned_count} kez kullanılmıştır."
        })
    
    # 2. ZXCBN PAROLA ANALİZİ
    password_check = zxcvbn(password)
    score = password_check['score']
    MIN_SCORE = 3 
    
    if score < MIN_SCORE:
        warning = password_check.get('feedback', {}).get('warning', 'Parolanız çok zayıf.')
        suggestions = password_check.get('feedback', {}).get('suggestions', [])
        
        rejection_reasons.append({
            "type": "ZXCVBN_WEAKNESS",
            "message": "Parola kalitesi yetersiz.",
            "details": warning,
            "suggestions": suggestions
        })
    
    # --- SONUÇ: REDDETME VEYA KABUL ETME ---
    if rejection_reasons:
        return jsonify({
            "message": "Parola güvenlik gereksinimlerini karşılamıyor.",
            "reasons": rejection_reasons
        }), 406
    # ----------------------------------------
    
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Bu e-posta adresi zaten kullanılıyor."}), 409

    # 3. Güvenli Parola Saklama (Argon2)
    try:
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Kayıt başarılı. Parolanız güvenli şekilde saklandı."}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Kayıt hatası: {e}") 
        return jsonify({"message": "Bir hata oluştu, lütfen tekrar deneyin."}), 500


@blp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    totp_code = data.get('totp_code')
    recovery_code = data.get('recovery_code')

    if not email or not password:
        return jsonify({"message": "Email ve parola gerekli."}), 400

    user = User.query.filter_by(email=email).first()

    # Parola kontrolü
    if user is None or not user.verify_password(password):
        return jsonify({"message": "Geçersiz kimlik bilgileri."}), 401

    # 2FA gerekliliği kontrolü
    if user.totp_secret:
        # 1. TOTP Kodu Kontrolü
        if totp_code:
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(totp_code):
                session['user_id'] = user.id
                session['logged_in'] = True
                return jsonify({"message": "Giriş başarılı (2FA Doğrulandı).", "requires_2fa": True}), 200
        
        # 2. Kurtarma Kodu Kontrolü
        if recovery_code and user.recovery_codes:
            hashed_codes = json.loads(user.recovery_codes)
            
            used_code_index = -1
            
            for i, hashed_code in enumerate(hashed_codes):
                try:
                    ph.verify(hashed_code, recovery_code)
                    used_code_index = i
                    break 
                except VerifyMismatchError:
                    continue 
            
            if used_code_index != -1:
                # Başarılı! Kodu tek kullanımlık olduğu için listeden sil
                hashed_codes.pop(used_code_index)
                user.recovery_codes = json.dumps(hashed_codes)
                db.session.commit()
                
                session['user_id'] = user.id
                session['logged_in'] = True
                return jsonify({"message": "Giriş başarılı (Kurtarma Kodu Kullanıldı).", "requires_2fa": True, "remaining_codes": len(hashed_codes)}), 200
            
        # 3. Hiçbir kod başarılı değilse
        return jsonify({"message": "2FA kodu veya geçerli bir Kurtarma Kodu gerekli.", "requires_2fa": True}), 401
    
    # 2FA kurulu değilse, standart giriş yap
    session['user_id'] = user.id
    session['logged_in'] = True
    return jsonify({"message": "Giriş başarılı.", "requires_2fa": False}), 200



@blp.route('/setup-2fa', methods=['GET'])
@login_required
def setup_2fa():
    user = User.query.get(session['user_id'])

    # KRİTİK DEĞİŞİKLİK: Eğer zaten kurulmuşsa QR üretme, bilgi ver.
    if user.totp_secret:
        return jsonify({
            "message": "2FA zaten kurulmuş ve aktif durumdadır. Güvenliğiniz için QR kodu tekrar gösterilmez.",
            "already_setup": True
        }), 200

    # Eğer kurulmamışsa (ilk kezse) üretim devam eder:
    secret = pyotp.random_base32()
    user.totp_secret = secret
    db.session.commit()

    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="BIL 420 Projesi"
    )

    img = qrcode.make(totp_uri)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return jsonify({
        "message": "2FA kurulumunu tamamlamak için QR kodu tarayın.",
        "qr_code_base64": qr_base64,
        "totp_secret": secret,
        "already_setup": False
    }), 200

@blp.route('/generate-recovery-codes', methods=['POST'])
@login_required 
def generate_recovery_codes():
    user = User.query.get(session['user_id'])
    
    NUM_CODES = 10
    
    raw_codes = []
    hashed_codes = []

    for _ in range(NUM_CODES):
        # 8 haneli rastgele alfanumerik kod üret
        code = secrets.token_urlsafe(8).upper()
        raw_codes.append(code)
        
        # Argon2 ile özetle
        hashed_codes.append(ph.hash(code))

    # Özetlenmiş kodları veritabanına JSON dizesi olarak kaydet
    user.recovery_codes = json.dumps(hashed_codes)
    db.session.commit()

    return jsonify({
        "message": "Kurtarma kodları başarıyla oluşturuldu.",
        "recovery_codes": raw_codes, 
        "warning": "Bu kodlar tek kullanımlıktır ve sadece bir kez gösterilecektir. Lütfen güvenli bir yere kaydedin."
    }), 201