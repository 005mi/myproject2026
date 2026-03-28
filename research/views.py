import csv
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, F, Sum
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponse
from django.contrib.auth.models import User
from .models import Project, UserProfile, Comment
from .forms import ProjectForm


def project_list(request):
    query       = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('dept', '').strip()
    year_filter = request.GET.get('year', '').strip()

    projects_qs = Project.objects.filter(is_approved=True).order_by('-academic_year', '-id')
    if query:
        projects_qs = projects_qs.filter(
            Q(title_th__icontains=query) | Q(student_name__icontains=query)
        )
    if dept_filter:
        projects_qs = projects_qs.filter(department=dept_filter)
    if year_filter:
        projects_qs = projects_qs.filter(academic_year=year_filter)

    # ── ปีการศึกษาทั้งหมดที่มีในระบบ ─────────────────────────────────────────
    all_years = list(
        Project.objects.filter(is_approved=True)
        .values_list('academic_year', flat=True)
        .distinct()
        .order_by('-academic_year')
    )

    current_buddhist_year = date.today().year + 543
    latest_year  = all_years[0] if all_years else current_buddhist_year
    recent_years = [y for y in all_years if y >= latest_year - 3]
    older_years  = [y for y in all_years if y < latest_year - 3]

    # ── Stats ──────────────────────────────────────────────────────────────────
    top_viewed     = Project.objects.filter(is_approved=True).order_by('-views_count')[:5]
    top_downloaded = Project.objects.filter(is_approved=True).order_by('-download_count')[:5]
    total_count    = Project.objects.filter(is_approved=True).count()
    total_system_views = (
        Project.objects.filter(is_approved=True)
        .aggregate(total=Sum('views_count'))['total'] or 0
    )
    stats_by_dept = (
        Project.objects.filter(is_approved=True)
        .values('department').annotate(total=Count('id')).order_by('-total')
    )

    top_dept_name = "ยังไม่มีข้อมูล"
    if stats_by_dept.exists():
        top_dept_code = stats_by_dept.first()['department']
        top_dept_name = dict(Project.DEPARTMENTS).get(top_dept_code, top_dept_code)

    # ── Pagination 10 รายการ/หน้า ─────────────────────────────────────────────
    paginator = Paginator(projects_qs, 10)
    projects  = paginator.get_page(request.GET.get('page'))

    return render(request, 'research/list.html', {
        'projects':           projects,
        'total_count':        total_count,
        'total_system_views': total_system_views,
        'top_dept_name':      top_dept_name,
        'top_viewed':         top_viewed,
        'top_downloaded':     top_downloaded,
        'current_dept':       dept_filter,
        'current_year':       year_filter,
        'recent_years':       recent_years,
        'older_years':        older_years,
        'query':              query,
    })


# ─── Admin ────────────────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.warning(request, "เฉพาะผู้ดูแลระบบเท่านั้นที่เข้าถึงหน้านี้ได้")
        return redirect('project_list')
    pending_projects  = Project.objects.filter(is_approved=False).order_by('-id')
    approved_projects = Project.objects.filter(is_approved=True).order_by('-id')
    return render(request, 'research/admin_dashboard.html', {
        'pending_projects':  pending_projects,
        'approved_projects': approved_projects,
        'pending_count':     pending_projects.count(),
        'approved_count':    approved_projects.count(),
    })


@login_required
def export_projects_csv(request):
    if not request.user.is_staff:
        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงส่วนนี้")
        return redirect('project_list')
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="Research_Report_RTC.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'ชื่อเรื่อง (TH)', 'ผู้วิจัย', 'สาขาวิชา',
        'ปีการศึกษา', 'ยอดเข้าชม', 'ยอดดาวน์โหลด', 'สถานะ',
    ])
    for p in Project.objects.all().order_by('-academic_year'):
        writer.writerow([
            p.title_th, p.student_name, p.get_department_display(),
            p.academic_year, p.views_count, p.download_count,
            "อนุมัติแล้ว" if p.is_approved else "รอตรวจสอบ",
        ])
    return response


# ─── Project CRUD ─────────────────────────────────────────────────────────────

@login_required
def project_upload(request):
    if request.user.profile.user_type != 'student' and not request.user.is_staff:
        messages.error(request, "เฉพาะนักศึกษาเท่านั้นที่เพิ่มผลงานได้")
        return redirect('project_list')
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.student_name = request.user.username
            project.is_approved  = False
            project.save()
            messages.success(request, "ส่งผลงานสำเร็จแล้ว! กรุณารอแอดมินตรวจสอบและอนุมัติ")
            return redirect('project_list')
        else:
            messages.error(request, "กรุณาตรวจสอบข้อมูลที่กรอก มีบางช่องที่ไม่ถูกต้อง")
    else:
        form = ProjectForm()
    return render(request, 'research/upload.html', {'form': form, 'edit_mode': False})


