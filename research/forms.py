from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # 1. ฟิลด์ทั้งหมด (ครบถ้วนตามหน้า Detail และ Upload)
        fields = [
            'title_th', 'title_en', 'student_name', 'researcher_co1', 'researcher_co2', 
            'department', 'academic_year', 'research_type', 'organization', 
            'background', 'objectives', 'scope', 'abstract', 'keywords', 
            'theory', 'methodology', 'results', 'discussion', 
            'suggestions_use', 'suggestions_next', 'funding_by', 'awards', 
            'other_info', 'pdf_file'
        ]
        
        # 2. ชื่อเรียกภาษาไทย
        labels = {
            'title_th': 'ชื่อผลงานวิจัย (ไทย)',
            'title_en': 'ชื่อผลงานวิจัย (อังกฤษ)',
            'student_name': 'ชื่อนักวิจัยหลัก',
            'researcher_co1': 'นักวิจัยร่วมคนที่ 1',
            'researcher_co2': 'นักวิจัยร่วมคนที่ 2',
            'department': 'สาขาวิชา/หน่วยงาน',
            'academic_year': 'ปีการศึกษา (พ.ศ.)',
            'research_type': 'ประเภทงานวิจัย',
            'organization': 'หน่วยงาน/วิทยาลัย',
            'background': 'ความเป็นมา/หลักการและเหตุผล',
            'objectives': 'วัตถุประสงค์การวิจัย',
            'scope': 'ขอบเขตการวิจัย',
            'abstract': 'บทคัดย่อ (Abstract)',
            'keywords': 'คำสำคัญ (Keywords)',
            'theory': 'ทฤษฎีที่เกี่ยวข้อง',
            'methodology': 'วิธีการดำเนินการวิจัย',
            'results': 'ผลการวิจัย',
            'discussion': 'อภิปรายผล',
            'suggestions_use': 'การนำไปใช้ประโยชน์',
            'suggestions_next': 'ข้อเสนอแนะในการวิจัยครั้งต่อไป',
            'funding_by': 'ผู้สนับสนุนทุนวิจัย',
            'awards': 'รางวัลที่เคยได้รับ/เกียรติประวัติ',
            'other_info': 'ข้อมูลเพิ่มเติมอื่นๆ',
            'pdf_file': 'ไฟล์เอกสาร PDF ฉบับเต็ม',
        }

        # 3. Widgets (เชื่อมกับ CSS .form-control)
        widgets = {
            'title_th': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'กรอกชื่อภาษาไทย'}),
            'title_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'English Title'}),
            'student_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อ-นามสกุล'}),
            'researcher_co1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อ-นามสกุล (ถ้ามี)'}),
            'researcher_co2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อ-นามสกุล (ถ้ามี)'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น AI, IoT, ร้อยเอ็ด'}),
            'academic_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'research_type': forms.Select(attrs={'class': 'form-control'}),
            'organization': forms.TextInput(attrs={'class': 'form-control'}),
            'funding_by': forms.TextInput(attrs={'class': 'form-control'}),
            
            'background': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'objectives': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'scope': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'abstract': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'theory': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'methodology': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'results': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'discussion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'suggestions_use': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'suggestions_next': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'awards': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'ระบุรางวัลหรือเกียรติประวัติที่ได้รับ'}),
            'other_info': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            
            'pdf_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }

    # 4. ตรวจสอบไฟล์ PDF
    def clean_pdf_file(self):
        file = self.cleaned_data.get('pdf_file')
        if file:
            if not file.name.lower().endswith('.pdf'):
                raise forms.ValidationError("กรุณาอัปโหลดเฉพาะไฟล์นามสกุล .pdf เท่านั้น")
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("ไฟล์มีขนาดใหญ่เกินไป (จำกัดไม่เกิน 10MB)")
        return file

    def clean(self):
        return super().clean()