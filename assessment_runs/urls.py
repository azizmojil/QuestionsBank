from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='assessment_dashboard'),
    path('', views.survey_list, name='survey_list'),
    path('survey/<int:survey_id>/', views.survey_version_list, name='survey_version_list'),
    path('version/<int:version_id>/', views.survey_question_list, name='survey_question_list'),
    path('version/<int:version_id>/submit/', views.submit_assessment_run, name='submit_assessment_run'),
    path('question/<int:question_id>/', views.assessment_page, name='assessment_page'),
    path('next_question/', views.get_next_question_view, name='get_next_question'),
    path('rewind/', views.rewind_assessment, name='rewind_assessment'),
    path('complete/', views.assessment_complete, name='assessment_complete'),
]
