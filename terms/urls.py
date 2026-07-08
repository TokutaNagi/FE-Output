from django.urls import path
from . import views

urlpatterns = [
    path("", views.top, name="top"),
    path("start/", views.start, name="start"),
    path("question/", views.question, name="question"),
    path("next/", views.next_question, name="next_question"),
    path("question/hint/", views.show_hint, name="show_hint"),
    path("result/", views.result, name="result"),
    path("retry/", views.retry, name="retry"),
    path("game_error/", views.game_error, name="game_error"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("mypage/", views.mypage, name="mypage"),
    path("logout/", views.logout_view, name="logout"),
    path("mistake-quiz/", views.mistake_quiz, name="mistake_quiz"),
]
