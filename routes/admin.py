from flask import Blueprint, render_template
from flask_login import login_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard_admin')
@login_required
def dashboard_admin():
    return render_template('dashboard_admin.html')


@admin_bp.route('/dashboard_seller')
@login_required
def dashboard_seller():
    return render_template('dashboard_seller.html')