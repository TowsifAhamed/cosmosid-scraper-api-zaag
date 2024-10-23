from django.urls import path
from .views import UserRegistrationView, CustomLoginView, LogoutView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),  # Logout view
    path('logout/', LogoutView.as_view(), name='logout'),  # Logout view
]
