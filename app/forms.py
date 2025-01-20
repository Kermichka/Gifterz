from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class WishlistForm(FlaskForm):
    title = StringField("Wishlist Title", validators=[DataRequired()])
    submit = SubmitField("Create Wishlist")


class GiftForm(FlaskForm):
    name = StringField("Gift Name", validators=[DataRequired()])
    price = DecimalField("Price", validators=[DataRequired()])
    submit = SubmitField("Add Gift")


class ContributionForm(FlaskForm):
    amount = DecimalField(
        "Contribution Amount", validators=[DataRequired(), NumberRange(min=0.01)]
    )
    submit = SubmitField("Contribute")


class ReserveForm(FlaskForm):
    submit = SubmitField("Reserve")
