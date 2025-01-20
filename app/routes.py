from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from .models import db, User, List, Present, Group, Buyer, Connection
from .forms import (
    LoginForm,
    RegisterForm,
    WishlistForm,
    GiftForm,
    ContributionForm,
    ReserveForm,
)
from werkzeug.security import check_password_hash
from sqlalchemy.orm import joinedload


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
    # Make 2 seperate endpoints/elifs
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
# @ is decorator to ensure that user has logged in, how do they work!!!
@login_required
def profile():
    user_wishlists = List.query.filter_by(user_id=current_user.id).all()

    user_groups = (
        db.session.query(Group, Present, List, User)
        .join(Buyer, Buyer.group_id == Group.id)
        .join(Present, Present.group_id == Group.id)
        .join(List, List.id == Present.list_id)
        .join(User, User.id == List.user_id)
        .filter(Buyer.user_id == current_user.id)
        .all()
    )

    return render_template(
        "profile.html",
        user=current_user,
        user_groups=user_groups,
        user_wishlists=user_wishlists,
    )


@main.route("/wishlist/<int:list_id>", methods=["GET"])
@login_required
def view_wishlist_details(list_id):
    wishlist = List.query.get_or_404(list_id)
    form = GiftForm()
    gifts = Present.query.filter_by(list_id=wishlist.id).all()

    # TODO: with join! no forloops to obtain database data
    for gift in gifts:
        gift.group = Group.query.filter_by(present_id=gift.id).first()

    return render_template("wishlist.html", wishlist=wishlist, form=form, gifts=gifts)


@main.route("/wishlist/<int:list_id>/gift", methods=["POST"])
@login_required
def create_wishlist_gift(list_id):
    wishlist = List.query.get_or_404(list_id)
    form = GiftForm()

    if form.validate_on_submit():
        new_gift = Present(
            name=form.name.data, price=form.price.data, list_id=wishlist.id
        )
        db.session.add(new_gift)
        db.session.commit()
        flash("Gift added successfully!", "success")
    else:
        flash("Invalid gift form.")

    return redirect(url_for("main.view_wishlist_details", list_id=wishlist.id))


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


@main.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing_page"))


@main.route("/search_users", methods=["GET"])
@login_required
def search_users():
    query = request.args.get("query", "")
    users = (
        # we use ilike() for case insensitive SQL ILIKE
        User.query.filter(User.name.ilike(f"%{query}%"))
        .filter(User.id != current_user.id)
        .all()
    )
    return render_template("search_results.html", query=query, users=users)


@main.route("/user/<int:user_id>/wishlist/<int:list_id>", methods=["GET", "POST"])
@login_required
# Divide 2, for get and post
def view_user_wishlist_details(user_id, list_id):
    user = User.query.get_or_404(user_id)
    wishlist = List.query.get_or_404(list_id)
    presents = Present.query.filter_by(list_id=wishlist.id).all()

    reserve_form = ReserveForm()

    for present in presents:
        if present.group_id:
            present.reserved = True
        else:
            present.reserved = False

    if reserve_form.validate_on_submit():
        present_id = request.form.get("present_id")
        present = Present.query.get_or_404(present_id)

        if present.group_id:
            flash("This present has already been reserved.", "warning")
            return redirect(
                url_for(
                    "main.view_user_wishlist_details",
                    user_id=user.id,
                    list_id=wishlist.id,
                )
            )

        group = Group(present_id=present_id, group_size=1)
        db.session.add(group)
        db.session.commit()

        buyer = Buyer(
            user_id=current_user.id,
            group_id=group.id,
            contribution_amount=present.price,
        )
        db.session.add(buyer)
        db.session.commit()

        return redirect(
            url_for(
                "main.view_user_wishlist_details", user_id=user.id, list_id=wishlist.id
            )
        )

    return render_template(
        "wishlist_details.html",
        user=user,
        wishlist=wishlist,
        presents=presents,
        reserve_form=reserve_form,
    )


@main.route("/group/<int:group_id>/join", methods=["POST"])
@login_required
def join_group(group_id):
    group = Group.query.get_or_404(group_id)
    present = Present.query.get_or_404(group.present_id)

    existing_reservation = Buyer.query.filter_by(
        user_id=current_user.id, group_id=group_id
    ).first()

    if existing_reservation:
        flash("You have already reserved this present in this group.", "warning")
        return redirect(url_for("main.profile"))

    current_group_size = Buyer.query.filter_by(group_id=group_id).count()
    if current_group_size >= group.group_size:
        flash("Sorry, this group is already full.", "warning")
        return redirect(url_for("main.profile"))

    new_reservation = Buyer(
        user_id=current_user.id, group_id=group_id, contribution_amount=0.0
    )
    db.session.add(new_reservation)

    present.reserved_by_id = current_user.id
    db.session.commit()

    flash("You have successfully joined the group and reserved the present!", "success")
    return redirect(url_for("main.profile"))


@main.route("/group/<int:group_id>")
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)
    present = Present.query.get_or_404(group.present_id)

    group_members = Buyer.query.filter_by(group_id=group_id).all()

    reserved_by_user = None
    if present.reserved_by_id:
        reserved_by_user = User.query.get(present.reserved_by_id)

    return render_template(
        "group_detail.html",
        group=group,
        present=present,
        group_members=group_members,
        reserved_by_user=reserved_by_user,
    )


@main.route("/create_group/<int:present_id>", methods=["POST"])
@login_required
def create_group(present_id):
    # Get the present by ID
    present = Present.query.get_or_404(present_id)

    # Check if the present already has a group
    if present.group_id:
        flash("This present already has a group.", "warning")
        return redirect(url_for("main.view_user_wishlist", user_id=current_user.id))

    # Get the group size from the form
    group_size = request.form.get("group_size", type=int)

    # Create a new group for the present
    new_group = Group(present_id=present.id, group_size=group_size)
    db.session.add(new_group)
    db.session.commit()

    flash("Group created successfully!", "success")
    return redirect(url_for("main.view_user_wishlist", user_id=current_user.id))


@main.route("/present/<int:present_id>/reserve", methods=["POST"])
@login_required
def reserve_present(present_id):
    present = Present.query.get_or_404(present_id)

    if present.group_id:
        flash("This present has already been reserved by another user.", "warning")
        return redirect(url_for("main.profile"))

    new_group = Group(present_id=present_id, group_size=1)
    db.session.add(new_group)
    db.session.commit()

    new_buyer = Buyer(
        user_id=current_user.id,
        group_id=new_group.id,
        contribution_amount=present.price,
    )
    db.session.add(new_buyer)

    present.group_id = new_group.id
    db.session.commit()

    flash("You have successfully reserved the present and joined the group!", "success")
    return redirect(url_for("main.profile"))


@main.route("/user/<int:user_id>/wishlists", methods=["GET"])
@login_required
def view_user_wishlists(user_id):
    user = User.query.get_or_404(user_id)
    wishlists = List.query.filter_by(user_id=user_id).all()
    return render_template("user_wishlists.html", user=user, wishlists=wishlists)
