// --- Global Tanımlar ---
const contentArea = document.getElementById('content-area');
const messageArea = document.getElementById('message-area');

// --- Yardımcı Fonksiyon: Mesajları Gösterme ---
function displayMessage(message, isError = false) {
    messageArea.innerHTML = `<p class="${isError ? 'error' : 'success'}">${message}</p>`;
}

// ----------------------------------------------------------------
// --- SAYFA GÖRÜNÜMÜ FONKSİYONLARI ---
// ----------------------------------------------------------------

function showRegisterForm() {
    contentArea.innerHTML = `
        <h2>Hesap Oluştur</h2>
        <form id="register-form">
            <div class="info">
                <label for="email">E-posta</label>
                <input type="email" id="email" required>
            </div>
            <div class="info">
                <label for="password">Parola</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit">Kaydol</button>
        </form>
        <p>Zaten hesabınız var mı? <a href="#" id="show-login">Giriş Yap</a></p>
    `;
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('show-login').addEventListener('click', showLoginForm);
    messageArea.innerHTML = '';
}

function showLoginForm() {
    contentArea.innerHTML = `
        <h2>Giriş Yap</h2>
        <form id="login-form">
            <div class="info">
                <label for="email">E-posta</label>
                <input type="email" id="email" required>
            </div>
            <div class="info">
                <label for="password">Parola</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit">Giriş Yap</button>
        </form>
        <p>Hesabınız yok mu? <a href="#" id="show-register">Hesap Oluştur</a></p>
    `;
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('show-register').addEventListener('click', showRegisterForm);
    messageArea.innerHTML = '';
}

function showProfilePage() {
    contentArea.innerHTML = `
        <h2>✨ Hoş Geldiniz! (Profil Yönetimi)</h2>
        <p>Oturumunuz başarıyla açıldı. Güvenlik ayarlarınızı buradan yönetebilirsiniz.</p>

        <div class="action-buttons">
            <button id="setup-2fa-btn">🔒 2FA Kurulumunu Başlat</button>
            <button id="generate-recovery-btn">🔑 Kurtarma Kodlarını Üret/Yenile</button>
            <button id="logout-btn">Çıkış Yap</button>
        </div>
    `; 
    // Profil sayfasının altındaki "undefined" hatası, buradaki gereksiz kodların temizlenmesiyle çözülmelidir.

    document.getElementById('setup-2fa-btn').addEventListener('click', handleSetup2FA);
    document.getElementById('generate-recovery-btn').addEventListener('click', handleGenerateRecoveryCodes);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    displayMessage('Giriş başarılı!', false); 
}

function show2FAForm(email, password) {
    contentArea.innerHTML = `
        <h2>🔒 Güvenlik Doğrulaması Gerekli</h2>
        <p>Hesabınıza erişmek için lütfen aşağıdaki yöntemlerden **birini** kullanın. (TOTP veya Kurtarma Kodu)</p>
        
        <form id="2fa-form">
            <div class="info">
                <label for="totp-code">1. Yöntem: Authenticator Kodu</label>
                <input type="text" id="totp-code" inputmode="numeric" pattern="[0-9]*" maxlength="6" placeholder="6 Haneli TOTP Kodu">
            </div>
            
            <div class="info">
                <label for="recovery-code">2. Yöntem: Yedek Kurtarma Kodu</label>
                <input type="text" id="recovery-code" placeholder="8 Haneli Tek Kullanımlık Kurtarma Kodu">
            </div>
            
            <input type="hidden" id="auth-email" value="${email}">
            <input type="hidden" id="auth-password" value="${password}">
            
            <button type="submit">Doğrula ve Giriş Yap</button>
        </form>
        <p><a href="#" id="back-to-login">Geri Dön</a></p>
    `;
    document.getElementById('2fa-form').addEventListener('submit', handle2FAValidation);
    document.getElementById('back-to-login').addEventListener('click', showLoginForm); 
    displayMessage('Lütfen 2FA kodunuzu veya bir Kurtarma Kodunuzu girin.', false);
}

function showQRCodePage(qrCodeBase64, secret) {
    contentArea.innerHTML = `
        <h2>🔒 2FA Kurulumunu Tamamlayın</h2>
        <p>Lütfen bu QR kodu Google Authenticator, Authy veya başka bir TOTP uygulaması ile tarayın.</p>
        
        <div class="qr-container">
            <img src="data:image/png;base64,${qrCodeBase64}" alt="2FA QR Code" class="qr-code"> 
        </div>
        
        <p>Veya kodu manuel olarak girin: <strong>${secret}</strong></p>

        <p class="warning">QR kodu tarandıktan sonra, uygulama kod üretmeye başlayacaktır.</p>
        <p>Kurulumu tamamlamak için uygulamadan gelen kodu kullanarak **Giriş Yap**malısınız.</p>
        
        <button id="back-to-profile">Profil Sayfasına Geri Dön</button>
    `;
    
    document.getElementById('back-to-profile').addEventListener('click', showProfilePage);
    displayMessage('Kurulum tamamlandı. Profil sayfanıza dönün.', false);
}

