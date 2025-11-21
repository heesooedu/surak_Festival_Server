from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .extensions import db
from .models import Booth, BoothPost, Student, PointTransaction, AdminUser, apply_point_delta


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    booths = Booth.query.filter_by(is_active=True).order_by(Booth.queue_length.asc()).all()
    top_students = Student.query.order_by(Student.point_balance.desc()).limit(10).all()
    return render_template("index.html", booths=booths, top_students=top_students)


@main_bp.route("/rankings")
def ranking_board():
    return render_template("rankings.html")


@main_bp.route("/api/rankings")
def api_rankings():
    students = Student.query.order_by(Student.point_balance.desc()).limit(10).all()
    payload = [
        {
            "rank": idx + 1,
            "name": s.name,
            "student_id": f"{s.student_id[:2]}***{s.student_id[-2:]}",
            "points": s.point_balance,
        }
        for idx, s in enumerate(students)
    ]
    return jsonify(payload)


@main_bp.route("/booths")
def booth_list():
    booths = Booth.query.filter_by(is_active=True).order_by(Booth.queue_length.asc()).all()
    return render_template("booths.html", booths=booths)


@main_bp.route("/booth/<int:booth_id>")
def booth_detail(booth_id):
    booth = Booth.query.get_or_404(booth_id)
    posts = BoothPost.query.filter_by(booth_id=booth.id).order_by(BoothPost.created_at.desc()).all()
    return render_template("booth_detail.html", booth=booth, posts=posts)


