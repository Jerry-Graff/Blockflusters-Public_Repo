from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("tos/", views.terms_of_service, name="terms_of_service"),
    path("cookies/", views.cookies_policy, name="cookies_policy"),
    path("start-game/", views.start_game, name="start_game"),
    path("play-game/", views.play_game, name="play_game"),
    path("check-movie-answer/", views.check_answer, name="check_answer"),
    path("end-game/", views.end_game, name="end_game"),
    path("is-movie-answer-correct/", views.is_answer_correct, name="is_answer_correct"),
    path("get-movie-hint/", views.get_hint, name="get_hint"),
    path("skip-film/", views.skip_image, name="skip_image"),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]