function showRecoveryCodes(codes) {
    const codesHTML = codes.map(code => `<li>${code}</li>`).join('');
    contentArea.innerHTML = `
        <h2>🚨 Kurtarma Kodlarınız Oluşturuldu</h2>
        <p class="warning">BU KODLARI SADECE BİR KEZ GÖRÜYORSUNUZ! Lütfen yazdığınızdan ve güvenli bir yerde sakladığınızdan emin olun.</p>
        <ul class="recovery-codes-list">
            ${codesHTML}
        </ul>
        <p>Her kod tek kullanımlıktır ve telefonunuzun kaybolması durumunda 2FA'yı atlamak için kullanılır.</p>
        <button id="back-to-profile">Profil Sayfasına Geri Dön</button>
    `;
    document.getElementById('back-to-profile').addEventListener('click', showProfilePage);
    displayMessage('KODLARINIZI GÜVENLİ BİR YERE KAYDEDİN.', false);
}


// ----------------------------------------------------------------
// --- API ETKİLEŞİM FONKSİYONLARI ---
// ----------------------------------------------------------------

async function handleRegister(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (response.ok) {
        displayMessage(data.message, false);
        showLoginForm();
    } else if (response.status === 406) {
        let errorMessage = data.message + (data.reasons ? "<br>" : "");
        data.reasons.forEach(reason => {
            errorMessage += `• ${reason.message} ${reason.details ? '(' + reason.details + ')' : ''}<br>`;
        });
        displayMessage(errorMessage, true);
    } else {
        displayMessage(data.message, true);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (response.ok) {
        showProfilePage();
    } else if (response.status === 401 && data.requires_2fa) {
        show2FAForm(email, password);
    }
    else {
        displayMessage(data.message, true);
    }
}

async function handle2FAValidation(e) {
    e.preventDefault();
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const totp_code = document.getElementById('totp-code').value;
    const recovery_code = document.getElementById('recovery-code').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, totp_code, recovery_code })
    });

    const data = await response.json();

    if (response.ok) {
        showProfilePage();
        displayMessage(data.message, false);
    } else {
        displayMessage(data.message, true);
    }
}

// static/app.js

async function handleSetup2FA() {
    const response = await fetch('/setup-2fa', { method: 'GET' });
    const data = await response.json();

    if (response.ok) {
        if (data.already_setup) {
            // Hata değil, bilgi mesajı olarak göster
            displayMessage(data.message, false); 
            showProfilePage(); // Profilde kal
        } else {
            // Sadece veri tam ise sayfayı göster
            if (data.qr_code_base64 && data.totp_secret) {
                showQRCodePage(data.qr_code_base64, data.totp_secret);
            } else {
                displayMessage("QR Kod verisi alınamadı.", true);
            }
        }
    } else {
        displayMessage(data.message, true);
    }
}
async function handleGenerateRecoveryCodes() {
    const response = await fetch('/generate-recovery-codes', { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        showRecoveryCodes(data.recovery_codes);
    } else {
        displayMessage(data.message, true);
        if (response.status === 401) {
            showLoginForm();
        }
    }
}

async function handleLogout() {
    const response = await fetch('/logout', { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
        displayMessage(data.message, false);
    } else {
        displayMessage(data.message, true);
    }
    showRegisterForm();
}
// --- 2FA Zaten Kuruluysa Gösterilecek Sayfa ---
function showAlreadySetupPage(message, details) {
    contentArea.innerHTML = `
        <div class="info-container">
            <div class="status-icon">✅</div>
            <h2>${message}</h2>
            <p>${details}</p>
            <div class="alert-box">
                <strong>Not:</strong> Eğer cihazınızı kaybettiyseniz veya erişiminizi yitirdiyseniz, lütfen daha önce oluşturduğunuz <strong>Kurtarma Kodlarını</strong> kullanın.
            </div>
            <button id="back-to-profile">Profil Sayfasına Geri Dön</button>
        </div>
    `;
    document.getElementById('back-to-profile').addEventListener('click', showProfilePage);
}

// --- handleSetup2FA Fonksiyonunun Güncellenmiş Hali ---
async function handleSetup2FA() {
    const response = await fetch('/setup-2fa', { method: 'GET' });
    const data = await response.json();

    if (response.ok) {
        if (data.already_setup) {
            // Hiçbir şey olmaması yerine bu fonksiyonu çağırıyoruz:
            showAlreadySetupPage(data.message, data.details);
        } else {
            // İlk kurulumsa QR kodunu göster
            showQRCodePage(data.qr_code_base64, data.totp_secret);
        }
    } else {
        displayMessage(data.message, true);
    }
}


// --- Uygulama Başlangıcı ---
document.addEventListener('DOMContentLoaded', () => {
    // Uygulama başladığında ilk olarak kayıt formunu göster
    showRegisterForm(); 
});