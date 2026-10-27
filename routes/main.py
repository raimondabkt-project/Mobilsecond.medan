from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, Mobil, User, MobilFoto
from werkzeug.utils import secure_filename
from elasticsearch_utils import index_mobil, buat_index, cari_mobil
import os

main_bp = Blueprint('main', __name__)



@main_bp.route('/')
def home():
    recommended_cars = (
        Mobil.query
        .filter_by(is_recommended=True, status='Ready')
        .order_by(Mobil.id.desc())
        .limit(6)
        .all()
    )
    return render_template('index.html', recommended=recommended_cars)


@main_bp.route('/katalog')
def katalog():
    query = request.args.get('q', '').strip()

    try:
        if query:
            # Ambil hasil dari Elasticsearch
            results = cari_mobil(query=query, limit=100)
            mobil_ids = [int(hit['_id']) for hit in results if hit.get('_id')]

            if mobil_ids:
                mobils = Mobil.query.filter(
                    Mobil.id.in_(mobil_ids),
                    Mobil.status == 'Ready'
                ).all()
            else:
                mobils = []
        else:
            mobils = Mobil.query.filter_by(status='Ready').all()

    except Exception as e:
        print(f"⚠️ ES Error: {e}")
        # Fallback ke MySQL
        if query:
            mobils = Mobil.query.filter(
                (Mobil.status == 'Ready') &
                ((Mobil.merek.ilike(f'%{query}%')) | (Mobil.model.ilike(f'%{query}%')))
            ).all()
        else:
            mobils = Mobil.query.filter_by(status='Ready').all()

    merek_list = sorted({m.merek for m in mobils if m.merek})

    return render_template('katalog.html',
                           mobils=mobils,
                           query=query,
                           merek_list=merek_list)


@main_bp.route('/detail/<string:model>')
def detail_mobil(model):
    from models import Mobil, User

    mobil = Mobil.query.filter(Mobil.model.ilike(model)).first()

    if not mobil:
        flash("Mobil tidak ditemukan.", "danger")
        return redirect(url_for('main.katalog'))

    sellers = User.query.filter_by(role='seller', status='aktif').all()

    return render_template('detail_mobil.html', mobil=mobil, sellers=sellers)


@main_bp.route('/cara_beli')
def cara_beli():
    return render_template('cara_beli.html')


@main_bp.route('/tentang')
def tentang():
    return render_template('tentang.html')


@main_bp.route('/favorit')
def favorit():
    favorite_cars = Mobil.query.filter_by(is_favorite=True, status='Ready').all()
    return render_template('favorit.html', favorites=favorite_cars)



@main_bp.route('/admin/dashboard')
@login_required
def dashboard_admin():
    if current_user.role != 'admin':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('main.home'))

    mobils = Mobil.query.all()
    sellers = User.query.filter_by(role='seller').all()
    return render_template('dashboard_admin.html', mobils=mobils, sellers=sellers)

@main_bp.route('/seller/dashboard')
@login_required
def dashboard_seller():
    if current_user.role != 'seller':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('main.home'))

    mobils = Mobil.query.filter_by(seller_id=current_user.id).all()
    return render_template('dashboard_seller.html', mobils=mobils)



@main_bp.route('/admin/tambah-unit', methods=['POST'])
@login_required
def tambah_unit():
    if current_user.role != 'admin':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('main.home'))

    try:
        kode_mobil = request.form.get('kode_mobil')
        merek = request.form.get('merek')
        model = request.form.get('model')
        harga = int(request.form.get('harga'))
        tahun = int(request.form.get('tahun'))
        kilometer = int(request.form.get('kilometer'))
        transmisi = request.form.get('transmisi')
        deskripsi = request.form.get('deskripsi')

        mobil = Mobil(
            kode_mobil=kode_mobil,
            merek=merek,
            model=model,
            harga=harga,
            tahun=tahun,
            kilometer=kilometer,
            transmisi=transmisi,
            deskripsi=deskripsi,
            status='Ready',
            uploaded_by_role='admin',
            seller_id=None
        )

        db.session.add(mobil)
        db.session.commit()

        # Proses Multiple Foto
        files = request.files.getlist('gambar')
        for index, file in enumerate(files):
            if file and file.filename:
                allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if ext in allowed:
                    filename = secure_filename(file.filename)
                    new_filename = f"{kode_mobil}_{index}_{filename}"
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(upload_path)

                    foto = MobilFoto(
                        mobil_id=mobil.id,
                        nama_file=new_filename,
                        urutan=index
                    )
                    db.session.add(foto)

        db.session.commit()

        
        try:
            index_mobil(mobil)
            print(f"✅ Mobil {mobil.kode_mobil} berhasil di-index ke Elasticsearch")
        except Exception as e:
            print(f"⚠️ Gagal index ke Elasticsearch: {e}")
        

        flash('✅ Unit mobil + foto berhasil ditambahkan!', 'success')
        return redirect(url_for('main.dashboard_admin'))

    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menambahkan unit: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard_admin'))



