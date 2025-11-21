import os
from flask import Blueprint, current_app, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .extensions import db
from .models import Booth


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/booth/hero", methods=["POST"])
@login_required
def upload_hero_image():
    if not hasattr(current_user, "role") or current_user.is_super_admin:
        flash("부스 관리자만 접근 가능합니다.", "danger")
        return redirect(url_for("main.index"))
    booth: Booth = current_user.booth
    file = request.files.get("hero")
    if not file or file.filename == "":
        flash("업로드할 파일을 선택하세요.", "warning")
        return redirect(url_for("main.booth_admin_console"))
    filename = secure_filename(file.filename)
    save_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)
    file.save(filepath)
    booth.hero_image = filename
    db.session.commit()
    flash("대표 이미지가 업데이트되었습니다.", "success")
    return redirect(url_for("main.booth_admin_console"))
