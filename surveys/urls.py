from django.urls import path

from . import views


urlpatterns = [
    path('builder/', views.survey_builder, name='survey_builder'),
]
