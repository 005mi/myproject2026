from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


# ─── User Profile ──────────────────────────────────────────────────────────────
class UserProfile(models.Model):
    USER_TYPES = [
        ('student', 'นักศึกษา'),
        ('guest', 'บุคคลภายนอก'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='guest')
    student_id = models.CharField(max_length=11, blank=True, null=True, verbose_name="รหัสนักศึกษา")
    phone = models.CharField(max_length=10, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")  # ✅ เพิ่มใหม่
    email_verified = models.BooleanField(default=False, verbose_name="ยืนยันอีเมลแล้ว")
    notify_new_project = models.BooleanField(default=False, verbose_name="แจ้งเตือนผลงานใหม่")

    class Meta:
        verbose_name = "โปรไฟล์ผู้ใช้งาน"
        verbose_name_plural = "โปรไฟล์ผู้ใช้งาน"

    def __str__(self):
        return f"{self.user.username} ({self.get_user_type_display()})"


# ─── ฟังก์ชันตรวจสอบขนาดไฟล์ (ไม่เกิน 10MB) ────────────────────────────────
def validate_file_size(value):
    filesize = value.size
    if filesize > 10 * 1024 * 1024:
        raise ValidationError("ขนาดไฟล์ PDF ต้องไม่เกิน 10MB")
    return value


# ─── Project ───────────────────────────────────────────────────────────────────
class Project(models.Model):
    DEPARTMENTS = [
        ('EE', 'สาขาเทคโนโลยีไฟฟ้า'),
        ('ET', 'สาขาเทคโนโลยีอิเล็กทรอนิกส์'),
        ('PT', 'สาขาเทคโนโลยีการผลิต'),
        ('MT', 'สาขาเทคโนโลยีเครื่องกล'),
        ('CT', 'สาขาเทคโนโลยีคอมพิวเตอร์'),
    ]

    RESEARCH_TYPES = [
        ('classroom', 'วิจัยในชั้นเรียน'),
        ('r_d', 'วิจัยและพัฒนา (R&D)'),
        ('innovation', 'นวัตกรรมและสิ่งประดิษฐ์'),
        ('survey', 'วิจัยเชิงสำรวจ'),
        ('other', 'อื่นๆ'),
    ]

    # --- ส่วนที่ 1: ข้อมูลพื้นฐาน ---
    title_th = models.CharField(max_length=500, verbose_name="ชื่อผลงานวิจัย (ภาษาไทย)")
    title_en = models.CharField(max_length=500, verbose_name="ชื่อผลงานวิจัย (ภาษาอังกฤษ)", blank=True, null=True)
    department = models.CharField(max_length=2, choices=DEPARTMENTS, default='CT', verbose_name="สาขาวิชา")
    academic_year = models.IntegerField(verbose_name="ปีที่ผลงานวิจัยเสร็จ (พ.ศ.)")
    research_type = models.CharField(max_length=50, choices=RESEARCH_TYPES, default='innovation', verbose_name="ประเภทของงานวิจัย")

    # --- ส่วนที่ 2: ทีมผู้วิจัยและหน่วยงาน ---
    student_name = models.CharField(max_length=255, verbose_name="ชื่อนักวิจัยหลัก")
    researcher_co1 = models.CharField(max_length=255, verbose_name="ชื่อนักวิจัยร่วมคนที่ 1", blank=True, null=True)
    researcher_co2 = models.CharField(max_length=255, verbose_name="ชื่อนักวิจัยร่วมคนที่ 2", blank=True, null=True)
    organization = models.CharField(max_length=255, verbose_name="หน่วยงาน", default="วิทยาลัยเทคนิคร้อยเอ็ด")
    funding_by = models.CharField(max_length=255, verbose_name="ผู้สนับสนุนทุนวิจัย", blank=True, null=True)
    awards = models.TextField(verbose_name="รางวัลที่เคยได้รับ", blank=True, null=True)

    # --- ส่วนที่ 3: เนื้อหาทางวิชาการ ---
    abstract = models.TextField(verbose_name="บทคัดย่อ", blank=True)
    keywords = models.CharField(max_length=255, verbose_name="คำสำคัญ (Keywords)", blank=True)
    background = models.TextField(verbose_name="ความเป็นมา/หลักการและเหตุผล", blank=True)
    objectives = models.TextField(verbose_name="วัตถุประสงค์การวิจัย", blank=True)
    scope = models.TextField(verbose_name="ขอบเขตของการวิจัย", blank=True)
    theory = models.TextField(verbose_name="ทฤษฎีที่ใช้ในการศึกษา/ที่เกี่ยวข้อง", blank=True)
    methodology = models.TextField(verbose_name="วิธีการวิจัย", blank=True)
    results = models.TextField(verbose_name="ผลการวิจัย", blank=True)
    discussion = models.TextField(verbose_name="อภิปรายผล", blank=True)
    suggestions_use = models.TextField(verbose_name="ข้อเสนอแนะในการใช้ประโยชน์", blank=True)
    suggestions_next = models.TextField(verbose_name="ข้อเสนอแนะในการทำวิจัยครั้งต่อไป", blank=True)
    other_info = models.TextField(verbose_name="อื่นๆ", blank=True, null=True)

    # --- ส่วนที่ 4: ไฟล์และการอนุมัติ ---
    pdf_file = models.FileField(
        upload_to='pdfs/',
        verbose_name="ไฟล์ PDF ฉบับเต็ม",
        validators=[FileExtensionValidator(allowed_extensions=['pdf']), validate_file_size],
        null=True, blank=True
    )
    is_approved = models.BooleanField(default=False, verbose_name="อนุมัติการเผยแพร่")
    views_count = models.PositiveIntegerField(default=0, verbose_name="ยอดเข้าชม")
    download_count = models.PositiveIntegerField(default=0, verbose_name="ยอดดาวน์โหลด")

    class Meta:
        verbose_name = "โครงงาน/ผลงานวิชาการ"
        verbose_name_plural = "โครงงาน/ผลงานวิชาการ"
        ordering = ['-academic_year']

    def __str__(self):
        return f"{self.title_th} ({self.get_department_display()})"


# ─── Comment ✅ เพิ่มใหม่ ──────────────────────────────────────────────────────
class Comment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(verbose_name="ความคิดเห็น")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "ความคิดเห็น"
        verbose_name_plural = "ความคิดเห็น"

    def __str__(self):
        return f"{self.user.username} on {self.project.title_th[:30]}"