@main_bp.route('/admin/tambah-seller', methods=['POST'])
@login_required
def tambah_seller():
    if current_user.role != 'admin':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('main.home'))

    nama = request.form.get('nama')
    email = request.form.get('email')
    whatsapp = request.form.get('whatsapp_number', '').strip()
    password = request.form.get('password')

    if User.query.filter_by(email=email).first():
        flash('Email sudah digunakan!', 'danger')
        return redirect(url_for('main.dashboard_admin'))

    if whatsapp.startswith('0'):
        whatsapp = '62' + whatsapp[1:]
    elif not whatsapp.startswith('62'):
        whatsapp = '62' + whatsapp

    seller = User(
        nama=nama,
        email=email,
        whatsapp_number=whatsapp,
        role='seller',
        status='aktif'
    )
    seller.set_password(password)

    db.session.add(seller)
    db.session.commit()

    flash('✅ Seller berhasil ditambahkan!', 'success')
    return redirect(url_for('main.dashboard_admin'))



@main_bp.route('/admin/edit-unit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_unit(id):
    if current_user.role != 'admin':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('main.home'))

    mobil = Mobil.query.get_or_404(id)

    if request.method == 'POST':
        try:
            mobil.merek = request.form.get('merek')
            mobil.model = request.form.get('model')
            mobil.harga = int(request.form.get('harga'))
            mobil.tahun = int(request.form.get('tahun'))
            mobil.kilometer = int(request.form.get('kilometer'))
            mobil.transmisi = request.form.get('transmisi')
            mobil.deskripsi = request.form.get('deskripsi')

            files = request.files.getlist('gambar')

            if files and files[0].filename != '':
                MobilFoto.query.filter_by(mobil_id=mobil.id).delete()
                for foto in mobil.fotos:
                    try:
                        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], foto.nama_file))
                    except:
                        pass

                for index, file in enumerate(files):
                    if file and file.filename:
                        allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
                        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                        if ext in allowed:
                            filename = secure_filename(file.filename)
                            new_filename = f"{mobil.kode_mobil}_{index}_{filename}"
                            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
                            file.save(upload_path)

                            foto = MobilFoto(
                                mobil_id=mobil.id,
                                nama_file=new_filename,
                                urutan=index
                            )
                            db.session.add(foto)

            db.session.commit()

            
            try:
                index_mobil(mobil)
                print(f"✅ Mobil {mobil.kode_mobil} berhasil di-update di Elasticsearch")
            except Exception as e:
                print(f"⚠️ Gagal update index Elasticsearch: {e}")
            

            flash('✅ Data mobil berhasil diperbarui!', 'success')
            return redirect(url_for('main.dashboard_admin'))

        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui data: {str(e)}', 'danger')
            return redirect(url_for('main.dashboard_admin'))

    return render_template('dashboard_admin.html', 
                           mobil_edit=mobil, 
                           mobils=Mobil.query.all(), 
                           sellers=User.query.filter_by(role='seller').all())



@main_bp.route('/admin/hapus-unit/<int:id>')
@login_required
def hapus_unit(id):
    mobil = Mobil.query.get_or_404(id)
    db.session.delete(mobil)
    db.session.commit()
    flash('✅ Mobil berhasil dihapus!', 'success')
    return redirect(url_for('main.dashboard_admin'))



