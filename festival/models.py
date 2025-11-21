import datetime as dt
from typing import Optional
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)


class Student(UserMixin, db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    pin_hash = db.Column(db.String(255), nullable=False)
    point_balance = db.Column(db.Integer, default=0, nullable=False)
    transactions = db.relationship("PointTransaction", back_populates="student", lazy="dynamic")

    def set_pin(self, pin: str):
        self.pin_hash = generate_password_hash(pin)

    def check_pin(self, pin: str) -> bool:
        return check_password_hash(self.pin_hash, pin)

    def get_id(self):
        return f"student:{self.id}"


class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="booth_admin")
    booth_id = db.Column(db.Integer, db.ForeignKey("booths.id"), nullable=True)

    booth = db.relationship("Booth", back_populates="admins")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"admin:{self.id}"

    @property
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"


class Booth(TimestampMixin, db.Model):
    __tablename__ = "booths"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    operating_hours = db.Column(db.String(120), nullable=True)
    queue_length = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    hero_image = db.Column(db.String(255), nullable=True)

    posts = db.relationship("BoothPost", back_populates="booth", cascade="all, delete-orphan")
    admins = db.relationship("AdminUser", back_populates="booth")
    transactions = db.relationship("PointTransaction", back_populates="booth")


class BoothPost(TimestampMixin, db.Model):
    __tablename__ = "booth_posts"

    id = db.Column(db.Integer, primary_key=True)
    booth_id = db.Column(db.Integer, db.ForeignKey("booths.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=True)

    booth = db.relationship("Booth", back_populates="posts")


class PointTransaction(TimestampMixin, db.Model):
    __tablename__ = "point_transactions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    booth_id = db.Column(db.Integer, db.ForeignKey("booths.id"), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=True)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True)

    student = db.relationship("Student", back_populates="transactions")
    booth = db.relationship("Booth", back_populates="transactions")
    admin = db.relationship("AdminUser")

    @property
    def direction(self) -> str:
        return "credit" if self.amount >= 0 else "debit"


def apply_point_delta(student: Student, amount: int, *, booth: Optional[Booth] = None, admin: Optional[AdminUser] = None, reason: str = None):
    if amount == 0:
        return
    student.point_balance = student.point_balance + amount
    transaction = PointTransaction(student=student, booth=booth, admin=admin, amount=amount, reason=reason)
    db.session.add(transaction)
