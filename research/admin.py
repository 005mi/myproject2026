from django.contrib import admin
from .models import Project # ดึงชื่อตาราง Project มา

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    # เพิ่ม 'department' ลงไปในวงเล็บนี้
    list_display = ('title_th', 'department', 'student_name', 'academic_year', 'is_approved')
    list_filter = ('department', 'academic_year', 'is_approved') # เพิ่มให้กรองตามสาขาได้ด้วย
    search_fields = ('title_th', 'student_name')