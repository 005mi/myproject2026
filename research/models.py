from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

# 1. ฟังก์ชันสำหรับตรวจสอบขนาดไฟล์
def validate_file_size(value):
    filesize = value.size
    # กำหนดขนาดสูงสุดที่ 10MB (10 * 1024 * 1024 ไบต์)
    if filesize > 10 * 1024 * 1024:
        raise ValidationError("ขนาดไฟล์ PDF ต้องไม่เกิน 10MB")
    return value

class Project(models.Model):
    DEPARTMENTS = [
        ('EE', 'สาขาเทคโนโลยีไฟฟ้า'),
        ('ET', 'สาขาเทคโนโลยีอิเล็กทรอนิกส์'),
        ('PT', 'สาขาเทคโนโลยีการผลิต'),
        ('MT', 'สาขาเทคโนโลยีเครื่องกล'),
        ('CT', 'สาขาเทคโนโลยีคอมพิวเตอร์'),
    ]

    title_th = models.CharField(max_length=500, verbose_name="ชื่อโครงการ (ภาษาไทย)")
    
    department = models.CharField(
        max_length=2, 
        choices=DEPARTMENTS, 
        default='CT', 
        verbose_name="สาขาวิชา"
    )
    
    student_name = models.CharField(max_length=255, verbose_name="ชื่อผู้จัดทำ")
    academic_year = models.IntegerField(verbose_name="ปีการศึกษา")

    # 2. เพิ่ม validate_file_size เข้าไปใน validators
    pdf_file = models.FileField(
        upload_to='pdfs/', 
        verbose_name="ไฟล์ PDF",
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size  # เช็คขนาดไฟล์ตรงนี้
        ]
    )
    
    is_approved = models.BooleanField(default=False, verbose_name="อนุมัติการเผยแพร่")

    class Meta:
        verbose_name = "โครงงาน/ผลงานวิชาการ"
        verbose_name_plural = "โครงงาน/ผลงานวิชาการ"
        ordering = ['-academic_year']

    def __str__(self):
        return f"{self.title_th} ({self.get_department_display()})"