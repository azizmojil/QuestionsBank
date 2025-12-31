from django.urls import path
from . import views

urlpatterns = [
    path('linguistic-review/', views.linguistic_review, name='linguistic_review'),
    path('linguistic-review/update/', views.update_staged_question, name='update_staged_question'),
    path('linguistic-review/send-translation/', views.send_to_translation, name='send_to_translation'),
    path('translation-queue/', views.translation_queue, name='translation_queue'),
    path('translation-queue/save/', views.save_translation, name='save_translation'),
]
