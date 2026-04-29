import csv
import json
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, F, Sum, Avg
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.models import User
from .models import Project, Comment, Favorite, Rating
from .forms import ProjectForm
from django_ratelimit.decorators import ratelimit


# ─── Helpers ───────────────────────────────────────────────────────────────────
def get_global_stats():
    approved = Project.objects.filter(is_approved=True)
    return {
        'total_count': approved.count(),
        'total_system_views': approved.aggregate(total=Sum('views_count'))['total'] or 0,
        'total_downloads': approved.aggregate(total=Sum('download_count'))['total'] or 0,
    }

def get_user_favorite_ids(user):
    if user.is_authenticated:
        return list(Favorite.objects.filter(user=user).values_list('project_id', flat=True))
    return []

def project_list(request):
    query       = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('dept', '').strip()
    year_filter = request.GET.get('year', '').strip()

    projects_qs = Project.objects.filter(is_approved=True).select_related().prefetch_related('ratings')
    
    is_landing = not (query or dept_filter or year_filter)
    top_rated_projects = []
    latest_projects = []

    if is_landing:
        # Fetch Top Rated (highest avg score) - limited to 6
        top_rated_projects = Project.objects.filter(is_approved=True).annotate(
            avg_score=Avg('ratings__score')
        ).filter(avg_score__isnull=False).order_by('-avg_score', '-download_count', '-views_count', '-id')[:6]
        
        # Fetch 6 Latest
        latest_projects = Project.objects.filter(is_approved=True).order_by('-id')[:6]
    
    # Apply filters for search results
    if query:
        projects_qs = projects_qs.filter(
            Q(title_th__icontains=query) | Q(student_name__icontains=query)
        )
    if dept_filter:
        projects_qs = projects_qs.filter(department=dept_filter)
    if year_filter:
        projects_qs = projects_qs.filter(academic_year=year_filter)

    projects_qs = projects_qs.order_by('-academic_year', '-id')

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
    
    g_stats = get_global_stats()
    total_count = f"{g_stats['total_count']:,}"
    total_system_views = f"{g_stats['total_system_views']:,}"
    total_downloads = f"{g_stats['total_downloads']:,}"
    
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
        'top_rated_projects': top_rated_projects,
        'latest_projects':    latest_projects,
        'is_landing':         is_landing,
        'total_count':        total_count,
        'total_system_views': total_system_views,
        'total_downloads':    total_downloads,
        'top_dept_name':      top_dept_name,
        'top_viewed':         top_viewed,
        'top_downloaded':     top_downloaded,
        'current_dept':       dept_filter,
        'current_year':       year_filter,
        'recent_years':       recent_years,
        'older_years':        older_years,
        'all_years':          all_years,
        'query':              query,
        'favorited_ids':      get_user_favorite_ids(request.user),
    })


def project_search(request):
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

    # ── Pagination 21 รายการ/หน้า (3 คอลัมน์ × 7 แถว) ────────────────────────
    paginator = Paginator(projects_qs, 21)
    projects  = paginator.get_page(request.GET.get('page'))

    return render(request, 'research/search.html', {
        'projects':           projects,
        'current_dept':       dept_filter,
        'current_year':       year_filter,
        'all_years':          all_years,
        'query':              query,
        'favorited_ids':      get_user_favorite_ids(request.user),
    })


