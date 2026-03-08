from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # CHANGE THIS LINE:
    path('admin/', admin.site.urls),  # Not admin.site.write
    
    path('services/', include('services.urls')), 
]