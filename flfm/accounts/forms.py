from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField
)
from wtforms.validators import DataRequired, Regexp, ValidationError, EqualTo

class NegativeRegexp(Regexp):
    def __call__(self, form, field, message=None):
        match = self.regex.match(field.data or '')
        if not match:
            return
        if message is None:
            if self.message is None:
                message = field.gettext('Invalid input.')
            else:
                message = self.message
        raise ValidationError(message)

class LoginForm(FlaskForm):
    username = StringField("User Name", validators=[DataRequired(),
                                                    NegativeRegexp(r"\\+|\/+|\*+|\?+|\"+|<+|>+|\|+|\!+")])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    username = StringField("User Name", validators=[DataRequired(),
                                                    NegativeRegexp(r"\\+|\/+|\*+|\?+|\"+|<+|>+|\|+|\!+")])
    password = PasswordField("Password", validators=[DataRequired()])
    password_again = PasswordField("Confirm Password",
                                   validators=[DataRequired(),
                                               EqualTo('password')])
    submit = SubmitField("Register")
