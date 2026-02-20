# app.py
import os
from flask import Flask, jsonify, session, render_template
from models import db, User # models.py'den db ve User import edildi
from flask_smorest import Api # <-- YENİ IMPORT: Swagger için

# resources/auth.py dosyasından Blueprint'i import et
from resources.auth import blp as AuthBlueprint # <-- YENİ IMPORT

# --- Uygulama Başlatma ---
app = Flask(__name__)

# --- Yapılandırma Ayarları ---
app.config['SECRET_KEY'] = 'cok-gizli-anahtar-buraya' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Veritabanı nesnesini uygulamaya bağla
db.init_app(app)

# --- API Belgeleme Yapılandırması (OpenAPI/Swagger) ---
app.config["API_TITLE"] = "BIL 420 Güvenli Kimlik Doğrulama API'si"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/" 
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Flask-smorest API nesnesini oluştur
api = Api(app)

# Blueprint'i uygulamaya kaydet (Modülerlik!)
api.register_blueprint(AuthBlueprint)


# --- Veritabanı Oluşturma Fonksiyonu ---
def create_db():
    """Uygulama çalıştırılmadan önce veritabanını ve tabloları oluşturur."""
    with app.app_context():
        # instance klasörünü oluşturur
        if not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path)
        
        # Tüm tabloları oluştur
        db.create_all()
        print("Veritabanı tabloları oluşturuldu.")


# --- Frontend Uç Noktaları ---
@app.route('/')
def index():
    """Minimal frontend'i sunar."""
    return render_template('index.html')

@app.route('/logout', methods=['POST'])
def logout():
    """Oturumu sonlandırır."""
    if 'user_id' in session:
        session.pop('user_id')
        session.pop('logged_in')
        return jsonify({"message": "Başarıyla çıkış yapıldı."}), 200
    return jsonify({"message": "Zaten oturum açık değil."}), 400


# --- Uygulama Başlatma ---
if __name__ == '__main__':
    # GEÇİCİ OLARAK, instance klasöründeki eski veritabanını silmeyi zorunlu kılalım
    import shutil
    db_path = os.path.join(app.instance_path, 'app.db')
    if os.path.exists(app.instance_path):
        try:
            os.remove(db_path) # Eski dosyayı sil
            print("Eski veritabanı silindi.")
        except OSError:
            # Dosya hala bir işlem tarafından kullanılıyorsa, klasörü sil
            shutil.rmtree(app.instance_path, ignore_errors=True)
            print("Eski instance klasörü silindi.")
            
    create_db()
    
    # Debug modunda yeniden başlatma sorun olmaması için şimdilik False yapalım
    app.run(debug=False)