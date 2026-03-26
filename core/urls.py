from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from research import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- Django Admin ---
    path('admin/', admin.site.urls),

    # --- Public ---
    path('', views.project_list, name='project_list'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),

    # --- ดาวน์โหลด PDF ---
    path('download/<int:project_id>/', views.download_pdf, name='download_pdf'),

    # --- Upload ---
    path('upload/', views.project_upload, name='project_upload'),

    # --- Auth ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # --- Password Reset (Quick - ไม่ต้องใช้ Email) ✅ ---
    path('password-reset-quick/', views.quick_password_reset, name='password_reset_quick'),

    # --- Password Reset (Email-based - เปิดเมื่อตั้ง SMTP แล้ว) ---
    # path('password_reset/', auth_views.PasswordResetView.as_view(...), name='password_reset'),
    # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(...), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(...), name='password_reset_confirm'),
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(...), name='password_reset_complete'),

    # --- Admin Dashboard ---
    path('manage/', views.admin_dashboard, name='admin_dashboard'),
    path('approve/<int:project_id>/', views.approve_project, name='approve_project'),
    path('delete/<int:project_id>/', views.delete_project, name='delete_project'),
    path('edit/<int:project_id>/', views.edit_project, name='edit_project'),
    path('export-csv/', views.export_projects_csv, name='export_projects_csv'),

     path('project/<int:project_id>/comment/', views.add_comment, name='add_comment'),

     path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)