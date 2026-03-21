from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # เลือกช่องให้นักศึกษากรอก
        fields = ['title_th', 'department', 'student_name', 'academic_year', 'pdf_file']
        labels = {
            'title_th': 'ชื่อเรื่อง (ไทย)',
            'department': 'สาขาวิชา',
            'student_name': 'ชื่อผู้จัดทำ',
            'academic_year': 'ปีการศึกษา (พ.ศ.)',
            'pdf_file': 'ไฟล์เอกสาร PDF',
        }


