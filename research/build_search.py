import os, re
base_dir = r"d:\PlatformIO\Projects\RTC_BTech_AIS2026 - Color\research\templates\research"
list_path = os.path.join(base_dir, 'list.html')
search_path = os.path.join(base_dir, 'search.html')

with open(list_path, 'r', encoding='utf-8') as f:
    html = f.read()

new_hero = """<section class="hero" style="background: linear-gradient(135deg, var(--crimson-dk) 0%, #30020a 100%); padding: clamp(40px, 6vw, 60px) 5% clamp(40px, 6vw, 60px);">
    <div class="hero-deco hero-deco-1"></div>
    <div class="hero-deco hero-deco-2"></div>
    <div class="hero-inner" style="max-width: 960px;">
        <div class="hero-text" style="text-align: left;">
            <h1 class="hero-title" style="color: white; margin-bottom: 5px;"><i class="fas fa-search" style="font-size: 0.8em; margin-right: 12px; color: white;"></i><span style="background:none;-webkit-text-fill-color: white; color: white;">ค้นหาผลงานวิจัย</span></h1>
            <p class="hero-sub" style="color: rgba(255,255,255,0.7); font-size: clamp(0.95em, 2vw, 1.1em); font-weight: 400;">ค้นหาและกรองผลงานตามเงื่อนไขที่ต้องการ</p>
        </div>
    </div>
</section>"""

html = re.sub(r'<!-- ── HERO ───────────────────────────────────────────────── -->.*?</section>', '<!-- ── HERO ───────────────────────────────────────────────── -->\n' + new_hero, html, flags=re.DOTALL)
html = re.sub(r'<!-- ── STATS TILES ─────────────────────────────────────────── -->.*?<!-- ── SEARCH & FILTERS ───────────────────────────────────── -->', '<!-- ── SEARCH & FILTERS ───────────────────────────────────── -->', html, flags=re.DOTALL)
html = re.sub(r'<!-- ── RANKING ─────────────────────────────────────────────── -->.*?<!-- ── SCRIPTS ─────────────────────────────────────────────── -->', '<!-- ── SCRIPTS ─────────────────────────────────────────────── -->', html, flags=re.DOTALL)
html = html.replace('margin: 0 auto 36px', 'margin: -25px auto 36px')
html = html.replace('{% block title %}RETC Academic Portal | วิทยาลัยเทคนิคร้อยเอ็ด{% endblock %}', '{% block title %}ค้นหาผลงานวิจัย | RETC Academic Portal{% endblock %}')

with open(search_path, 'w', encoding='utf-8') as f:
    f.write(html)

with open(list_path, 'r', encoding='utf-8') as f:
    list_html = f.read()

list_html = re.sub(r'<!-- ── SEARCH & FILTERS ───────────────────────────────────── -->.*?<!-- ── PROJECT LIST ────────────────────────────────────────── -->', '<!-- ── PROJECT LIST ────────────────────────────────────────── -->', list_html, flags=re.DOTALL)
with open(list_path, 'w', encoding='utf-8') as f:
    f.write(list_html)

print("Done")