@main_bp.route('/admin/edit-seller/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_seller(id):
    seller = User.query.get_or_404(id)

    if request.method == 'POST':
        seller.nama = request.form.get('nama')
        seller.email = request.form.get('email')

        whatsapp = request.form.get('whatsapp_number', '').strip()
        if whatsapp:
            if whatsapp.startswith('0'):
                whatsapp = '62' + whatsapp[1:]
            elif not whatsapp.startswith('62'):
                whatsapp = '62' + whatsapp
            seller.whatsapp_number = whatsapp

        password = request.form.get('password')
        if password and password.strip() != '':
            seller.set_password(password)

        db.session.commit()
        flash('✅ Data seller berhasil diubah!', 'success')
        return redirect(url_for('main.dashboard_admin'))

    return render_template('dashboard_admin.html', 
                           seller_edit=seller, 
                           mobils=Mobil.query.all(), 
                           sellers=User.query.filter_by(role='seller').all())



@main_bp.route('/admin/hapus-seller/<int:id>')
@login_required
def hapus_seller(id):
    seller = User.query.get_or_404(id)
    db.session.delete(seller)
    db.session.commit()
    flash('✅ Seller berhasil dihapus!', 'success')
    return redirect(url_for('main.dashboard_admin'))

def generate_kode_mobil():
    """Generate kode mobil otomatis (MB001, MB002, dst)"""
    last_mobil = Mobil.query.order_by(Mobil.id.desc()).first()
    
    if last_mobil and last_mobil.kode_mobil.startswith('MB'):
        try:
            last_number = int(last_mobil.kode_mobil.replace('MB', ''))
            new_number = last_number + 1
        except:
            new_number = 1
    else:
        new_number = 1
    
    return f"MB{new_number:03d}"   # Hasil: MB001, MB002, MB015, dst


@main_bp.route('/seller/tambah-unit', methods=['POST'])
@login_required
def tambah_unit_seller():
    if current_user.role != 'seller':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('main.home'))

    try:
        kode_mobil = generate_kode_mobil()
        merek = request.form.get('merek')
        model = request.form.get('model')
        tahun = int(request.form.get('tahun'))
        harga_raw = request.form.get('harga', '0')
        harga = int(harga_raw.replace('.', '').replace(',', '').replace('Rp', '').strip())
        kilometer = int(request.form.get('kilometer'))
        transmisi = request.form.get('transmisi')
        deskripsi = request.form.get('deskripsi')

        mobil = Mobil(
            kode_mobil=kode_mobil,
            merek=merek,
            model=model,
            tahun=tahun,
            harga=harga,
            kilometer=kilometer,
            transmisi=transmisi,
            deskripsi=deskripsi,
            status='Ready',
            uploaded_by_role='seller',
            seller_id=current_user.id
        )

        db.session.add(mobil)
        db.session.commit()

        # Proses Multiple Foto
        files = request.files.getlist('gambar')
        for index, file in enumerate(files):
            if file and file.filename:
                allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if ext in allowed:
                    filename = secure_filename(file.filename)
                    new_filename = f"{kode_mobil}_{index}_{filename}"
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
                    file.save(upload_path)

                    foto = MobilFoto(
                        mobil_id=mobil.id,
                        nama_file=new_filename,
                        urutan=index
                    )
                    db.session.add(foto)

        db.session.commit()

        
        try:
            index_mobil(mobil)
            print(f"✅ Mobil {mobil.kode_mobil} berhasil di-index ke Elasticsearch")
        except Exception as e:
            print(f"⚠️ Gagal index ke Elasticsearch: {e}")
        

        flash('✅ Unit mobil berhasil ditambahkan!', 'success')
        return redirect(url_for('main.dashboard_seller'))

    except Exception as e:
        db.session.rollback()
        print("ERROR TAMBAH UNIT SELLER:", str(e))
        flash(f'Gagal menambahkan unit: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard_seller'))



@main_bp.route('/seller/edit-unit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_unit_seller(id):
    mobil = Mobil.query.get_or_404(id)

    if mobil.seller_id != current_user.id:
        flash('Kamu tidak berhak mengedit mobil ini!', 'danger')
        return redirect(url_for('main.dashboard_seller'))

    if request.method == 'POST':
        try:
            mobil.merek = request.form.get('merek')
            mobil.model = request.form.get('model')
            mobil.harga = int(request.form.get('harga'))
            mobil.tahun = int(request.form.get('tahun'))
            mobil.kilometer = int(request.form.get('kilometer'))
            mobil.transmisi = request.form.get('transmisi')
            mobil.deskripsi = request.form.get('deskripsi')

            files = request.files.getlist('gambar')

            if files and files[0].filename != '':
                MobilFoto.query.filter_by(mobil_id=mobil.id).delete()
                for foto in mobil.fotos:
                    try:
                        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], foto.nama_file))
                    except:
                        pass

                for index, file in enumerate(files):
                    if file and file.filename:
                        allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
                        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                        if ext in allowed:
                            filename = secure_filename(file.filename)
                            nou_filename = f"{mobil.kode_mobil}_{index}_{filename}"
                            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], nou_filename)
                            file.save(upload_path)

                            foto = MobilFoto(
                                mobil_id=mobil.id,
                                nama_file=nou_filename,
                                urutan=index
                            )
                            db.session.add(foto)

            db.session.commit()

            
            try:
                index_mobil(mobil)
                print(f"✅ Mobil {mobil.kode_mobil} berhasil di-update di Elasticsearch")
            except Exception as e:
                print(f"⚠️ Gagal update index Elasticsearch: {e}")
            

            flash('✅ Data mobil berhasil diperbarui!', 'success')
            return redirect(url_for('main.dashboard_seller'))

        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui data: {str(e)}', 'danger')
            return redirect(url_for('main.dashboard_seller'))

    return render_template('dashboard_seller.html', 
                           mobil_edit=mobil, 
                           mobils=Mobil.query.filter_by(seller_id=current_user.id).all())