@xframe_options_exempt
def serve_pdf_preview(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not project.pdf_file:
        return HttpResponse("ไม่พบไฟล์ PDF ในระบบ", status=404)
    
    try:
        # --- 🟢 นับยอดวิวเมื่อมีการเปิดดูไฟล์ (ป้องกันการปั๊มยอดด้วย Session) 🟢 ---
        session_key = f'viewed_project_{project.id}'
        if not request.session.get(session_key, False):
            Project.objects.filter(id=project_id).update(views_count=F('views_count') + 1)
            request.session[session_key] = True
            request.session.modified = True
        # -----------------------------------------------------------------------
        
        # ✅ ใช้ Signed URL ร่วมกับเซิร์ฟเวอร์ Proxy + Bypass SSL
        if project.pdf_file.url.startswith('http'):
            import cloudinary
            import cloudinary.utils
            import urllib.request
            import ssl
            import os
            
            # 🌟 บังคับให้อ่านกุญแจใหม่จาก Environment ทุกครั้ง (เพื่อความชัวร์)
            cloudinary.config(
                cloudinary_url = os.getenv('CLOUDINARY_URL'),
                secure = True
            )
            
            # 1. สร้างลิงก์ที่มีกุญแจ (Signed URL)
            signed_url, options = cloudinary.utils.cloudinary_url(
                project.pdf_file.name, 
                sign_url=True,
                resource_type='raw'
            )
            
            # 2. ให้เซิร์ฟเวอร์เราไปดูดไฟล์มาแสดงผลเอง
            try:
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(signed_url, context=context) as response:
                    return HttpResponse(response.read(), content_type='application/pdf')
            except Exception as e:
                conf = cloudinary.config()
                env_val = os.getenv('CLOUDINARY_URL', 'NOT_FOUND')
                # ปิดบังรหัสลับเพื่อความปลอดภัย แต่โชว์ส่วนหัวและท้ายเพื่อตรวจสอบ
                masked_env = env_val[:20] + "..." + env_val[-10:] if len(env_val) > 30 else env_val
                return HttpResponse(f"ไม่สามารถดึงไฟล์ได้ (สาเหตุ: {str(e)}) | ENV: {masked_env} | Cloud: {conf.cloud_name} | URL: {signed_url}", status=404)

        response = FileResponse(project.pdf_file.open('rb'), content_type='application/pdf')
        return response
    except Exception:
        file_url = project.pdf_file.url if project.pdf_file else "No URL"
        return HttpResponse(f"ไฟล์สูญหายหรือระบบจัดเก็บขัดข้อง (Path: {file_url})", status=404)


def project_stats(request):
    all_projects = Project.objects.filter(is_approved=True)

    g_stats = get_global_stats()
    total_count = f"{g_stats['total_count']:,}"
    total_views = f"{g_stats['total_system_views']:,}"
    total_downloads = f"{g_stats['total_downloads']:,}"

    dept_stats = list(all_projects.values('department').annotate(count=Count('id')).order_by('-count'))
    
    DEPARTMENTS = dict(Project.DEPARTMENTS)
    # Simplify label strings by removing unneeded words if desired, e.g. "สาขาเทคโนโลยี" -> ""
    major_counts_data = {}
    for d in dept_stats:
        dept_name = DEPARTMENTS.get(d['department'], d['department']).replace('สาขาเทคโนโลยี', '')
        major_counts_data[dept_name] = d['count']

    # Top Dept
    top_dept_name = '-'
    top_dept_rating = '0.0'
    if dept_stats:
        top_dept_code = dept_stats[0]['department']
        top_dept_name = DEPARTMENTS.get(top_dept_code, top_dept_code).replace('สาขาเทคโนโลยี', '')
        
        # Calculate real average for the top department
        top_dept_avg = Project.objects.filter(department=top_dept_code).aggregate(Avg('ratings__score'))['ratings__score__avg']
        top_dept_rating = f"{top_dept_avg:.1f}" if top_dept_avg else "0.0"

    top_viewed = list(all_projects.order_by('-views_count')[:5].values('id', 'title_th', 'views_count'))
    top_downloaded = list(all_projects.order_by('-download_count')[:5].values('id', 'title_th', 'download_count'))

    # Replace MOCK with REAL Top Rated logic
    # We annotate projects with their average rating and order by it
    top_rated_qs = all_projects.annotate(avg_score=Avg('ratings__score')).filter(avg_score__isnull=False).order_by('-avg_score', '-download_count', '-views_count', '-id')[:5]
    top_rated = []
    for p in top_rated_qs:
        top_rated.append({
            'id': p.id,
            'title_th': p.title_th,
            'score': f"{p.avg_score:.1f}"
        })

    chart_labels = list(major_counts_data.keys())
    chart_data = list(major_counts_data.values())

    return render(request, 'research/stats.html', {
        'total_count': total_count,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'top_dept_name': top_dept_name,
        'top_dept_rating': top_dept_rating,
        'top_viewed': top_viewed,
        'top_downloaded': top_downloaded,
        'top_rated': top_rated,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data)
    })

# ─── Admin ────────────────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.warning(request, "เฉพาะผู้ดูแลระบบเท่านั้นที่เข้าถึงหน้านี้ได้")
        return redirect('project_list')
    pending_projects  = Project.objects.filter(is_approved=False).order_by('-id')
    approved_projects = Project.objects.filter(is_approved=True).order_by('-id')
    users = User.objects.select_related('profile').order_by('-date_joined')
    return render(request, 'research/admin_dashboard.html', {
        'pending_projects':  pending_projects,
        'approved_projects': approved_projects,
        'pending_count':     pending_projects.count(),
        'approved_count':    approved_projects.count(),
        'users':             users,
        'user_count':        users.count(),
    })


