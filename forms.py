from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SubmitField,
    SelectField,
    BooleanField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class RegisterForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=64)])
    confirm_password = PasswordField(
        "Repeat password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class JobForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=160)])
    short_description = StringField("Short description", validators=[DataRequired(), Length(min=10, max=300)])
    full_description = TextAreaField("Full description", validators=[DataRequired(), Length(min=30)])
    company_name = StringField("Company", validators=[DataRequired(), Length(min=2, max=160)])
    salary = StringField("Salary", validators=[Optional(), Length(max=80)])
    location = StringField("Location", validators=[DataRequired(), Length(min=2, max=120)])

    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Save job")


class ProfileForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])

    photo = FileField(
        "Photo",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png"], "Only JPG/PNG allowed"),
            FileSize(max_size=10 * 1024 * 1024, message="Max 10MB"),
        ],
    )
    submit = SubmitField("Save changes")


class DeleteForm(FlaskForm):
    submit = SubmitField("Delete")

