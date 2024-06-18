from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_request, name='process_request'),
    path('results/<str:palabra>/<str:fecha_inicio>/<str:fecha_fin>/', views.show_results, name='results'),
]
