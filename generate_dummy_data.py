
import os
import django
import random

# ตั้งค่าเพื่อให้เรียกใช้ Django models ได้
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from research.models import Project

def generate_dummy():
    departments = [
        ('EE', 'สาขาเทคโนโลยีไฟฟ้า'),
        ('ET', 'สาขาเทคโนโลยีอิเล็กทรอนิกส์'),
        ('PT', 'สาขาเทคโนโลยีการผลิต'),
        ('MT', 'สาขาเทคโนโลยีเครื่องกล'),
        ('CT', 'สาขาเทคโนโลยีคอมพิวเตอร์'),
    ]

    research_types = ['classroom', 'r_d', 'innovation', 'survey']
    
    first_names = ["สมชาย", "วิชัย", "มานะ", "ปิติ", "ชูใจ", "วีระ", "ดวงพร", "ศิริพร", "เกรียงไกร", "นเรศ", "พรชัย", "สุรพล"]
    last_names = ["ใจดี", "รักชาติ", "มั่งคั่ง", "รุ่งเรือง", "สืบสาย", "พานิช", "พงษ์พิพัฒน์", "เจริญพร", "เลิศวิจิตร"]

    topics = {
        'EE': ["ระบบควบคุมมอเตอร์", "การจัดการพลังงานแสงอาทิตย์", "เครื่องตรวจจับกระแสไฟฟ้า", "การปรับปรุงหม้อแปลง", "ระบบเตือนภัยไฟฟ้าลัดวงจร"],
        'ET': ["วงจรขยายสัญญาณ", "เครื่องวัดอุณหภูมิไร้สาย", "แขนกลควบคุมด้วย Arduino", "ระบบ IOT ในบ้าน", "การวิเคราะห์สัญญาณดิจิทัล"],
        'PT': ["การลดขั้นตอนการผลิต", "สายพานลำเลียงอัตโนมัติ", "การซ่อมบำรุงเครื่องจักรเชิงป้องกัน", "การวิเคราะห์ต้นทุนการผลิต", "เทคนิคการเชื่อมโลหะ"],
        'MT': ["การออกแบบชิ้นส่วนเครื่องยนต์", "ระบบไฮดรอลิกประหยัดพลังงาน", "เครื่องตัดหญ้าควบคุมระยะไกล", "การทดสอบความแข็งแรงวัสดุ", "เครื่องอัดขยะรีไซเคิล"],
        'CT': ["แอพพลิเคชันจัดการคลังสินค้า", "ระบบจดจำใบหน้า", "เครือข่ายความปลอดภัยไร้สาย", "เว็บไซต์ฐานข้อมูลวิจัย", "การพัฒนาเกมเพื่อการเรียนรู้"]
    }

    count_per_dept = 21
    total_created = 0

    print(f"เริ่มสร้างข้อมูลจำลอง สาขาละ {count_per_dept} ผลงาน...")

    for dept_code, dept_name in departments:
        for i in range(1, count_per_dept + 1):
            title_base = random.choice(topics[dept_code])
            title_th = f"สมมุติ: {title_base} รุ่นที่ {i} สำหรับ{dept_name}"
            title_en = f"Suppose: {title_base} Vol.{i} for {dept_code} Department"
            
            student = f"{random.choice(first_names)} {random.choice(last_names)}"
            co1 = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            year = random.randint(2565, 2569)
            res_type = random.choice(research_types)
            
            abstract_text = (
                f"สมมุติ.... งานวิจัยเรื่อง {title_th} นี้มีวัตถุประสงค์เพื่อศึกษาและพัฒนา{title_base} "
                f"ให้มีประสิทธิภาพสูงขึ้น โดยใช้เทคโนโลยีสมัยใหม่มาประยุกต์ใช้ ผลการศึกษาพบว่าระบบสามารถทำงานได้ "
                f"อย่างแม่นยำและช่วยลดระยะเวลาในการทำงานลงได้มากกว่า 20% เมื่อเทียบกับวิธีการแบบเดิม"
            )

            Project.objects.create(
                title_th=title_th,
                title_en=title_en,
                department=dept_code,
                academic_year=year,
                research_type=res_type,
                student_name=student,
                researcher_co1=co1,
                abstract=abstract_text,
                background=f"สมมุติ.... เนื่องด้วยปัจจุบันเทคโนโลยีด้าน {dept_name} มีการพัฒนาอย่างต่อเนื่อง...",
                objectives=f"สมมุติ.... 1. เพื่อพัฒนา{title_base} 2. เพื่อทดสอบประสิทธิภาพการทำงาน",
                methodology=f"สมมุติ.... การวิจัยนี้ใช้วิธีการออกแบบเชิงวิศวกรรมและทดสอบในสภาวะจำลอง...",
                results=f"สมมุติ.... ระบบที่พัฒนาขึ้นสามารถตอบสนองความต้องการของผู้ใช้งานได้เป็นอย่างดี",
                is_approved=True,
                views_count=random.randint(10, 500)
            )
            total_created += 1
            
        print(f"  - สร้างข้อมูลสาขา {dept_name} เสร็จสิ้น ({count_per_dept} รายการ)")

    print(f"เสร็จสมบูรณ์! สร้างข้อมูลทั้งหมด {total_created} รายการ")

if __name__ == "__main__":
    generate_dummy()
