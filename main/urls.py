from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='start'),
    path('ssh', views.ssh, name='ssh'),
    path('wakeonlan/<number>/', views.wakeonlan, name='wol'),
    path('wakeall', views.wakeall, name='wolall'),
    path('toLinux/<number>/', views.toLinux, name='reboot'),
    path('send/<number>/', views.send, name='send'),
    path('calculations/<number>/<foldername>/<filename>/',
         views.calculations, name='calculations'),
    path('get/<number>/<foldername>/<filename>/', views.get, name='get'),
    path('remove/<number>/<foldername>/<filename>/', views.remove, name='remove'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
