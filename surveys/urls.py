from django.urls import path

from . import views


urlpatterns = [
    path('builder/', views.survey_builder, name='survey_builder'),
    path('builder/initial/submit/', views.submit_initial_questions, name='submit_initial_questions'),
    path('builder/routing/', views.survey_builder_routing, name='survey_builder_routing'),
]
