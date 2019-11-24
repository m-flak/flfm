from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, HiddenField, BooleanField,
    FieldList, FormField, SelectField, RadioField
)
import wtforms
from wtforms.validators import (
    DataRequired, Regexp, ValidationError, EqualTo, InputRequired, Optional
)

# Make sure the 'User to share with' field isn't blank if necessary
def check_only_for_new(form, field):
    do_what = {choice[1]: choice[2] for choice in form.what_to_do.iter_choices()}
    # compare via the choice's label
    label = 'Make a New Share'
    if do_what[label]:
        if not field.data:
            raise ValidationError("You must input a user name!")

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

class RegisteredUser(wtforms.Form):
    user_name = HiddenField()
    is_enabled = BooleanField("Enabled?", false_values=(False, 'false', 0, '0'))
    is_admin = BooleanField("Administrator?", false_values=(False, 'false', 0, '0'))

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

class UpdatePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    new_password_again = PasswordField("Confirm Password",
                                       validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField()

class ManageAccountsForm(FlaskForm):
    manage_us = FieldList(FormField(RegisteredUser))
    submit = SubmitField("Commit Changes")

class MySharesForm(FlaskForm):
    what_to_do = RadioField("Task to Perform", validators=[InputRequired()],
                            choices=[('manage', "Manage Existing Shares"),
                                     ('new', "Make a New Share")])
    sharing_to = SelectField("Users I'm sharing with", validators=[Optional()],
                             coerce=int)
    stop_sharing_to = BooleanField("Stop Sharing with this user?",
                                   false_values=(False, 'false', 0, '0'))
    new_share_with = StringField("User to share with",
                                 validators=[check_only_for_new])
    submit = SubmitField()
