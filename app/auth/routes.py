# app/auth/routes.py

from urllib.parse import urlparse
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from . import auth_bp
from app.auth.forms import LoginForm, RegisterForm
from app.models import User
from app.extensions import db


def redirect_after_login(user):
    """
    Centralized redirect logic after login/register
    """
    if user.is_admin:
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("users.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect_after_login(current_user)

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password", "danger")
            return render_template("auth/login.html", form=form)

        # Check Active Status
        if not user.is_active:
            flash("Your account is awaiting admin approval. Please wait for confirmation.", "warning")
            return render_template("auth/login.html", form=form)

        # Success
        login_user(user)
        flash("Logged in successfully", "success")

        # Safe next-page redirect
        next_page = request.args.get("next")
        if next_page:
            parsed = urlparse(next_page)
            if parsed.netloc == "":
                return redirect(next_page)

        return redirect_after_login(user)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect_after_login(current_user)

    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # Check duplicate email
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        # Create user with fields matching your updated User model
        user = User(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=email,
            phone=form.phone.data.strip() if form.phone.data else None,
            is_admin=False,
            is_active=False  # created as inactive / pending
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # --- FIX: REMOVED user.ensure_avatar() call ---
        # The User model does not have this method, and it is not needed
        # for basic registration.

        flash(
            "Registration received. Your account is pending admin approval. You will receive confirmation once an administrator approves your account.",
            "info"
        )

        return redirect(url_for("auth.login"))

    # If post with errors
    if request.method == "POST" and form.errors:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("public.index"))