from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('secure-core-db/', admin.site.urls),
    path('', include('dashboard.urls')),
]