@login_required
def delete_user(request, user_id):
    print(f"DEBUG delete_user: method={request.method}, user_id={user_id}, request.user={request.user}")
    if not request.user.is_staff:
        messages.error(request, "ไม่มีสิทธิ์")
        return redirect('project_list')
    if request.method == 'POST':
        target = get_object_or_404(User, id=user_id)
        if target == request.user:
            messages.error(request, "ไม่สามารถลบบัญชีตัวเองได้")
        else:
            name = target.username
            target.delete()
            messages.success(request, f"ลบผู้ใช้ '{name}' เรียบร้อยแล้ว")
    return redirect('admin_dashboard')


@login_required
def toggle_user_staff(request, user_id):
    print(f"DEBUG toggle_user_staff: method={request.method}, user_id={user_id}, request.user={request.user}")
    if not request.user.is_staff:
        messages.error(request, "ไม่มีสิทธิ์")
        return redirect('project_list')
    if request.method == 'POST':
        target = get_object_or_404(User, id=user_id)
        if target == request.user:
            messages.error(request, "ไม่สามารถเปลี่ยนสิทธิ์ตัวเองได้")
        else:
            target.is_staff = not target.is_staff
            target.save()
            role = 'ผู้ดูแลระบบ' if target.is_staff else 'ผู้ใช้ทั่วไป'
            messages.success(request, f"เปลี่ยนสิทธิ์ '{target.username}' เป็น {role} เรียบร้อยแล้ว")
    return redirect('admin_dashboard')


@login_required
def reset_user_password(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "ไม่มีสิทธิ์")
        return redirect('project_list')
    if request.method == 'POST':
        target = get_object_or_404(User, id=user_id)
        new_password = request.POST.get('new_password', '').strip()
        if len(new_password) < 6:
            messages.error(request, "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")
        else:
            target.set_password(new_password)
            target.save()
            messages.success(request, f"รีเซ็ตรหัสผ่านสำหรับ '{target.username}' เรียบร้อยแล้ว")
    return redirect('admin_dashboard')


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


@login_required
def my_projects(request):
    # Show both approved and pending papers for the logged-in user
    projects_qs = Project.objects.filter(uploaded_by=request.user).order_by('-id')
    
    total_count = projects_qs.count()
    pending_count = projects_qs.filter(is_approved=False).count()
    approved_count = projects_qs.filter(is_approved=True).count()
    
    return render(request, 'research/my_list.html', {
        'projects': projects_qs,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
    })


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
            project.uploaded_by = request.user
            # ✅ ไม่ทับ student_name แล้ว เพื่อให้ผู้ใช้พิมพ์ชื่ออะไรก็ได้
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
    # 🛡️ เช็คสิทธิ์: เป็น Admin หรือเป็นคนที่อัปโหลดผลงานชิ้นนี้
    if request.user.is_staff or project.uploaded_by == request.user:
        title = project.title_th
        project.delete()
        messages.success(request, f'ลบผลงาน "{title}" เรียบร้อยแล้ว')
    else:
        messages.error(request, "คุณไม่มีสิทธิ์ลบผลงานของผู้อื่น")
    return redirect('admin_dashboard' if request.user.is_staff else 'project_list')


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # 🛡️ Admin แก้ได้ทุกอย่าง, นักศึกษาแก้ได้เฉพาะงานที่ตัวเองอัปโหลด
    if not request.user.is_staff and project.uploaded_by != request.user:
        messages.error(request, "คุณไม่มีสิทธิ์แก้ไขผลงานของผู้อื่น")
        return redirect('project_list')
        
    try:
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
    except FileNotFoundError:
        # If file is missing on Render disk, we still want to allow editing text fields
        # We manually re-initialize the form without the instance's missing file if needed,
        # but usually, simply notifying the user is better.
        messages.warning(request, "ระบบตรวจพบว่าไฟล์ PDF เดิมสูญหายจากเซิร์ฟเวอร์ (เนื่องจากการ Restart) คุณสามารถแก้ไขข้อมูลส่วนอื่นและอัปโหลดไฟล์ใหม่ได้ครับ")
        form = ProjectForm(instance=project)
        # Force pdf_file to None in the form so it doesn't try to access the missing file
        form.initial['pdf_file'] = None

    return render(request, 'research/edit.html', {
        'form':      form,
        'project':   project,
        'edit_mode': True,
    })


