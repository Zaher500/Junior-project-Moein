from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    # path('profile/', views.user_profile, name='user-profile'),
    # path('protected-test/', views.protected_test, name='protected-test'),
]