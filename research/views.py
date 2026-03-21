from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.contrib import messages
from .models import Project

# 1. หน้าแสดงรายการโครงการ (Public)
def project_list(request):
    query = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('dept', '').strip()
    
    # ดึงเฉพาะโครงการที่อนุมัติแล้วมาแสดงหน้าแรก
    projects = Project.objects.filter(is_approved=True)
    
    # สถิติสำหรับ Dashboard
    total_count = projects.count()
    stats_by_dept = projects.values('department').annotate(total=Count('id')).order_by('-total')
    
    top_dept_name = ""
    if stats_by_dept.exists():
        top_dept = stats_by_dept.first()
        # ดึงชื่อเต็มของสาขาจาก Choices ใน Model
        top_dept_name = dict(Project.DEPARTMENTS).get(top_dept['department'])

    # ระบบค้นหา
    if query:
        projects = projects.filter(
            Q(title_th__icontains=query) | Q(student_name__icontains=query)
        )
    
    # ระบบกรองสาขา
    if dept_filter:
        projects = projects.filter(department=dept_filter)
        
    context = {
        'projects': projects,
        'total_count': total_count,
        'top_dept_name': top_dept_name,
    }
    return render(request, 'research/list.html', context)


# 2. หน้าส่งผลงาน (สำหรับนักศึกษา)
@login_required(login_url='login')
def project_upload(request):
    if request.method == 'POST':
        Project.objects.create(
            title_th=request.POST.get('title_th'),
            department=request.POST.get('department'),
            student_name=request.POST.get('student_name'),
            academic_year=request.POST.get('academic_year'),
            pdf_file=request.FILES.get('pdf_file'),
            is_approved=False # รอแอดมินอนุมัติ
        )
        messages.success(request, 'ส่งผลงานสำเร็จแล้ว! กรุณารอแอดมินตรวจสอบความถูกต้อง')
        return redirect('project_list')
    
    return render(request, 'research/upload.html')


# 3. หน้าจัดการระบบ (สำหรับ Admin)
@login_required(login_url='login')
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.warning(request, "คุณไม่มีสิทธิ์เข้าถึงหน้าผู้ดูแลระบบ")
        return redirect('project_list')
    
    # แสดงเฉพาะโครงการที่ยังไม่อนุมัติ
    pending_projects = Project.objects.filter(is_approved=False).order_by('-id')
    return render(request, 'research/admin_dashboard.html', {'projects': pending_projects})


# 4. ฟังก์ชัน อนุมัติผลงาน
@login_required(login_url='login')
def approve_project(request, project_id):
    if request.user.is_superuser:
        project = get_object_or_404(Project, id=project_id)
        project.is_approved = True
        project.save()
        messages.success(request, f'อนุมัติโครงการ "{project.title_th}" เรียบร้อยแล้ว')
    return redirect('admin_dashboard')


# 5. ฟังก์ชัน แก้ไขผลงาน (NEW!)
@login_required(login_url='login')
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if not request.user.is_superuser:
        return redirect('project_list')

    if request.method == 'POST':
        project.title_th = request.POST.get('title_th')
        project.student_name = request.POST.get('student_name')
        project.academic_year = request.POST.get('academic_year')
        project.department = request.POST.get('department')
        
        # ถ้ามีการอัปโหลดไฟล์ใหม่มาทับ
        if request.FILES.get('pdf_file'):
            project.pdf_file = request.FILES.get('pdf_file')
            
        project.save()
        messages.success(request, f"แก้ไขข้อมูลโครงการ '{project.title_th}' เรียบร้อยแล้ว")
        return redirect('admin_dashboard')

    return render(request, 'research/edit.html', {'project': project})


# 6. ฟังก์ชัน ลบผลงาน
@login_required(login_url='login')
def delete_project(request, project_id):
    if request.user.is_superuser:
        project = get_object_or_404(Project, id=project_id)
        title = project.title_th
        # ลบไฟล์ในเครื่องออกด้วย (ถ้าไม่ได้ใช้ django-cleanup)
        if project.pdf_file:
            project.pdf_file.delete()
        project.delete()
        messages.success(request, f'ลบโครงการ "{title}" ออกจากระบบแล้ว')
    return redirect('admin_dashboard')


# 7. ฟังก์ชันเข้าสู่ระบบ
def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        if user is not None:
            login(request, user)
            messages.success(request, f'ยินดีต้อนรับคุณ {user.username}')
            return redirect('project_list')
        messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    return render(request, 'research/login.html')


# 8. ฟังก์ชันออกจากระบบ
def logout_view(request):
    logout(request)
    messages.info(request, 'คุณได้ออกจากระบบเรียบร้อยแล้ว')
    return redirect('project_list')


# 9. ฟังก์ชันสมัครสมาชิก
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'สมัครสมาชิกและเข้าสู่ระบบสำเร็จ')
            return redirect('project_list')
    else:
        form = UserCreationForm()
    return render(request, 'research/register.html', {'form': form})