from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from .models import Student, AdminUser


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


auth_views = {
    "student": "auth/login_student.html",
    "admin": "auth/login_admin.html",
}


@auth_bp.route("/login/student", methods=["GET", "POST"])
def login_student():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        pin = request.form.get("pin")
        student = Student.query.filter_by(student_id=student_id).first()
        if student and student.check_pin(pin):
            login_user(student)
            flash("로그인되었습니다.", "success")
            return redirect(url_for("main.student_dashboard"))
        flash("학번 또는 PIN이 올바르지 않습니다.", "danger")
    return render_template(auth_views["student"])


@auth_bp.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = AdminUser.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            flash("관리자 로그인 성공", "success")
            return redirect(url_for("main.admin_redirect"))
        flash("로그인 정보가 올바르지 않습니다.", "danger")
    return render_template(auth_views["admin"])


@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("로그아웃 되었습니다.", "info")
    return redirect(url_for("main.index"))
