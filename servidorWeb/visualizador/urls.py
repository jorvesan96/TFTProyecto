from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_request, name='process_request'),
    path('results/<str:palabra>/<str:fecha_inicio>/<str:fecha_fin>/', views.show_results, name='results'),
    path('word_cloud/', views.show_word_cloud_results, name='word_cloud_results'),
    path('polling_endpoint/results/', views.polling_endpoint_results, name='polling_endpoint_results'),
    path('polling_endpoint/word_cloud/', views.polling_endpoint_word_cloud, name='polling_endpoint_word_cloud'),
]