@login_required
def approve_project(request, project_id):
    if request.user.is_staff:
        project = get_object_or_404(Project, id=project_id)
        project.is_approved = True
        project.save()
        messages.success(request, f'อนุมัติผลงาน "{project.title_th}" สำเร็จแล้ว')
    else:
        messages.error(request, "คุณไม่มีสิทธิ์อนุมัติผลงาน")
    return redirect('admin_dashboard')


@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user.is_staff or project.student_name == request.user.username:
        title = project.title_th
        project.delete()
        messages.success(request, f'ลบผลงาน "{title}" เรียบร้อยแล้ว')
    else:
        messages.error(request, "คุณไม่มีสิทธิ์ลบผลงานของผู้อื่น")
    return redirect('admin_dashboard' if request.user.is_staff else 'project_list')


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not request.user.is_staff and project.student_name != request.user.username:
        messages.error(request, "คุณไม่มีสิทธิ์แก้ไขผลงานของผู้อื่น")
        return redirect('project_list')
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'แก้ไขผลงาน "{project.title_th}" สำเร็จแล้ว')
            return redirect('project_list')
        else:
            messages.error(request, "กรุณาตรวจสอบข้อมูลที่กรอก มีบางช่องที่ไม่ถูกต้อง")
    else:
        form = ProjectForm(instance=project)
    # BUG FIX: ส่ง project ไปด้วยเพื่อแสดงชื่อในหัวฟอร์ม edit
    return render(request, 'research/edit.html', {
        'form':      form,
        'project':   project,
    })


def project_detail(request, project_id):
    # BUG FIX: ใช้ is_approved=True เพื่อกันคนพิมพ์ URL ตรงเข้าผลงานที่ยังไม่อนุมัติ
    project = get_object_or_404(Project, id=project_id, is_approved=True)
    
    # --- 🟢 ส่วนที่แก้ไข: เพิ่มระบบ Session ป้องกันการปั๊มวิว 🟢 ---
    session_key = f'viewed_project_{project.id}'
    if not request.session.get(session_key, False):
        Project.objects.filter(id=project_id).update(views_count=F('views_count') + 1)
        request.session[session_key] = True
        request.session.modified = True  # บังคับให้ Django บันทึก Session ทันที
    # -------------------------------------------------------------
        
    project.refresh_from_db()
    comments = project.comments.select_related('user').all()
    return render(request, 'research/detail.html', {
        'project':  project,
        'comments': comments,
    })

