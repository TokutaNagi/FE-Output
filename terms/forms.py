from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "answer-input"

        self.fields["username"].widget.attrs["placeholder"] = "ユーザー名"
        self.fields["password1"].widget.attrs["placeholder"] = "パスワード"
        self.fields["password2"].widget.attrs["placeholder"] = "パスワード（確認）"

        self.fields["username"].help_text = ""
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""