@main_bp.route('/seller/hapus-unit/<int:id>')
@login_required
def hapus_unit_seller(id):
    mobil = Mobil.query.get_or_404(id)

    if mobil.seller_id != current_user.id:
        flash('Kamu tidak berhak menghapus mobil ini!', 'danger')
        return redirect(url_for('main.dashboard_seller'))

    if mobil.gambar:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], mobil.gambar))
        except:
            pass

    db.session.delete(mobil)
    db.session.commit()
    flash('✅ Mobil berhasil dihapus!', 'success')
    return redirect(url_for('main.dashboard_seller'))



@main_bp.route('/ubah-status/<int:id>', methods=['POST'])
@login_required
def ubah_status(id):
    mobil = Mobil.query.get_or_404(id)

    if current_user.role == 'seller' and mobil.seller_id != current_user.id:
        flash('Kamu tidak boleh mengubah status mobil ini!', 'danger')
        return redirect(url_for('main.dashboard_seller'))

    new_status = request.form.get('status')
    if new_status in ['Ready', 'Terpanjar', 'Terjual']:
        mobil.status = new_status
        db.session.commit()
        flash(f'Status mobil berhasil diubah menjadi {new_status}', 'success')
    else:
        flash('Status tidak valid!', 'danger')

    if current_user.role == 'admin':
        return redirect(url_for('main.dashboard_admin'))
    return redirect(url_for('main.dashboard_seller'))



@main_bp.route('/admin/toggle-recommend/<int:id>', methods=['POST'])
@login_required
def toggle_recommend(id):
    if current_user.role != 'admin':
        flash("Akses ditolak!", "danger")
        return redirect(url_for('main.dashboard_admin'))

    mobil = Mobil.query.get_or_404(id)
    mobil.is_recommended = not mobil.is_recommended
    db.session.commit()

    flash(f'✅ {mobil.merek} {mobil.model} berhasil diubah status rekomendasinya.', 'success')
    return redirect(url_for('main.dashboard_admin'))



@main_bp.route('/admin/kelola-favorit', methods=['GET', 'POST'])
@login_required
def kelola_favorit():
    if current_user.role != 'admin':
        flash("Akses ditolak!", "danger")
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        selected_ids = request.form.getlist('favorite')
        Mobil.query.update({Mobil.is_favorite: False})
        db.session.commit()

        for mobil_id in selected_ids:
            mobil = Mobil.query.get(int(mobil_id))
            if mobil:
                mobil.is_favorite = True

        db.session.commit()
        flash(f"✅ {len(selected_ids)} mobil berhasil disimpan sebagai Mobil Favorit.", "success")
        return redirect(url_for('main.kelola_favorit'))

    all_mobil = Mobil.query.order_by(Mobil.id.desc()).all()
    favorite_count = Mobil.query.filter_by(is_favorite=True).count()

    return render_template('admin_kelola_favorit.html', 
                           mobil_list=all_mobil, 
                           favorite_count=favorite_count)



@main_bp.route('/admin/update-whatsapp', methods=['POST'])
@login_required
def update_whatsapp():
    if current_user.role != 'admin':
        flash("Akses ditolak!", "danger")
        return redirect(url_for('main.dashboard_admin'))

    whatsapp = request.form.get('whatsapp_number', '').strip()
    if whatsapp:
        whatsapp = ''.join(filter(str.isdigit, whatsapp))
        if whatsapp.startswith('0'):
            whatsapp = '62' + whatsapp[1:]
        elif not whatsapp.startswith('62'):
            whatsapp = '62' + whatsapp

    if whatsapp and len(whatsapp) >= 10:
        current_user.whatsapp_number = whatsapp
        db.session.commit()
        flash("✅ Nomor WhatsApp berhasil diperbarui!", "success")
    else:
        flash("Nomor WhatsApp tidak valid.", "danger")

    return redirect(url_for('main.dashboard_admin'))


if __name__ == '__main__':
    pass