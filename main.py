from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import datetime
import secrets
import json
import os

app = Flask(__name__)
app.secret_key = 'change_this_to_a_random_secret_key'

# ============ بيانات الأدمن ============
ADMIN_USERNAME = "Akatsuki_019"
ADMIN_PASSWORD = "B"
ADMIN_PROMO_CODE = "CC"

# ============ ملف البيانات ============
DATA_FILE = "key.json"

def load_data():
    global users, standalone_keys
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            users = data.get("users", {})
            standalone_keys = data.get("standalone_keys", {})
            # تحويل النصوص إلى datetime
            for uname, u in users.items():
                u['expiry'] = datetime.datetime.fromisoformat(u['expiry'])
            for k, exp in standalone_keys.items():
                standalone_keys[k] = datetime.datetime.fromisoformat(exp)
    else:
        users = {}
        standalone_keys = {}

def save_data():
    data = {
        "users": {},
        "standalone_keys": {}
    }
    for uname, u in users.items():
        data["users"][uname] = {
            "password": u['password'],
            "promo_code": u['promo_code'],
            "key": u['key'],
            "expiry": u['expiry'].isoformat()
        }
    for k, exp in standalone_keys.items():
        data["standalone_keys"][k] = exp.isoformat()
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# تحميل البيانات عند بدء التشغيل
load_data()

# ============ التصميم العام (ثيم أحمر) ============
BASE_STYLE = """
<style>
    * { box-sizing: border-box; }
    body {
        background: #16090c;
        color: #f5f1f2;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
    }
    .panel {
        background: #1f0f13;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7);
        width: 380px;
        border: 1px solid #3b1a22;
    }
    .panel h2 {
        text-align: center;
        color: #f43f5e;
        margin-bottom: 25px;
        font-size: 24px;
        letter-spacing: 1px;
    }
    label {
        display: block;
        margin-bottom: 8px;
        font-size: 14px;
        color: #b08a96;
    }
    input, select {
        width: 100%;
        padding: 12px;
        margin-bottom: 20px;
        background: #2a151c;
        border: 1px solid #4a2530;
        color: #fff;
        border-radius: 10px;
        font-size: 15px;
        outline: none;
        transition: 0.3s;
    }
    input:focus, select:focus {
        border-color: #f43f5e;
        box-shadow: 0 0 8px rgba(244, 63, 94, 0.4);
    }
    button {
        width: 100%;
        background: linear-gradient(135deg, #e11d48, #be123c);
        color: white;
        border: none;
        padding: 14px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 10px;
        cursor: pointer;
        transition: 0.3s;
    }
    button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }
    .alert {
        margin-top: 20px;
        background: #3d1320;
        color: #fb7185;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        font-size: 14px;
        border: 1px solid #9f1239;
        word-break: break-all;
    }
    .error {
        background: #7f1d1d;
        color: #fca5a5;
        border-color: #b91c1c;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
    th, td {
        border: 1px solid #4a2530;
        padding: 8px;
        text-align: center;
        font-size: 13px;
    }
    th {
        background: #2a151c;
        color: #fb7185;
    }
    a {
        color: #fb7185;
        text-decoration: none;
        margin-top: 20px;
        display: inline-block;
    }
    a:hover { text-decoration: underline; }
    .section {
        margin-top: 30px;
        border-top: 1px solid #3b1a22;
        padding-top: 20px;
    }
</style>
"""

# ============ قوالب الصفحات (نفسها بدون تغيير) ============
USER_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Shell Akatsuki - تسجيل الدخول</title>
    """ + BASE_STYLE + """
