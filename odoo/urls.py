from django.urls import path

from odoo import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/recovery", views.login_recovery_view, name="login_recovery"),
    path("index/<str:dni>/<str:internal_code>/", views.index_view, name="index"),
    path(
        "claim/<str:dni>/<int:contract_id>/",
        views.claim_create_view,
        name="claim_create",
    ),
    path("save_claim/", views.claim_create_view, name="save_claim"),
    path("save_comment/", views.claim_create_view, name="save_comment"),
    # path('claim/(?P<dni>[^/]+)/(?P<id>[0-9]+)/save_claim\\Z', views.process_comment_view, name='save_comment'),
    path(
        "account_movements_list/<str:dni>/",
        views.account_movements_list_view,
        name="account_movements_list",
    ),
]