def project_detail(request, project_id):
    # BUG FIX: อนุญาตให้เข้าดูได้ทั้งอนุมัติแล้วและยังไม่อนุมัติ (สำหรับคนอัปโหลดตรวจความเรียบร้อย)
    # แต่ถ้าไม่อนุมัติ และไม่ใช่เจ้าของ/สตาฟ จะ redirect ออก (กันคนสุ่ม ID)
    project = get_object_or_404(Project, id=project_id)
    
    if not project.is_approved and not request.user.is_staff and project.uploaded_by != request.user:
        messages.warning(request, "ผลงานนี้อยู่ระหว่างการตรวจสอบ")
        return redirect('project_list')

    # --- 🟢 ส่วนที่แก้ไข: เพิ่มระบบ Session ป้องกันการปั๊มวิว 🟢 ---
    session_key = f'viewed_project_{project.id}'
    if not request.session.get(session_key, False):
        Project.objects.filter(id=project_id).update(views_count=F('views_count') + 1)
        request.session[session_key] = True
        request.session.modified = True
    # -------------------------------------------------------------
        
    project.refresh_from_db()
    
    # เรายังเก็บ logic เดิมไว้เผื่ออนาคตต้องการแสดงคอมเมนต์ หรือ Favorite
    comments = project.comments.select_related('user').all()
    is_favorited = False
    user_rating = 0
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, project=project).exists()
        rating_obj = Rating.objects.filter(user=request.user, project=project).first()
        if rating_obj:
            user_rating = rating_obj.score

    return render(request, 'research/detail.html', {
        'project':  project,
        'comments': comments,
        'is_favorited': is_favorited,
        'user_rating': user_rating,
    })

def download_pdf(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if project.pdf_file:
        # --- 🟢 เพิ่มระบบ Session ป้องกันการปั๊มยอดดาวน์โหลด 🟢 ---
        session_key = f'downloaded_project_{project.id}'
        if not request.session.get(session_key, False):
            Project.objects.filter(id=project_id).update(download_count=F('download_count') + 1)
            request.session[session_key] = True
            request.session.modified = True
        # -------------------------------------------------------------
        if project.pdf_file.url.startswith('http'):
            import cloudinary
            import cloudinary.utils
            import urllib.request
            import os
            
            cloudinary.config(
                cloudinary_url = os.getenv('CLOUDINARY_URL'),
                secure = True
            )
            
            signed_url, options = cloudinary.utils.cloudinary_url(
                project.pdf_file.name, 
                sign_url=True,
                resource_type='raw'
            )
            with urllib.request.urlopen(signed_url) as response:
                return HttpResponse(response.read(), content_type='application/pdf')
        return FileResponse(project.pdf_file.open(), content_type='application/pdf')
    messages.warning(request, "ผลงานนี้ยังไม่มีไฟล์ PDF แนบ")
    return redirect('project_detail', project_id=project_id)


# ─── Auth ─────────────────────────────────────────────────────────────────────

@ratelimit(key='ip', rate='5/m', block=True)
def register_view(request):
    if request.method == 'POST':
        u_name   = request.POST.get('username', '').strip()
        u_pass   = request.POST.get('password', '').strip()
        u_type   = request.POST.get('user_type', 'guest')
        u_email  = request.POST.get('email', '').strip()
        u_notify = request.POST.get('notify_new_project') == '1'
        u_phone  = request.POST.get('phone', '').strip()

        if not u_name or not u_pass or not u_email:
            messages.error(request, "กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน (ชื่อผู้ใช้, รหัสผ่าน, และอีเมล)")
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


@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        user_role_requested = request.POST.get('user_role', 'student')
        
        if form.is_valid():
            user = form.get_user()
            is_actually_staff = user.is_staff
            
            # ดึง User Type จาก Profile (ถ้ามี)
            actual_user_type = 'guest'
            if hasattr(user, 'profile'):
                actual_user_type = user.profile.user_type
            
            # --- 🛡️ การตรวจสอบสิทธิ์แบบเข้มงวด 🛡️ ---
            
            # 1. กรณีเลือก "เจ้าหน้าที่"
            if user_role_requested == 'admin' and not is_actually_staff:
                messages.error(request, "บัญชีนี้ไม่มีสิทธิ์เข้าใช้งานในฐานะเจ้าหน้าที่")
                return render(request, 'research/login.html', {'form': form, 'error': True})
            
            # 2. กรณีบัญชี Admin ไปเข้า Tab อื่น
            if user_role_requested != 'admin' and is_actually_staff:
                messages.error(request, "บัญชีเจ้าหน้าที่ กรุณาเลือกประเภท 'เจ้าหน้าที่' เพื่อเข้าสู่ระบบ")
                return render(request, 'research/login.html', {'form': form, 'error': True})
            
            # 3. กรณีเลือก "นักศึกษา" แต่เป็น "บุคคลภายนอก"
            if user_role_requested == 'student' and not is_actually_staff and actual_user_type == 'guest':
                messages.error(request, "บัญชีนี้เป็นประเภทบุคคลภายนอก กรุณาเลือกประเภท 'บุคคลภายนอก'")
                return render(request, 'research/login.html', {'form': form, 'error': True})
            
            # 4. กรณีเลือก "บุคคลภายนอก" แต่เป็น "นักศึกษา"
            if user_role_requested == 'guest' and not is_actually_staff and actual_user_type == 'student':
                messages.error(request, "บัญชีนี้เป็นประเภทนักศึกษา กรุณาเลือกประเภท 'นักศึกษา'")
                return render(request, 'research/login.html', {'form': form, 'error': True})
            
            # ----------------------------------------
            
            login(request, user)
            if user.is_staff:
                messages.success(request, f'ยินดีต้อนรับ Admin "{user.username}" เข้าสู่ระบบสำเร็จ')
            else:
                messages.success(request, f'ยินดีต้อนรับ "{user.username}" เข้าสู่ระบบสำเร็จ')
            return redirect('project_list')
        else:
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
        parent_id = request.POST.get('parent_id')
        
        if body:
            parent_comment = None
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    parent_comment = None
                    
            Comment.objects.create(
                project=project, 
                user=request.user, 
                body=body, 
                parent=parent_comment
            )
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




# ─── Favorites ✅ เพิ่มใหม่ ───────────────────────────────────────────────────

@login_required
def favorite_list(request):
    """
    Shows a list of projects that the current user has favorited with pagination and ratings info.
    """
    favorites = Favorite.objects.filter(user=request.user).select_related('project')
    project_ids = [fav.project.id for fav in favorites]
    
    # Query favorite projects — average_rating is a @property on the model
    projects_qs = Project.objects.filter(id__in=project_ids).order_by('-id')
    
    # ── PAGINATION (12 items per page = 3 columns x 4 rows) ──
    paginator = Paginator(projects_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'research/favorites.html', {
        'projects': page_obj,  # Now passing the page object
        'total_count': projects_qs.count()
    })


@login_required
def toggle_favorite(request, project_id):
    """
    Adds or removes a project from the current user's favorites.
    Can be called via POST or AJAX.
    """
    project = get_object_or_404(Project, id=project_id)
    favorite_obj = Favorite.objects.filter(user=request.user, project=project)
    
    is_favorited = False
    if favorite_obj.exists():
        favorite_obj.delete()
        is_favorited = False
        message = "นำออกจากรายการโปรดแล้ว"
    else:
        Favorite.objects.create(user=request.user, project=project)
        is_favorited = True
        message = "บันทึกในรายการโปรดแล้ว"
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return HttpResponse(json.dumps({
            'success': True,
            'is_favorited': is_favorited,
            'message': message
        }), content_type="application/json")
    
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'project_list'))


