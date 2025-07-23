from django.urls import path
from .views import upload_file
from . import views

urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('progress_sse/', views.progress_sse, name='progress_sse'),
    path('delete/', views.delete_file, name='delete_file'),
    path('processed_files/', views.get_processed_files, name='processed_files'),
    path('stage/', views.stage_files, name='stage_files'),
    path('stop_pixel_streaming/', views.stop_pixel_streaming, name='stop_pixel_streaming'),
    path('start_unreal_play/', views.start_unreal_play, name='start_unreal_play'),
    path('unstage_files/', views.delete_files, name='unstage_files'),
    path('check_unreal_status/', views.check_unreal_status, name='check_unreal_status'),
]