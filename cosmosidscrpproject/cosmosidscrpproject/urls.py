"""
URL configuration for cosmosidscrpproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Cosmosid Scraping Data",
        default_version='v1',
        description="API documentation for viewing scraped data",
        contact=openapi.Contact(email="towsif.kuet.ac.bd@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api-auth/', include('rest_framework.urls')),  # For login/logout via DRF
    path('auth/', include('users.urls')),  # Register
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login - get tokens
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('apis/', include('apis.urls')),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),  # OpenAPI JSON format
]