</head>
<body>
    <div class="panel">
        <h2>Shell Akatsuki</h2>
        <form method="POST">
            <label>اسم المستخدم:</label>
            <input type="text" name="username" required>
            <label>كلمة المرور:</label>
            <input type="password" name="password" required>
            <label>الكود الترويجي:</label>
            <input type="text" name="promo_code" required>
            <button type="submit">تسجيل الدخول</button>
        </form>
        {% if error %}
            <div class="alert error">{{ error }}</div>
        {% endif %}
        {% if key %}
            <div class="alert">مفتاحك: {{ key }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Shell Akatsuki - دخول الأدمن</title>
    """ + BASE_STYLE + """
</head>
<body>
    <div class="panel">
        <h2>لوحة الأدمن</h2>
        <form method="POST">
            <label>اسم المستخدم:</label>
            <input type="text" name="admin_username" required>
            <label>كلمة المرور:</label>
            <input type="password" name="admin_password" required>
            <label>الكود الترويجي:</label>
            <input type="text" name="admin_promo_code" required>
            <button type="submit">دخول</button>
        </form>
        {% if error %}
            <div class="alert error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

ADMIN_PANEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Shell Akatsuki - لوحة التحكم</title>
    """ + BASE_STYLE + """
</head>
<body>
    <div class="panel" style="width: 600px;">
        <h2>لوحة التحكم</h2>

        <h3>إنشاء مستخدم جديد</h3>
        <form method="POST">
            <label>اسم المستخدم:</label>
            <input type="text" name="new_username" required>
            <label>كلمة المرور:</label>
            <input type="password" name="new_password" required>
            <label>الكود الترويجي:</label>
            <input type="text" name="new_promo" required>
            <label>مدة صلاحية المفتاح (ساعات):</label>
            <select name="duration">
                <option value="1">ساعة واحدة</option>
                <option value="24">24 ساعة</option>
                <option value="168">أسبوع</option>
                <option value="720">شهر</option>
            </select>
            <button type="submit" name="action" value="create_user">إنشاء المستخدم</button>
        </form>
        {% if user_alert_msg %}
            <div class="alert">{{ user_alert_msg }}</div>
        {% endif %}

        <div class="section">
            <h3>إنشاء مفتاح مستقل (بدون مستخدم)</h3>
            <form method="POST">
                <label>مدة صلاحية المفتاح (ساعات):</label>
                <select name="key_duration">
                    <option value="1">ساعة واحدة</option>
                    <option value="24">24 ساعة</option>
                    <option value="168">أسبوع</option>
                    <option value="720">شهر</option>
                </select>
                <button type="submit" name="action" value="create_key">إنشاء مفتاح</button>
            </form>
            {% if key_alert_msg %}
                <div class="alert">{{ key_alert_msg }}</div>
            {% endif %}
        </div>

        <div class="section">
            <h3>المستخدمون الحاليون</h3>
            <table>
                <tr><th>اسم المستخدم</th><th>المفتاح</th><th>تاريخ الانتهاء</th></tr>
                {% for uname, data in users.items() %}
                <tr>
                    <td>{{ uname }}</td>
                    <td>{{ data.key }}</td>
                    <td>{{ data.expiry.strftime('%Y-%m-%d %H:%M') }}</td>
                </tr>
                {% endfor %}
            </table>

            <h3>المفاتيح المستقلة</h3>
            <table>
                <tr><th>المفتاح</th><th>تاريخ الانتهاء</th></tr>
                {% for key, exp in standalone_keys.items() %}
                <tr>
                    <td>{{ key }}</td>
                    <td>{{ exp.strftime('%Y-%m-%d %H:%M') }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <a href="/logout">تسجيل الخروج</a>
    </div>
</body>
</html>
"""

# ---------- وظائف مساعدة ----------
def generate_key():
    return secrets.token_hex(8).upper()

# ---------- مسارات ----------
@app.route('/', methods=['GET', 'POST'])
def user_login():
    error = None
    key = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        promo = request.form.get('promo_code', '').strip()

        user = users.get(username)
        if user and user['password'] == password and user['promo_code'] == promo:
            if datetime.datetime.now() > user['expiry']:
                error = "انتهت صلاحية هذا الحساب"
            else:
                if not user['key']:
                    user['key'] = generate_key()
                    save_data()  # حفظ البيانات بعد توليد المفتاح
                key = user['key']
        else:
            error = "بيانات الدخول غير صحيحة"

    return render_template_string(USER_LOGIN_TEMPLATE, error=error, key=key)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('admin_username', '').strip()
        password = request.form.get('admin_password', '').strip()
        promo = request.form.get('admin_promo_code', '').strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD and promo == ADMIN_PROMO_CODE:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = "بيانات الأدمن غير صحيحة"
    return render_template_string(ADMIN_LOGIN_TEMPLATE, error=error)

@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    user_alert_msg = None
    key_alert_msg = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_user':
            new_username = request.form.get('new_username', '').strip()
            new_password = request.form.get('new_password', '').strip()
            new_promo = request.form.get('new_promo', '').strip()
            hours = int(request.form.get('duration', 24))

            if new_username in users:
                user_alert_msg = "اسم المستخدم موجود مسبقًا"
            else:
                expiry = datetime.datetime.now() + datetime.timedelta(hours=hours)
                new_key = generate_key()
                users[new_username] = {
                    'password': new_password,
                    'promo_code': new_promo,
                    'key': new_key,
                    'expiry': expiry
                }
                save_data()  # حفظ البيانات بعد إنشاء المستخدم
                user_alert_msg = f"تم إنشاء المستخدم [{new_username}] بنجاح، مفتاحه: {new_key}"

        elif action == 'create_key':
            hours = int(request.form.get('key_duration', 24))
            expiry = datetime.datetime.now() + datetime.timedelta(hours=hours)
            new_key = generate_key()
            standalone_keys[new_key] = expiry
            save_data()  # حفظ البيانات بعد إنشاء المفتاح
            key_alert_msg = f"تم إنشاء المفتاح المستقل: {new_key}"

    return render_template_string(
        ADMIN_PANEL_TEMPLATE,
        user_alert_msg=user_alert_msg,
        key_alert_msg=key_alert_msg,
        users=users,
        standalone_keys=standalone_keys
    )

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# ---------- واجهة API للتحقق من المفتاح ----------
@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data"})

    key = data.get('key')

    # التحقق من مفاتيح المستخدمين
    for uname, user_data in users.items():
        if user_data['key'] == key:
            if datetime.datetime.now() < user_data['expiry']:
                return jsonify({"success": True, "message": "Key is valid!"})
            else:
                return jsonify({"success": False, "message": "Key expired!"})

    # التحقق من المفاتيح المستقلة
    if key in standalone_keys:
        if datetime.datetime.now() < standalone_keys[key]:
            return jsonify({"success": True, "message": "Key is valid!"})
        else:
            del standalone_keys[key]
            save_data()
            return jsonify({"success": False, "message": "Key expired!"})

    return jsonify({"success": False, "message": "Invalid key!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
