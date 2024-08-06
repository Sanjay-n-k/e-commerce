from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('buy-product/<int:product_id>/', views.buy_product, name='buy_product'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('order_confirmation/', views.order_confirmation, name='order_confirmation'),
    path('payment-success/', views.payment_success, name='payment_success'),
]
