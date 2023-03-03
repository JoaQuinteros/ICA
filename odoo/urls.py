from django.urls import path

from odoo import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('index/<str:dni>/', views.index_view, name='index'),
    path('claim/<str:dni>/<int:id>/', views.claim_create_view, name='claim_create'),
]