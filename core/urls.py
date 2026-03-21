from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from research import views # ดึง Logic ทั้งหมดมาจากแอป research

urlpatterns = [
    # ส่วนของแอดมินระบบ Django
    path('admin/', admin.site.urls),
    
    # ส่วนของหน้าแสดงผล (Public)
    path('', views.project_list, name='project_list'),
    
    # ส่วนของนักศึกษา (Upload)
    path('upload/', views.project_upload, name='project_upload'),
    
    # ส่วนของระบบสมาชิก
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # ส่วนของการจัดการสำหรับ Admin (Dashboard/Edit/Approve/Delete)
    path('manage/', views.admin_dashboard, name='admin_dashboard'),
    path('approve/<int:project_id>/', views.approve_project, name='approve_project'),
    path('delete/<int:project_id>/', views.delete_project, name='delete_project'),
    path('edit/<int:project_id>/', views.edit_project, name='edit_project'),
]

# ตั้งค่าให้เรียกดูไฟล์ PDF ในโฟลเดอร์ media ได้ขณะพัฒนาเครื่องตัวเอง
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)