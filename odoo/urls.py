from django.urls import path

from odoo import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('index/<str:dni>/', views.index_view, name='index'),
    path('claim/<str:dni>/<int:id>/', views.claim_create_view, name='claim_create'),
    path('save_claim/', views.process_claim_view, name='save_claim'),
    path('save_comment/', views.process_comment_view, name='save_comment'),
    #path('claim/(?P<dni>[^/]+)/(?P<id>[0-9]+)/save_claim\\Z', views.process_comment_view, name='save_comment'),
    path('account_move_list/<str:dni>/', views.account_move_list_view, name='account_move_list'),
]