def download_pdf(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if project.pdf_file:
        Project.objects.filter(id=project_id).update(download_count=F('download_count') + 1)
        return FileResponse(project.pdf_file.open(), content_type='application/pdf')
    messages.warning(request, "ผลงานนี้ยังไม่มีไฟล์ PDF แนบ")
    return redirect('project_detail', project_id=project_id)


# ─── Auth ─────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.method == 'POST':
        u_name   = request.POST.get('username', '').strip()
        u_pass   = request.POST.get('password', '').strip()
        u_type   = request.POST.get('user_type', 'guest')
        u_email  = request.POST.get('email', '').strip()
        u_notify = request.POST.get('notify_new_project') == '1'
        u_phone  = request.POST.get('phone', '').strip()

        if not u_name or not u_pass:
            messages.error(request, "กรุณากรอกชื่อผู้ใช้และรหัสผ่านให้ครบ")
            return render(request, 'research/register.html')

        if u_type == 'guest' and not u_email:
            messages.error(request, "บุคคลภายนอกต้องกรอกอีเมลเพื่อยืนยันตัวตน")
            return render(request, 'research/register.html')

        if u_type == 'student' and (not u_name.isdigit() or len(u_name) != 11):
            messages.error(request, "รหัสนักศึกษาต้องเป็นตัวเลข 11 หลักเท่านั้น")
            return render(request, 'research/register.html')

        if u_phone and (not u_phone.isdigit() or len(u_phone) != 10):
            messages.error(request, "เบอร์โทรศัพท์ต้องเป็นตัวเลข 10 หลัก")
            return render(request, 'research/register.html')

        if User.objects.filter(username=u_name).exists():
            messages.error(request, f'ชื่อผู้ใช้ "{u_name}" มีผู้อื่นใช้งานแล้ว กรุณาเลือกชื่ออื่น')
            return render(request, 'research/register.html')

        if u_email and User.objects.filter(email=u_email).exists():
            messages.error(request, "อีเมลนี้ถูกใช้งานแล้ว กรุณาใช้อีเมลอื่น")
            return render(request, 'research/register.html')

        if len(u_pass) < 6:
            messages.error(request, "รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร")
            return render(request, 'research/register.html')

        user = User.objects.create_user(username=u_name, password=u_pass, email=u_email)
        user.profile.user_type = u_type
        user.profile.notify_new_project = u_notify
        user.profile.phone = u_phone
        if u_type == 'student':
            user.profile.student_id = u_name
        user.profile.save()

        messages.success(request, f'ลงทะเบียนสำเร็จ! ยินดีต้อนรับ "{u_name}" กรุณาเข้าสู่ระบบ')
        return redirect('login')

    return render(request, 'research/register.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                messages.success(request, f'ยินดีต้อนรับ Admin "{user.username}" เข้าสู่ระบบสำเร็จ')
            else:
                messages.success(request, f'ยินดีต้อนรับ "{user.username}" เข้าสู่ระบบสำเร็จ')
            return redirect('project_list')
        else:
            # ✅ render หน้า login ซ้ำพร้อม error=True แทนการใช้ messages
            # เพื่อให้ {% if error %} ใน template แสดง error ในหน้า login โดยตรง
            return render(request, 'research/login.html', {'form': form, 'error': True})
    else:
        form = AuthenticationForm()
    return render(request, 'research/login.html', {'form': form})


def logout_view(request):
    username = request.user.username
    logout(request)
    messages.info(request, f'"{username}" ออกจากระบบเรียบร้อยแล้ว')
    return redirect('project_list')


# ─── Comment ──────────────────────────────────────────────────────────────────

# BUG FIX: เพิ่ม @login_required — ก่อนหน้านี้ไม่มี ทำให้ AnonymousUser crash ได้
@login_required
def add_comment(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        body = request.POST.get('body', '').strip()
        if body:
            Comment.objects.create(project=project, user=request.user, body=body)
            messages.success(request, "แสดงความคิดเห็นสำเร็จ")
        else:
            messages.error(request, "กรุณากรอกข้อความก่อนส่ง")
    return redirect('project_detail', project_id=project_id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user.is_staff or comment.user == request.user:
        project_id = comment.project.id
        comment.delete()
        messages.success(request, "ลบความคิดเห็นเรียบร้อยแล้ว")
        return redirect('project_detail', project_id=project_id)
    else:
        messages.error(request, "คุณไม่มีสิทธิ์ลบความคิดเห็นนี้")
        return redirect('project_detail', project_id=comment.project.id)


# ─── Password Reset ───────────────────────────────────────────────────────────

def quick_password_reset(request):
    if request.method == 'POST':
        # BUG FIX: ก่อนหน้านี้รับแค่ 'username' และ 'email' แต่ template ส่งมาเป็น
        # 'username_student' / 'username_guest' และ 'phone' (นักศึกษา) หรือ 'email' (guest)
        user_type = request.POST.get('user_type', 'student')
        new_pass  = request.POST.get('new_password', '').strip()
        conf_pass = request.POST.get('confirm_password', '').strip()

        if user_type == 'student':
            u_name  = request.POST.get('username_student', '').strip()
            u_phone = request.POST.get('phone', '').strip()
            u_email = ''
        else:
            u_name  = request.POST.get('username_guest', '').strip()
            u_email = request.POST.get('email', '').strip()
            u_phone = ''

        if not u_name:
            messages.error(request, "กรุณากรอกชื่อผู้ใช้ / รหัสนักศึกษา")
        elif new_pass != conf_pass:
            messages.error(request, "รหัสผ่านใหม่ไม่ตรงกัน")
        elif len(new_pass) < 6:
            messages.error(request, "รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร")
        else:
            try:
                if user_type == 'student':
                    user = User.objects.get(username=u_name)
                    # ตรวจสอบเบอร์โทรที่ลงทะเบียนไว้
                    if not hasattr(user, 'profile') or user.profile.phone != u_phone:
                        raise User.DoesNotExist
                else:
                    user = User.objects.get(username=u_name, email=u_email)

                user.set_password(new_pass)
                user.save()
                messages.success(
                    request,
                    f'เปลี่ยนรหัสผ่านสำหรับ "{u_name}" สำเร็จแล้ว! กรุณาเข้าสู่ระบบใหม่'
                )
                return redirect('login')

            except User.DoesNotExist:
                messages.error(request, "ข้อมูลไม่ถูกต้อง ไม่สามารถเปลี่ยนรหัสผ่านได้")

    return render(request, 'research/password_reset.html')