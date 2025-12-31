from django.urls import path

from . import views


urlpatterns = [
    path('builder/', views.survey_builder, name='survey_builder'),
    path('builder/initial/submit/', views.submit_initial_questions, name='submit_initial_questions'),
    path('builder/routing/', views.survey_builder_routing, name='survey_builder_routing'),
    path('builder/routing/data/', views.survey_routing_data, name='survey_routing_data'),
    path('builder/routing/save/', views.save_survey_routing, name='survey_routing_save'),
]
