from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from .models import db, User, List, Present, Group, Buyer, Connection
from .forms import LoginForm, RegisterForm, WishlistForm, GiftForm, ContributionForm
from werkzeug.security import check_password_hash

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def landing_page():
    login_form = LoginForm()
    register_form = RegisterForm()

    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("main.profile"))
        else:
            flash("Invalid email or password.", "danger")

    if register_form.validate_on_submit():
        existing_user = User.query.filter_by(email=register_form.email.data).first()
        if existing_user:
            flash("Email is already in use. Please log in.", "warning")
            return redirect(url_for("main.landing_page"))

        new_user = User(
            name=register_form.name.data,
            email=register_form.email.data,
        )
        new_user.password = register_form.password.data
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Registration successful!", "success")
        return redirect(url_for("main.profile"))

    return render_template(
        "landing.html", login_form=login_form, register_form=register_form
    )


@main.route("/profile")
@login_required
def profile():
    user_lists = List.query.filter_by(user_id=current_user.id).all()
    return render_template("profile.html", user=current_user, lists=user_lists)


@main.route("/wishlist/<int:list_id>")
@login_required
def view_wishlist(list_id):
    wishlist = Present.query.filter_by(list_id=list_id).all()
    return render_template("wishlist.html", wishlist=wishlist)


@main.route("/create_wishlist", methods=["GET", "POST"])
@login_required
def create_wishlist():
    form = WishlistForm()
    if form.validate_on_submit():
        existing_list = List.query.filter_by(
            title=form.title.data, user_id=current_user.id
        ).first()
        if existing_list:
            flash("You already have a wishlist with this title.", "warning")
            return redirect(url_for("main.profile"))

        new_list = List(title=form.title.data, user_id=current_user.id)
        db.session.add(new_list)
        db.session.commit()
        flash("Wishlist created successfully!", "success")
        return redirect(url_for("main.profile"))
    return render_template("create_wishlist.html", form=form)


@main.route("/wishlist/<int:list_id>/add_gift", methods=["GET", "POST"])
@login_required
def add_gift(list_id):
    form = GiftForm()
    if form.validate_on_submit():
        new_gift = Present(name=form.name.data, price=form.price.data, list_id=list_id)
        db.session.add(new_gift)
        db.session.commit()
        flash("Gift added successfully!", "success")
        return redirect(url_for("main.view_wishlist", list_id=list_id))
    return render_template("add_gift.html", form=form, list_id=list_id)


@main.route("/group/<int:group_id>/contribute", methods=["GET", "POST"])
@login_required
def contribute_to_group(group_id):
    form = ContributionForm()
    group = Group.query.get_or_404(group_id)
    if form.validate_on_submit():
        contribution = Buyer(
            user_id=current_user.id,
            group_id=group_id,
            contribution_amount=form.amount.data,
        )
        db.session.add(contribution)
        db.session.commit()
        flash("Contribution added successfully!", "success")
        return redirect(url_for("main.profile"))
    return render_template("contribute.html", form=form, group=group)