@login_required
def rate_project(request, project_id):
    """
    Handles project rating submissions (1-5 stars). If score is 0, removes the rating.
    """
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        score = request.POST.get('score')
        
        try:
            score = int(score)
            if 1 <= score <= 5:
                Rating.objects.update_or_create(
                    user=request.user,
                    project=project,
                    defaults={'score': score}
                )
                messages.success(request, f"คุณให้คะแนนผลงานนี้ {score} ดาวเรียบร้อยแล้ว")
            elif score == 0:
                Rating.objects.filter(user=request.user, project=project).delete()
                messages.success(request, "ยกเลิกการให้คะแนนเรียบร้อยแล้ว")
            else:
                messages.error(request, "คะแนนต้องอยู่ระหว่าง 1-5")
        except (ValueError, TypeError):
            messages.error(request, "ข้อมูลคะแนนไม่ถูกต้อง")
            
    return redirect('project_detail', project_id=project_id)

@login_required
def cancel_rating(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        Rating.objects.filter(user=request.user, project=project).delete()
        messages.success(request, "ยกเลิกการให้คะแนนเรียบร้อยแล้ว")
    return redirect('project_detail', project_id=project_id)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        if not email:
            messages.error(request, "จำเป็นต้องระบุอีเมลเพื่อความปลอดภัย")
        else:
            # Update User model
            request.user.email = email
            request.user.save()
            
            # Update UserProfile model
            profile = request.user.profile
            profile.phone = phone
            profile.save()
            
            messages.success(request, "อัปเดตข้อมูลส่วนตัวเรียบร้อยแล้ว")
            return redirect('project_list')
            
    return render(request, 'research/profile_edit.html')