@main_bp.route("/dashboard")
@login_required
def student_dashboard():
    if current_user.is_authenticated and hasattr(current_user, "role"):
        return redirect(url_for("main.admin_redirect"))
    transactions = (
        PointTransaction.query.filter_by(student_id=current_user.id)
        .order_by(PointTransaction.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("student_dashboard.html", student=current_user, transactions=transactions)


@main_bp.route("/admin")
@login_required
def admin_redirect():
    if not hasattr(current_user, "role"):
        return redirect(url_for("main.student_dashboard"))
    if current_user.is_super_admin:
        return redirect(url_for("main.super_admin_console"))
    return redirect(url_for("main.booth_admin_console"))


@main_bp.route("/admin/booth", methods=["GET", "POST"])
@login_required
def booth_admin_console():
    if not hasattr(current_user, "role") or current_user.is_super_admin:
        flash("부스 관리자만 접근 가능합니다.", "danger")
        return redirect(url_for("main.index"))
    booth = current_user.booth
    if request.method == "POST":
        action = request.form.get("action")
        if action == "increment":
            booth.queue_length += 1
        elif action == "decrement" and booth.queue_length > 0:
            booth.queue_length -= 1
        elif action == "set":
            try:
                booth.queue_length = max(0, int(request.form.get("queue_length", booth.queue_length)))
            except ValueError:
                flash("유효한 숫자를 입력하세요.", "danger")
        booth.description = request.form.get("description", booth.description)
        booth.location = request.form.get("location", booth.location)
        booth.operating_hours = request.form.get("operating_hours", booth.operating_hours)
        db.session.commit()
        flash("부스 정보가 저장되었습니다.", "success")
    posts = BoothPost.query.filter_by(booth_id=booth.id).order_by(BoothPost.created_at.desc()).all()
    return render_template("booth_admin.html", booth=booth, posts=posts)


@main_bp.route("/admin/booth/posts", methods=["POST"])
@login_required
def booth_post_editor():
    if not hasattr(current_user, "role") or current_user.is_super_admin:
        flash("부스 관리자만 접근 가능합니다.", "danger")
        return redirect(url_for("main.index"))
    booth = current_user.booth
    title = request.form.get("title")
    content = request.form.get("content")
    if title:
        post = BoothPost(booth=booth, title=title, content=content)
        db.session.add(post)
        db.session.commit()
        flash("게시물이 추가되었습니다.", "success")
    return redirect(url_for("main.booth_admin_console"))


@main_bp.route("/admin/booth/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_booth_post(post_id):
    if not hasattr(current_user, "role") or current_user.is_super_admin:
        flash("부스 관리자만 접근 가능합니다.", "danger")
        return redirect(url_for("main.index"))
    post = BoothPost.query.get_or_404(post_id)
    if post.booth_id != current_user.booth_id:
        flash("해당 부스 게시물만 삭제할 수 있습니다.", "danger")
        return redirect(url_for("main.booth_admin_console"))
    db.session.delete(post)
    db.session.commit()
    flash("게시물이 삭제되었습니다.", "info")
    return redirect(url_for("main.booth_admin_console"))


@main_bp.route("/admin/points", methods=["POST"])
@login_required
def booth_admin_points():
    if not hasattr(current_user, "role") or current_user.is_super_admin:
        flash("부스 관리자만 접근 가능합니다.", "danger")
        return redirect(url_for("main.index"))
    student_id = request.form.get("student_id")
    delta_raw = request.form.get("delta")
    reason = request.form.get("reason") or "Booth adjustment"
    student = Student.query.filter_by(student_id=student_id).first()
    try:
        delta = int(delta_raw)
    except (TypeError, ValueError):
        flash("변경값이 올바르지 않습니다.", "danger")
        return redirect(url_for("main.booth_admin_console"))
    if not student:
        flash("학생을 찾을 수 없습니다.", "danger")
        return redirect(url_for("main.booth_admin_console"))
    with db.session.begin():
        apply_point_delta(student, delta, booth=current_user.booth, admin=current_user, reason=reason)
    flash("포인트가 변경되었습니다.", "success")
    return redirect(url_for("main.booth_admin_console"))


@main_bp.route("/admin/super", methods=["GET", "POST"])
@login_required
def super_admin_console():
    if not hasattr(current_user, "role") or not current_user.is_super_admin:
        flash("슈퍼 관리자 전용 페이지입니다.", "danger")
        return redirect(url_for("main.index"))
    booths = Booth.query.order_by(Booth.created_at.desc()).all()
    admins = AdminUser.query.order_by(AdminUser.username).all()
    students = Student.query.order_by(Student.name).limit(20).all()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create_booth":
            booth = Booth(
                name=request.form.get("name"),
                description=request.form.get("description"),
                location=request.form.get("location"),
                operating_hours=request.form.get("operating_hours"),
            )
            db.session.add(booth)
            db.session.commit()
            flash("부스가 생성되었습니다.", "success")
        elif action == "create_admin":
            booth_id = request.form.get("booth_id")
            username = request.form.get("username")
            password = request.form.get("password")
            if booth_id and username and password:
                admin = AdminUser(username=username, role="booth_admin", booth_id=int(booth_id))
                admin.set_password(password)
                db.session.add(admin)
                db.session.commit()
                flash("부스 관리자가 생성되었습니다.", "success")
        elif action == "award_all":
            try:
                amount = int(request.form.get("amount", 0))
            except ValueError:
                amount = 0
            if amount != 0:
                students_all = Student.query.all()
                with db.session.begin():
                    for student in students_all:
                        apply_point_delta(student, amount, admin=current_user, reason="전체 지급")
                flash("전체 지급이 완료되었습니다.", "success")
        elif action == "award_one":
            student_id = request.form.get("student_id")
            try:
                amount = int(request.form.get("amount", 0))
            except ValueError:
                amount = 0
            student = Student.query.filter_by(student_id=student_id).first()
            if student and amount:
                with db.session.begin():
                    apply_point_delta(student, amount, admin=current_user, reason="개별 지급")
                flash("포인트가 지급되었습니다.", "success")
    return render_template(
        "super_admin.html",
        booths=booths,
        admins=admins,
        students=students,
    )


@main_bp.route("/admin/transactions")
@login_required
def transaction_log():
    if not hasattr(current_user, "role") or not current_user.is_super_admin:
        flash("슈퍼 관리자 전용 페이지입니다.", "danger")
        return redirect(url_for("main.index"))
    booth_id = request.args.get("booth_id", type=int)
    student_id = request.args.get("student_id", type=int)
    query = PointTransaction.query
    if booth_id:
        query = query.filter_by(booth_id=booth_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    transactions = query.order_by(PointTransaction.created_at.desc()).limit(200).all()
    booths = Booth.query.order_by(Booth.name).all()
    students = Student.query.order_by(Student.name).all()
    return render_template("transactions.html", transactions=transactions, booths=booths, students=students)
