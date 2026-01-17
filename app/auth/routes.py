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

        # --- ERROR WAS HERE ---
        # If user is None (invalid email) or password is wrong:
        if not user or not user.check_password(form.password.data):
            # login_user(user)  <-- REMOVE THIS LINE. You cannot login a user that doesn't exist!
            flash("Invalid email or password", "danger")
            return render_template("auth/login.html", form=form)

        # --- Check Active Status ---
        if not user.is_active:
            flash("Your account is awaiting admin approval. Please wait for confirmation.", "warning")
            return render_template("auth/login.html", form=form)

        # --- SUCCESS ---
        login_user(user)  # Only login here, after all checks pass
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

    if request.method == "POST":
        current_app.logger.debug("REGISTER POST: request.form keys = %s", list(request.form.keys()))
        current_app.logger.debug("REGISTER POST: form.data = %s", form.data)
        current_app.logger.debug("REGISTER POST: form.validate() = %s", form.validate())
        current_app.logger.debug("REGISTER POST: form.errors = %s", form.errors)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        # Check duplicate email
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        # Optional: check duplicate username
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash("Username already taken. Choose another.", "warning")
            return redirect(url_for("auth.register"))

        user = User(
            username=form.username.data.strip(),
            email=email,
            phone=form.phone.data.strip() if form.phone.data else None,
            is_admin=False,
            is_active=False  # <-- new: created as inactive / pending
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()  # user.id exists

        user.ensure_avatar()
        db.session.commit()

        # DO NOT auto-login. Instead inform user to wait for admin approval.
        flash(
            "Registration received. Your account is pending admin approval. You will receive confirmation once an administrator approves your account.",
            "info"
        )

        # Optionally send an email to admin (not implemented here)
        return redirect(url_for("auth.login"))

    # If post with errors, keep previous toasts logic
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
