import csv
from flask.cli import with_appcontext
import click
from .extensions import db
from .models import Student, AdminUser, Booth


def register_cli(app):
    @app.cli.command("load-students")
    @click.argument("csv_path")
    @with_appcontext
    def load_students(csv_path):
        """CSV 파일에서 학생 정보를 불러옵니다."""
        created = 0
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if not row.get("student_id") or not row.get("pin"):
                    continue
                student = Student(student_id=row["student_id"], name=row.get("name", ""))
                student.set_pin(row["pin"])
                db.session.add(student)
                created += 1
        db.session.commit()
        click.echo(f"{created} students imported")

    @app.cli.command("create-super-admin")
    @click.argument("username")
    @click.argument("password")
    @with_appcontext
    def create_super_admin(username, password):
        admin = AdminUser(username=username, role="super_admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo("Super admin created")

    @app.cli.command("create-booth")
    @click.argument("name")
    @with_appcontext
    def create_booth(name):
        booth = Booth(name=name, description="")
        db.session.add(booth)
        db.session.commit()
        click.echo(f"Booth '{name}' created")
