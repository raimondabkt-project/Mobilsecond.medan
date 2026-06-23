from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from models import db, User
from werkzeug.security import check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message

auth_bp = Blueprint('auth', __name__)

# ==================== LOGIN ====================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Selamat datang, {user.nama}!', 'success')

            if user.role == 'admin':
                return redirect(url_for('main.dashboard_admin'))
            elif user.role == 'seller':
                return redirect(url_for('main.dashboard_seller'))
            else:
                return redirect(url_for('main.home'))

        else:
            flash('Email atau password salah!', 'danger')

    return render_template('login.html')

# ==================== LOGOUT ====================
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('main.home'))

# ==================== REGISTER ====================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nama = request.form.get('nama')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar!', 'danger')
            return redirect(url_for('auth.register'))

        user = User(nama=nama, email=email, role='buyer')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('✅ Akun buyer berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ==================== LUPA PASSWORD ====================
def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            try:
                s = get_serializer()
                token = s.dumps(email, salt='password-reset-salt')
                reset_url = url_for('auth.reset_password', token=token, _external=True)

                mail_username = current_app.config.get('MAIL_USERNAME', '')

                if mail_username:
                    msg = Message(
                        subject='Reset Password - Mobil Second Medan',
                        recipients=[email],
                        body=f'''Halo {user.nama},

Anda telah meminta reset password.

Silakan klik link berikut (berlaku 1 jam):
{reset_url}

Jika tidak meminta ini, abaikan email ini.
'''
                    )
                    current_app.extensions['mail'].send(msg)
                    flash('✅ Link reset password telah dikirim ke email Anda.', 'success')
                else:
                    flash('✅ [DEV MODE] Link reset ada di terminal/log server.', 'info')
                    print(f"[DEV] Reset link untuk {email}: {reset_url}")

            except Exception as e:
                print(f"Error: {e}")
                flash('Gagal memproses. Coba lagi.', 'danger')
        else:
            flash('Jika email terdaftar, link akan dikirim.', 'info')

        return redirect(url_for('auth.forgot_password'))

    return render_template('forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = get_serializer()
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('Link sudah kedaluwarsa.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    except:
        flash('Link tidak valid.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User tidak ditemukan.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if len(password) < 6:
            flash('Password minimal 6 karakter.', 'danger')
            return render_template('reset_password.html', token=token)

        if password != confirm:
            flash('Konfirmasi password tidak cocok.', 'danger')
            return render_template('reset_password.html', token=token)

        user.set_password(password)
        db.session.commit()
        flash('✅ Password berhasil direset! Silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)