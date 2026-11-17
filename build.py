# -*- coding: utf-8 -*-
"""Build sharpstory.studio from the content/ folder.

Everything editable lives in content/ (edited through /admin). This script turns it
into static pages in dist/. It uses only the Python standard library, so it runs on
Netlify with no install step:  python3 build.py
"""
import datetime, glob, html, json, os, re, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'dist')
C = lambda *p: os.path.join(ROOT, 'content', *p)


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def slug_of(path):
    return os.path.splitext(os.path.basename(path))[0]


S = load(C('settings.json'))
HOME, WORK, ABOUT, JOURNAL, CONTACT, SERVICES, BOOK = (load(C(n + '.json')) for n in ('home', 'work', 'about', 'journal', 'contact', 'services', 'book'))
BRAND = load(os.path.join(ROOT, 'src', 'brand.json'))
DOMAIN = S['domain'].rstrip('/')
EMAIL = S['email'].strip()

PROJECTS = []
for f in glob.glob(C('projects', '*.json')):
    p = load(f)
    if p.get('draft'):
        continue
    p['slug'] = slug_of(f)
    PROJECTS.append(p)
PROJECTS.sort(key=lambda p: (bool(p.get('concept')), p.get('order', 999), p['title'].lower()))

ARTICLES = []
for f in glob.glob(C('articles', '*.json')):
    a = load(f)
    if a.get('draft'):
        continue
    a['slug'] = slug_of(f)
    ARTICLES.append(a)
ARTICLES.sort(key=lambda a: str(a.get('date', '')), reverse=True)
_feat = next((a for a in ARTICLES if a.get('featured')), ARTICLES[0] if ARTICLES else None)
if _feat:
    ARTICLES.remove(_feat)
    ARTICLES.insert(0, _feat)


# ---------- helpers ----------
def t(x):
    """Escape plain text for HTML."""
    return html.escape(str(x or ''), quote=False)


def at(x):
    """Escape text for an attribute."""
    return html.escape(str(x or ''), quote=True)


def br(x):
    return '<br>'.join(t(l) for l in str(x or '').split('\n') if l.strip())


def lines(x):
    return ''.join('<span class="ln"><span>%s</span></span>' % t(l) for l in str(x or '').split('\n') if l.strip())


def img(x):
    """Normalise an image path from the editor to a site path."""
    x = str(x or '').strip()
    if not x:
        return ''
    if x.startswith(('http://', 'https://', '/')):
        return x
    return '/' + x.lstrip('./')


def img_size(src):
    """Width and height of a local image (WebP, PNG or JPEG), read with the standard library."""
    f = os.path.join(ROOT, 'static', img(src).lstrip('/')) if img(src).startswith('/') else ''
    if not f or not os.path.isfile(f):
        return None
    try:
        with open(f, 'rb') as fh:
            d = fh.read(65536)
        if d[:4] == b'RIFF' and d[8:12] == b'WEBP':
            c = d[12:16]
            if c == b'VP8X':
                return (1 + int.from_bytes(d[24:27], 'little'), 1 + int.from_bytes(d[27:30], 'little'))
            if c == b'VP8 ':
                return (int.from_bytes(d[26:28], 'little') & 0x3fff, int.from_bytes(d[28:30], 'little') & 0x3fff)
            if c == b'VP8L':
                b = int.from_bytes(d[21:25], 'little')
                return (1 + (b & 0x3fff), 1 + ((b >> 14) & 0x3fff))
        if d[:8] == b'\x89PNG\r\n\x1a\n':
            return (int.from_bytes(d[16:20], 'big'), int.from_bytes(d[20:24], 'big'))
        if d[:2] == b'\xff\xd8':
            i = 2
            while i < len(d) - 9:
                if d[i] != 0xFF:
                    i += 1
                    continue
                m = d[i + 1]
                if m in (0xC0, 0xC1, 0xC2):
                    return (int.from_bytes(d[i + 7:i + 9], 'big'), int.from_bytes(d[i + 5:i + 7], 'big'))
                i += 2 + int.from_bytes(d[i + 2:i + 4], 'big')
    except Exception:
        return None
    return None


def img_tag(src, alt, cls='', sizes='100vw'):
    """An <img> with its real size, lazy loading and a phone-sized version when one exists."""
    u = img(src)
    a = ' class="%s"' % cls if cls else ''
    wh = img_size(src)
    if wh:
        a += ' width="%d" height="%d"' % wh
        m = re.sub(r'\.(webp|jpe?g|png)$', r'-m.\1', u)
        mw = img_size(m) if m != u else None
        if mw and mw[0] < wh[0]:
            a += ' srcset="%s %dw, %s %dw" sizes="%s"' % (at(m), mw[0], at(u), wh[0], sizes)
    return '<img src="%s" alt="%s" loading="lazy" decoding="async"%s>' % (at(u), at(alt), a)


def url_css(x):
    return 'url(%s)' % img(x).replace(' ', '%20').replace('(', '%28').replace(')', '%29')


TAG = {'Brand strategy': 'strategy', 'Branding': 'branding', 'Packaging design': 'packaging'}


def tags(p):
    return ' '.join(TAG[s] for s in p.get('services', []) if s in TAG)


def num(i):
    return '%02d' % (i + 1)


def inline_md(x):
    x = t(x)
    x = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)', lambda m: '<img src="%s" alt="%s" loading="lazy">' % (at(img(m.group(2))), m.group(1)), x)
    x = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: '<a href="%s"%s>%s</a>' % (
        m.group(2).replace('"', '%22'), '' if m.group(2).startswith('/') else ' target="_blank" rel="noopener"', m.group(1)), x)
    x = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', x)
    x = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', x)
    x = re.sub(r'(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])', r'<em>\1</em>', x)
    return x


def markdown(md):
    """Small Markdown renderer for journal articles: paragraphs, headings, lists,
    quotes, images, links, bold and italics."""
    out = []
    for block in re.split(r'\n\s*\n', str(md or '').replace('\r\n', '\n').strip()):
        b = block.strip()
        if not b:
            continue
        ls = b.split('\n')
        m = re.match(r'^(#{1,4})\s+(.*)$', b)
        if m and len(ls) == 1:
            lvl = 2 if len(m.group(1)) <= 2 else 3
            out.append('<h%d class="fu">%s</h%d>' % (lvl, inline_md(m.group(2)), lvl))
        elif all(re.match(r'^\s*[-*+]\s+', l) for l in ls):
            out.append('<ul class="fu">%s</ul>' % ''.join('<li>%s</li>' % inline_md(re.sub(r'^\s*[-*+]\s+', '', l)) for l in ls))
        elif all(re.match(r'^\s*\d+[.)]\s+', l) for l in ls):
            out.append('<ol class="fu">%s</ol>' % ''.join('<li>%s</li>' % inline_md(re.sub(r'^\s*\d+[.)]\s+', '', l)) for l in ls))
        elif all(l.startswith('>') for l in ls):
            out.append('<blockquote class="fu">%s</blockquote>' % inline_md(' '.join(l.lstrip('> ').strip() for l in ls)))
        elif re.match(r'^!\[[^\]]*\]\([^)]+\)$', b):
            m = re.match(r'^!\[([^\]]*)\]\(([^)\s]+)\)$', b)
            cap = '<figcaption>%s</figcaption>' % t(m.group(1)) if m.group(1) else ''
            out.append('<figure class="fu"><img src="%s" alt="%s" loading="lazy">%s</figure>' % (at(img(m.group(2))), at(m.group(1)), cap))
        else:
            out.append('<p class="fu">%s</p>' % '<br>'.join(inline_md(l) for l in ls))
    return ''.join(out)


SOCIALS = [(lab, S.get(k, '').strip()) for k, lab in (('instagram', 'Instagram'), ('linkedin', 'LinkedIn'), ('behance', 'Behance'))]
SOCIALS = [(lab, u) for lab, u in SOCIALS if u]
TAG = {'Brand strategy': 'strategy', 'Branding': 'branding', 'Packaging design': 'packaging'}
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
CTA = S.get('nav_cta') or 'Book a free call'


def clip(x, n=155):
    x = re.sub(r'\s+', ' ', str(x or '')).strip()
    return x if len(x) <= n else x[:x.rfind(' ', 0, n - 1)] + '…'


def tags(p):
    return ' '.join(TAG[s] for s in p.get('services', []) if s in TAG)


def nice_date(d):
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(d or ''))
    return '%d %s %s' % (int(m.group(3)), MONTHS[int(m.group(2)) - 1], m.group(1)) if m else ''


# ---------- type helpers: the motion is prepared here so pages never flash ----------
def chars(text, start=0):
    """Display text split into words and letters for the rise-in reveal. Lines break on new lines."""
    i = start
    out = []
    for line in [l for l in str(text or '').split('\n') if l.strip()]:
        ws = []
        for w in line.split():
            cs = ''
            for ch in w:
                cs += '<span class="c" style="--i:%d">%s</span>' % (i, t(ch))
                i += 1
            ws.append('<span class="w">%s</span>' % cs)
        out.append(' '.join(ws))
    return '<span aria-hidden="true">%s</span>' % '<br>'.join(out)


def plain(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def title(tag, text, cls='', extra=''):
    return '<%s class="dh ch2 %s" aria-label="%s"%s>%s</%s>' % (tag, cls, at(plain(text)), extra, chars(text), tag)


def rls(text):
    """Each line rises through a mask."""
    return ''.join('<span class="rl"><span>%s</span></span>' % t(l) for l in str(text or '').split('\n') if l.strip())


def scrub(text):
    """Words that light up as the reader scrolls past."""
    return ' '.join('<span class="sw">%s</span>' % t(w) for w in plain(text).split(' '))


def first_sentence(text):
    x = plain(text)
    m = re.match(r'^(.+?[.!?])\s+(.+)$', x)
    return (m.group(1), m.group(2)) if m else (x, '')


def sym(cls=''):
    return '<svg class="%s" viewBox="0 0 1149 1149" fill="currentColor" aria-hidden="true">%s</svg>' % (cls, BRAND['sym'])


def pic(src, alt, sizes='100vw', eager=False, full=False):
    h = img_tag(src, alt, sizes=sizes)
    if eager:
        h = h.replace(' loading="lazy"', ' fetchpriority="high"')
    if full:
        h = h.replace('<img ', '<img data-full="%s" ' % at(img(src)), 1)
    return h


def social_fl():
    return ''.join('<a class="fl" href="%s" target="_blank" rel="noopener"><b>%s</b><i>↗</i></a>' % (at(u), lab) for lab, u in SOCIALS)


# ---------- shared blocks ----------
def process_html(show_get=False):
    steps = ''
    for i, x in enumerate(SERVICES.get('process', [])):
        note = (' · ' + t(x['note'])) if x.get('note') else ''
        get = '<div class="get"><b>You get</b>%s</div>' % t(x['get']) if show_get and x.get('get') else ''
        steps += ('<div class="step"><span class="num">%s%s</span><h4 class="dh">%s</h4><p>%s</p>%s<small>%s</small></div>'
                  % (num(i), note, t(x['title']), t(x.get('text')), get, t(x.get('time'))))
    return '<div class="pl" id="pl"><i class="fill"></i><i class="head" id="phead"></i>%s</div>' % steps


def work_row(p, i, hide_thumb=False):
    thumb = '' if hide_thumb else img_tag(p.get('cover_image'), '', 'thumb', '100vw')
    return ('<a class="wr fu" href="/work/%s/" data-pv="%d" data-cur="View" data-pt="%s" data-t="%s"><span class="n">%s</span><h3 class="dh">%s</h3>'
            '<span class="m"><b>%s</b>%s</span>%s</a>'
            % (p['slug'], i, at(p['title']), tags(p), num(i), t(p['title']), t(p['sector']), t(p.get('tagline')), thumb))


def preview(srcs):
    return '<div class="pv" id="pv" aria-hidden="true">%s</div>' % ''.join(
        '<img src="%s" alt="" data-i="%d" loading="lazy" decoding="async">' % (at(img(s)), i) for i, s in enumerate(srcs))


def page_head(label, heading, lead, right='', side=''):
    return ('<header class="ph"><div class="lbl fu" data-late="1"><span>%s</span><span>%s</span></div>%s'
            '<div class="pl2 fu" data-late="1"><span class="lbl">%s</span><p>%s</p></div></header>'
            % (t(label), right, title('h1', heading, '', ' data-late="1"'), side or 'Sharp Story', t(lead)))


def end_html(full=True):
    cta = ''
    if full:
        cta = ('<span class="lbl">%s</span>%s<div class="bt"><a class="mag" href="/book/">%s →</a><span class="alt2">%s</span></div>'
               % (t(S.get('cta_label')), title('h2', S.get('cta_heading') or "Let's talk."), t(CTA), t(S.get('cta_note'))))
    follow = '<div class="fc"><span class="lbl">Follow</span>%s</div>' % social_fl() if SOCIALS else '<div></div>'
    return ('<section class="end%s" id="end" data-inv data-dk>%s<footer class="ft">'
            '<div class="fc fintro"><p class="dh">%s</p><span class="live"><i></i>%s</span></div>'
            '<nav class="fc" aria-label="Studio"><span class="lbl">Studio</span><a class="fl" href="/work/"><b>Work</b><i>→</i></a><a class="fl" href="/services/"><b>Services</b><i>→</i></a>'
            '<a class="fl" href="/about/"><b>About</b><i>→</i></a><a class="fl" href="/journal/"><b>Journal</b><i>→</i></a></nav>'
            '<div class="fc"><span class="lbl">Contact</span><a class="mail" href="mailto:%s">%s</a><a class="fl" href="/book/"><b>%s</b><i>→</i></a><a class="fl" href="/contact/"><b>Send a brief</b><i>→</i></a></div>'
            '%s<a class="btt" href="#" id="btt" aria-label="Back to top"><svg viewBox="0 0 120 120" aria-hidden="true"><defs><path id="cir" d="M60,60 m-46,0 a46,46 0 1,1 92,0 a46,46 0 1,1 -92,0"/></defs>'
            '<text><textPath href="#cir" textLength="286" lengthAdjust="spacing">BACK TO TOP • BACK TO TOP • </textPath></text></svg><span><b>↑</b></span></a></footer>'
            '<svg class="ewm" id="ewm" viewBox="0 0 578.45 61.54" role="img" aria-label="Sharp Story">%s</svg>'
            '<div class="fine"><span>© %s Sharp Story</span><span>%s</span></div></section>'
            % ('' if full else ' short', cta, br(S.get('footer_heading')), t(S.get('footer_status')), at(EMAIL), t(EMAIL), t(CTA), follow,
               BRAND['wm'], YEAR, t(S.get('footer_tagline'))))


# ---------- home ----------
def home_html():
    h = HOME
    words = [[w.get('top', ''), w.get('bottom', '')] for w in h.get('hero_words', [])] or [['Sharp', 'Story']]
    shown = [p for p in PROJECTS if p.get('show_on_home')] or PROJECTS
    out = '<h1 class="sr">%s</h1>' % t('%s: %s' % (S.get('site_name', 'Sharp Story'), h.get('hero_text')))
    out += ('<section class="hero" id="hero"><div class="hk" id="hk" data-cur="Click" data-words="%s">'
            '<div class="kn c" id="h1" aria-hidden="true">%s</div><div class="kn c" id="h2" aria-hidden="true">%s</div>'
            '<div class="hb"><p>%s</p><span class="mid" id="hmid" aria-hidden="true"></span><span class="r lb">%s</span></div></div></section>'
            % (at(json.dumps(words, ensure_ascii=False)), t(words[0][0]), t(words[0][1]), t(h.get('hero_text')), t(h.get('hero_corner'))))
    lines = h.get('studio_lines', [])
    ps = ''.join('<p>%s</p>' % ' '.join('<span class="w"><span style="--i:%d">%s</span></span>' % (k, t(w)) for k, w in enumerate(plain(l).split(' '))) for l in lines)
    out += ('<section class="say" id="say-s" data-dk><div class="sayp"><span class="lbl">%s</span><div class="sl" id="sl">%s</div>'
            '<div class="sbar"><span id="sn">01</span><i><b></b></i><span>%s</span></div></div></section>'
            % (t(h.get('studio_label')), ps, num(len(lines) - 1)))
    tk = ''.join('<span>%s</span><i>✳</i>' % t(w) for w in h.get('ticker', [])) * 4
    out += '<div class="tk" aria-hidden="true"><div class="dh" id="tk">%s</div></div>' % tk
    out += ('<section class="sec" id="work"><div class="sh rvb"><h2 class="dh">%s</h2></div><div>%s</div>'
            '<div class="wfoot"><a class="ul" href="/work/" data-pt="Work">%s →</a></div></section>'
            % (rls(h.get('work_heading')), ''.join(work_row(p, i) for i, p in enumerate(shown)), t(h.get('work_link'))))
    out += preview([p.get('detail_image') or p.get('cover_image') for p in shown])
    cards = ''.join('<a class="card" href="/services/#%s" data-pt="Services"><div class="n"><span>%s</span><span class="ic">↗</span></div><h3 class="dh">%s</h3><p>%s</p><ul>%s</ul></a>'
                    % (slugify(x['title']), num(i), t(x['title']), t(x.get('card_text') or x.get('line')), ''.join('<li>%s</li>' % t(v) for v in x.get('tags', [])))
                    for i, x in enumerate(SERVICES.get('services', [])))
    out += ('<section class="sec dark" id="services" data-dk><div class="sh rvb"><h2 class="dh">%s</h2><span class="fu">%s</span></div><div class="cards">%s</div></section>'
            % (rls(h.get('services_heading')), t(h.get('services_note')), cards))
    out += ('<section class="sec" id="process"><div class="sh rvb"><h2 class="dh">%s</h2></div>%s</section>'
            % (rls(h.get('process_heading')), process_html()))
    return out


def slugify(x):
    return re.sub(r'[^a-z0-9]+', '-', str(x).lower()).strip('-')


# ---------- work ----------
def work_html():
    w = WORK
    n = len(PROJECTS)
    counts = {k: sum(1 for p in PROJECTS if v in p.get('services', [])) for v, k in TAG.items()}
    chips = '<button class="chip on" data-f="all" aria-pressed="true">All<sup>%s</sup></button>' % num(n - 1)
    chips += ''.join('<button class="chip" data-f="%s" aria-pressed="false">%s<sup>%s</sup></button>' % (k, t(v), num(counts[k] - 1))
                     for v, k in TAG.items() if counts[k])
    cards = ''
    for i, p in enumerate(PROJECTS):
        port = i % 4 in (1, 2)
        src = (p.get('detail_image') if port else None) or p.get('gallery_image') or p.get('cover_image')
        cards += ('<a class="wc fu%s" href="/work/%s/" data-t="%s" data-cur="View" data-pt="%s"><div class="im ri"><span data-py="0.05">%s</span></div>'
                  '<div class="wt"><span class="n">%s</span><h2 class="dh"><span>%s</span></h2><span class="s">%s</span><p>%s</p></div></a>'
                  % (' pt2' if port else '', p['slug'], tags(p), at(p['title']), pic(src, '%s, %s' % (p['title'], p['sector'].lower()), '(max-width: 800px) 100vw, 58vw'),
                     num(i), t(p['title']), t(p['sector']), t(p.get('tagline'))))
    rows = ''.join(work_row(p, i, True) for i, p in enumerate(PROJECTS))
    out = page_head('Work', w['heading'], w['lead'], '<b id="wcount">%s</b> projects' % ('%02d' % n), 'Strategy · Identity · Packaging')
    out += ('<div class="wk" data-m="grid"><div class="wbar"><div id="wf" role="group" aria-label="Filter by service">%s</div>'
            '<div id="wv" role="group" aria-label="Layout"><button class="chip on" data-m="grid" aria-pressed="true">Grid</button><button class="chip" data-m="list" aria-pressed="false">List</button></div></div>'
            '<div class="wg">%s</div><div class="wl2">%s</div></div>' % (chips, cards, rows))
    return out + preview([p.get('detail_image') or p.get('cover_image') for p in PROJECTS])


# ---------- case study ----------
def case_html(p, i):
    x = PROJECTS[(i + 1) % len(PROJECTS)]
    cc = p.get('concept')
    n = p['title']
    lab = ('The brief', 'The insight', 'The idea', 'The system', 'The aim') if cc else ('The challenge', 'The insight', 'The idea', 'The system', 'The outcome')
    fig = [0]

    def capn():
        fig[0] += 1
        return 'Fig. %s' % num(fig[0] - 1)

    def cnum(k, label):
        return '<div class="cnum"><b>%s</b><span>%s</span></div>' % (num(k), t(label))

    def chap(k, label):
        return ' data-chap="%s — %s"' % (num(k), at(label))

    services = '<br>'.join(t(s) for s in p.get('services', []))
    out = ('<header class="ch"><div class="crow fu" data-late="1"><a class="back" href="/work/" data-pt="Work"><i>←</i> All work</a><span class="lbl">Project %s / %s</span></div>'
           '<h1 class="dh ct" aria-label="%s">%s</h1>'
           '<dl class="cmeta"><div class="fu" data-late="1"><dt>In short</dt><dd class="tl">%s</dd></div><div class="fu" data-late="1"><dt>Sector</dt><dd>%s</dd></div>'
           '<div class="fu" data-late="1"><dt>Services</dt><dd>%s</dd></div><div class="fu" data-late="1"><dt>Type</dt><dd>%s</dd></div></dl></header>'
           % (num(i), num(len(PROJECTS) - 1), at(n), chars(n), t(p.get('tagline')), t(p['sector']), services, 'Brand concept' if cc else 'Client project'))
    out += ('<section class="cx" aria-label="Cover"><div class="cxs"><div class="cxi" data-zoom data-cur="Open">%s</div>'
            '<div class="cxt"><span class="lbl">%s</span><span class="lbl">%s</span></div></div></section>'
            % (pic(p.get('cover_image'), '%s, %s' % (n, p['sector'].lower()), eager=True, full=True), t(n), t(p['sector'])))
    a, b = first_sentence(p.get('challenge'))
    out += ('<section class="cs"%s><div class="cg">%s<div class="cbody"><p class="big sc">%s</p>%s</div></div></section>'
            % (chap(0, lab[0]), cnum(0, lab[0]), scrub(a), '<p class="fu">%s</p>' % t(b) if b else ''))
    if img(p.get('range_image')):
        out += ('<figure><div class="fb ri" data-zoom data-cur="Open"><span data-py="0.1">%s</span></div><figcaption class="cap"><span>%s</span><span>%s</span></figcaption></figure>'
                % (pic(p['range_image'], '%s, %s' % (n, p.get('range_caption') or 'range'), full=True), capn(), t(p.get('range_caption'))))
    if p.get('insight'):
        out += '<section class="cq"%s>%s<p class="dh sc">%s</p></section>' % (chap(1, lab[1]), cnum(1, lab[1]), scrub(p['insight']))
    a, b = first_sentence(p.get('idea'))
    ident = ''
    if img(p.get('identity_image')):
        ident = ('<figure class="im2 fu"><div class="im ri" data-zoom data-cur="Open">%s</div><figcaption class="cap in"><span>%s</span><span>%s</span></figcaption></figure>'
                 % (pic(p['identity_image'], '%s, %s' % (n, p.get('identity_caption') or 'identity'), full=True), capn(), t(p.get('identity_caption'))))
    out += ('<section class="cs cidea"%s><div class="cg">%s<div class="cbody"><p class="big sc">%s</p>%s</div>%s</div></section>'
            % (chap(2, lab[2]), cnum(2, lab[2]), scrub(a), '<p class="fu">%s</p>' % t(b) if b else '', ident))
    figs = ''
    for k in ('detail', 'stationery', 'poster'):
        if img(p.get(k + '_image')):
            figs += ('<figure data-zoom data-cur="Open"><div class="im">%s</div><figcaption><b>%s</b>%s</figcaption></figure>'
                     % (pic(p[k + '_image'], '%s, %s' % (n, p.get(k + '_caption') or k), '(max-width: 800px) 90vw, 60vw', full=True), capn(), t(p.get(k + '_caption'))))
    dl = ''.join('<li><span>%s</span>%s</li>' % (num(k), t(v)) for k, v in enumerate(p.get('deliverables', [])))
    out += ('<section class="strip" data-dk%s><div class="stp"><div class="trk"><div class="sti">%s<h2 class="dh">What we made</h2><ol>%s</ol></div>%s</div>'
            '<div class="stb"><span>%s</span><i><b></b></i><span>%s</span></div></div></section>'
            % (chap(3, lab[3]), cnum(3, lab[3]), dl, figs, t(n), 'Keep scrolling'))
    out += ('<section class="cout dark" data-dk%s>%s<p class="dh sc">%s</p><div class="del">'
            '<div class="fu"><span>Sector</span>%s</div><div class="fu"><span>Services</span>%s</div><div class="fu"><span>Type</span>%s</div>'
            '<div class="fu"><span>Your brand next?</span><a class="ul" href="/book/" data-pt="%s">%s →</a></div></div></section>'
            % (chap(4, lab[4]), cnum(4, lab[4]), scrub(p.get('outcome')), t(p['sector']), services, 'Brand concept' if cc else 'Client project', at(CTA), t(CTA)))
    out += ('<a class="cnx" href="/work/%s/" data-pt="%s" data-cur="Open" data-chapend><div class="nxs"><div class="nxi">%s</div>'
            '<div class="nxh"><span>Next project</span><span>%s / %s</span></div><div class="nxt"><h2 class="dh">%s</h2><span class="lbl">%s →</span></div></div></a>'
            % (x['slug'], at(x['title']), pic(x.get('cover_image'), ''), num((i + 1) % len(PROJECTS)), num(len(PROJECTS) - 1), t(x['title']), t(x['sector'])))
    return out


CASE_EXTRA = ('<div class="chp" id="chp" aria-hidden="true"><svg viewBox="0 0 32 32"><circle class="a" cx="16" cy="16" r="14"/><circle class="b" cx="16" cy="16" r="14"/></svg><em></em></div>'
              '<div class="lbx" id="lbx" role="dialog" aria-label="Image viewer"><img alt=""><button type="button">Close</button></div>')


# ---------- services ----------
def services_html():
    c = SERVICES
    sv = c.get('services', [])
    out = page_head(c.get('label') or 'Services', c['heading'], c.get('lead'), '%s services' % ('%02d' % len(sv)), 'Strategy · Identity · Packaging')
    rows = ''
    for i, x in enumerate(sv):
        inc = ''.join('<li class="fu"><span>%s</span>%s</li>' % (num(k), t(v)) for k, v in enumerate(x.get('includes', [])))
        rows += ('<article class="svx" id="%s"><div class="sx1 rvb"><span class="lbl">%s / %s</span><h2 class="dh">%s</h2><p class="fu">%s</p></div>'
                 '<div class="sx2"><p class="fu">%s</p><dl class="fu"><div><dt>For</dt><dd>%s</dd></div><div><dt>Typical timeline</dt><dd>%s</dd></div></dl>'
                 '<span class="lbl mut">What’s included</span><ol>%s</ol></div></article>'
                 % (slugify(x['title']), num(i), num(len(sv) - 1), rls(x['title']), t(x.get('line')), t(x.get('text')), t(x.get('for')), t(x.get('timeline')), inc))
    note = '<p class="svnote fu">%s</p>' % t(c['together_note']) if c.get('together_note') else ''
    out += '<section class="sec" style="padding-top:0">%s%s</section>' % (rows, note)
    out += ('<section class="sec" id="process" style="padding-top:0"><div class="sh rvb"><h2 class="dh">%s</h2><span class="fu">%s</span></div>%s</section>'
            % (rls(c.get('process_heading')), t(c.get('process_label')), process_html(True)))
    h = HOME
    if h.get('faq'):
        items = ''.join('<details class="fqi fu"><summary><span>%s</span><i aria-hidden="true"></i></summary><div class="fa"><div><p>%s</p></div></div></details>'
                        % (t(f['q']), t(f['a'])) for f in h['faq'])
        out += ('<section class="sec fq" id="faq" style="padding-top:0"><div class="sh rvb"><h2 class="dh">%s</h2><span class="fu">%s</span></div><div>%s</div></section>'
                % (rls(h.get('faq_heading')), t(h.get('faq_label')), items))
    return out


# ---------- about ----------
def about_html():
    a = ABOUT
    out = page_head('About', a['heading'], a['lead'], 'Independent studio', 'The studio')
    out += '<section class="stm dark" data-dk><span class="lbl" style="color:#8f9dff">What we believe</span><p class="dh sc">%s</p></section>' % scrub(a.get('statement'))
    photo = img(a.get('founder_photo'))
    face = img_tag(photo, a.get('founder_name', '')) if photo else ''
    out += ('<section class="cs story"><div class="cg"><div class="cnum"><b>01</b><span>The studio</span></div><div class="cbody">%s'
            '<div class="fdr fu">%s<div><b>%s</b><span>%s</span></div></div></div></div></section>'
            % (''.join('<p class="fu">%s</p>' % t(x) for x in a.get('story', [])), face, t(a.get('founder_name')), t(a.get('founder_role'))))
    cards = ''.join('<div class="card"><div class="n"><span>%s</span><span class="ic">✳</span></div><h3 class="dh">%s</h3><p>%s</p></div>'
                    % (num(i), t(x['title']), t(x['text'])) for i, x in enumerate(a.get('audiences', [])))
    out += ('<section class="sec dark" data-dk><div class="sh rvb"><h2 class="dh">%s</h2></div><div class="cards c2">%s</div></section>'
            % (rls(a.get('audience_label')), cards))
    pr = ''.join('<li class="fu"><span>%s</span><h3 class="dh">%s</h3><p>%s</p></li>' % (num(i), t(x['title']), t(x['text'])) for i, x in enumerate(a.get('principles', [])))
    out += '<section class="sec"><div class="sh rvb"><h2 class="dh">%s</h2></div><ol class="pr2">%s</ol></section>' % (rls(a.get('principles_label')), pr)
    return out


# ---------- journal ----------
def journal_html():
    j = JOURNAL
    out = page_head('Journal', j['heading'], j['lead'], '%s articles' % ('%02d' % len(ARTICLES)), 'Notes from the studio')
    if ARTICLES:
        f = ARTICLES[0]
        out += ('<a class="jfe fu" href="/journal/%s/" data-cur="Read" data-pt="%s"><div class="im ri">%s</div><div class="tx"><span class="lbl">Featured · %s · %s</span>'
                '<h2 class="dh">%s</h2><p>%s</p><span class="ul">Read article →</span></div></a>'
                % (f['slug'], at(f['title']), pic(f.get('image'), '', '(max-width: 800px) 100vw, 58vw'), t(f.get('category')), t(f.get('read_time')), t(f['title']), t(f.get('excerpt'))))
    rest = ARTICLES[1:]
    if rest:
        rows = ''.join('<a class="jr fu" href="/journal/%s/" data-pv="%d" data-cur="Read" data-pt="%s"><span class="lbl">%s · %s</span><h3 class="dh">%s</h3><span class="rt">%s</span></a>'
                       % (a['slug'], k, at(a['title']), t(a.get('category')), t(nice_date(a.get('date'))), t(a['title']), t(a.get('read_time'))) for k, a in enumerate(rest))
        out += '<section class="jl"><div class="sh rvb"><h2 class="dh">%s</h2></div><div>%s</div></section>' % (rls(j.get('more_label') or 'More articles'), rows)
        out += preview([a.get('image') for a in rest])
    return out


def article_html(a, i):
    x = ARTICLES[(i + 1) % len(ARTICLES)]
    figure = ('<figure class="afig"><div class="im ri"><span data-py="0.08">%s</span></div></figure>' % pic(a['image'], '', eager=True)) if img(a.get('image')) else ''
    return ('<header class="ah"><div class="crow fu" data-late="1"><a class="back" href="/journal/" data-pt="Journal"><i>←</i> Journal</a><span class="lbl">%s · %s</span></div>'
            '%s<p class="lead fu" data-late="1">%s</p></header>%s'
            '<div class="ab"><aside><p>%s</p><p>%s</p><p>%s</p><a class="ul" href="/book/" data-pt="%s">%s →</a></aside><article class="prose">%s</article></div>'
            '<a class="anx" href="/journal/%s/" data-cur="Read" data-pt="%s" data-dk><span class="lbl">Next article · %s</span><h2 class="dh">%s</h2></a>'
            % (t(a.get('category')), t(a.get('read_time')), title('h1', a['title'], '', ' data-late="1"'), t(a.get('excerpt')), figure,
               t(nice_date(a.get('date'))), t(a.get('category')), t(a.get('read_time')), at(CTA), t(CTA), markdown(a.get('body')),
               x['slug'], at(x['title']), t(x.get('category')), t(x['title'])))


# ---------- contact, book, 404 ----------
def contact_html():
    c = CONTACT
    chips = lambda xs: ''.join('<button type="button" class="chip" aria-pressed="false">%s</button>' % t(v) for v in xs)
    extra = ''.join('<span class="lbl qn">%s</span><div class="chips" id="%s" data-g="1">%s</div>' % (t(c.get(k + '_label')), gid, chips(c.get(k, [])))
                    for k, gid in (('skus', 'skus'), ('timeline', 'tml')) if c.get(k))
    steps = ''.join('<li><span>%s</span>%s</li>' % (num(i), t(v)) for i, v in enumerate(c.get('next_steps', [])))
    social = '<div class="ac fu"><span class="lbl">Elsewhere</span><div class="soc">%s</div></div>' % social_fl() if SOCIALS else ''
    out = page_head('Contact', c['heading'], c['lead'], 'Replies within a day', 'Start a project')
    out += ('<section class="cf"><form name="brief" method="POST" data-netlify="true" netlify-honeypot="bot-field" id="bf" data-email="%s" novalidate>'
            '<input type="hidden" name="form-name" value="brief"><input type="hidden" name="needs" id="fneeds"><input type="hidden" name="skus" id="fskus"><input type="hidden" name="timeline" id="ftime">'
            '<p hidden><label>Leave this empty <input name="bot-field"></label></p>'
            '<label class="fld fu"><span>Your name</span><input id="fn" name="name" autocomplete="name" required><em>Please add your name.</em></label>'
            '<label class="fld fu"><span>Email</span><input id="fe" name="email" type="email" autocomplete="email" required><em>Please add a valid email.</em></label>'
            '<label class="fld fu"><span>Company or brand</span><input id="fc" name="company" autocomplete="organization"></label>'
            '<span class="lbl qn">%s</span><div class="chips fu" id="need" data-g="1">%s</div>%s'
            '<label class="fld fu"><span>Tell us about the project</span><textarea id="fm" name="message" rows="4" required placeholder="%s"></textarea><em>A line or two about the project helps us reply properly.</em></label>'
            '<div class="sub fu"><button type="submit" class="btn" id="snd" data-l="%s">%s <i>→</i></button><p>%s</p></div><p class="ok" id="ok" role="status">%s</p></form>'
            '<aside><div class="ac blue fu" data-inv><span class="lbl">%s</span><h3 class="dh">%s</h3><a class="mag" href="/book/">%s →</a></div>'
            '<div class="ac fu"><span class="lbl">Email</span><a class="mlk" href="mailto:%s">%s</a></div>'
            '<div class="ac fu"><span class="lbl">%s</span><ol>%s</ol></div>%s</aside></section>'
            % (at(EMAIL), t(c.get('needs_label')), chips(c.get('needs', [])), extra, at(c.get('message_placeholder')), at(c.get('button')), t(c.get('button')),
               t(c.get('form_note')), t(c.get('success_message')), t(c.get('call_heading') or 'Prefer to talk?'), t(c.get('call_text') or 'A free 30-minute call.'),
               t(CTA), at(EMAIL), t(EMAIL), t(c.get('next_heading')), steps, social))
    return out


def book_html():
    c = BOOK
    pts = ''.join('<li class="fu"><span>%s</span>%s</li>' % (num(i), t(x)) for i, x in enumerate(c.get('points', [])))
    u = c.get('booking_url', '').strip()
    embed = u + ('&' if '?' in u else '?') + 'gv=true'
    out = page_head(c.get('label') or 'Book a free call', c['heading'], c.get('lead'), '30 minutes · Free', 'Free call')
    out += ('<section class="bk"><div class="bl"><span class="lbl">%s</span><ol>%s</ol><div class="lks"><a class="ul" href="%s" target="_blank" rel="noopener">%s ↗</a>'
            '<a class="ul" href="/contact/" data-pt="Contact">%s →</a></div></div>'
            '<div class="cal fu" data-lenis-prevent><div class="ld">Loading calendar…</div><iframe data-src="%s" title="Book a free call with Sharp Story" loading="lazy"></iframe></div></section>'
            % (t(c.get('points_label')), pts, at(u), t(c.get('fallback')), t(c.get('brief_note')), at(embed)))
    return out


def notfound_html():
    return ('<header class="ph nf"><div class="lbl fu" data-late="1"><span>404</span><span>Page not found</span></div>%s'
            '<div class="pl2 fu" data-late="1"><span class="lbl">Lost?</span><p>The page you were looking for has moved or never existed.</p></div>'
            '<div class="btns fu" data-late="1"><a class="btn" href="/">Home <i>→</i></a><a class="btn ghost" href="/work/">See the work <i>→</i></a><a class="btn ghost" href="/book/">%s <i>→</i></a></div></header>'
            % (title('h1', 'Nothing\nhere.', '', ' data-late="1"'), t(CTA)))


# ---------- assemble ----------
import hashlib, datetime
YEAR = datetime.date.today().year
CSS = open(os.path.join(ROOT, 'src', 'site.css'), encoding='utf-8').read()
JS = open(os.path.join(ROOT, 'src', 'site.js'), encoding='utf-8').read()
VER = hashlib.md5((CSS + JS).encode()).hexdigest()[:8]
LD = json.dumps({'@context': 'https://schema.org', '@type': 'Organization', 'name': S.get('site_name', 'Sharp Story'), 'url': DOMAIN + '/',
                 'logo': DOMAIN + '/apple-touch-icon.png', 'description': S['seo_description'],
                 'knowsAbout': ['Brand strategy', 'Branding', 'Visual identity', 'Packaging design'], 'email': EMAIL}, ensure_ascii=False)
NAV = (('Work', '/work/'), ('Services', '/services/'), ('About', '/about/'), ('Journal', '/journal/'), ('Contact', '/contact/'))
SECTION = {'work': '/work/', 'case': '/work/', 'services': '/services/', 'about': '/about/', 'journal': '/journal/', 'article': '/journal/', 'contact': '/contact/', 'book': '/book/'}


def page(path, view, title_, desc, inner, noindex=False, extra_ld='', end=True, extra='', og=None):
    e = lambda v: html.escape(v, quote=True)
    cur = SECTION.get(view)
    ac = lambda u: ' aria-current="page"' if u == cur else ''
    nav = ''.join('<a href="%s"%s>%s</a>' % (u, ac(u), l) for l, u in NAV)
    mnav = ''.join('<a class="dh" href="%s"%s style="--i:%d"><span>%s</span></a>' % (u, ac(u), k, l) for k, (l, u) in enumerate(NAV + ((CTA, '/book/'),)))
    msoc = ''.join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (at(u), lab) for lab, u in SOCIALS)
    ogi = DOMAIN + (img(og) if og else '/og.png')
    head = ('<title>%s</title><meta name="description" content="%s"><meta property="og:title" content="%s"><meta property="og:description" content="%s">'
            '<meta property="og:type" content="website"><meta property="og:image" content="%s"><meta property="og:url" content="%s%s">'
            '<meta name="twitter:card" content="summary_large_image"><link rel="canonical" href="%s%s"><script type="application/ld+json">%s</script>'
            % (e(title_), e(desc), e(title_), e(desc), e(ogi), DOMAIN, path, DOMAIN, path, LD.replace('</', '<\\/')))
    if extra_ld:
        head += '<script type="application/ld+json">%s</script>' % extra_ld.replace('</', '<\\/')
    if noindex:
        head += '<meta name="robots" content="noindex">'
    rp = '<div class="rp" id="rp" aria-hidden="true"></div>' if view in ('case', 'article') else ''
    return ('<!DOCTYPE html>\n<html lang="en" class="nojs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            '<meta name="theme-color" content="#f1f0eb">%s'
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800&display=swap" rel="stylesheet">'
            '<link rel="stylesheet" href="/assets/site.css?v=%s">'
            '<script>var h=document.documentElement;h.className="js";try{if(sessionStorage.getItem("pt")!==null)h.classList.add("ptin")}catch(e){}</script></head>'
            '<body data-page="%s"><a class="skip" href="#main">Skip to content</a>'
            '<div class="pt" id="pt" aria-hidden="true"><div class="ptw">%s<span class="dh" id="ptt"></span></div></div><div class="cur" id="cur" aria-hidden="true"><b></b></div>%s'
            '<header class="top" id="top"><a class="lg" href="/" aria-label="Sharp Story, home">%s</a>'
            '<nav class="tn" aria-label="Main">%s<a class="cta" href="/book/">%s</a><button class="mb" id="mb" type="button" aria-expanded="false" aria-controls="mn">Menu</button></nav></header>'
            '<div class="mn" id="mn"><nav aria-label="Menu">%s</nav><div class="mf"><a href="mailto:%s">%s</a>%s</div></div>'
            '<main id="main">%s</main>%s%s'
            '<script src="/js/lenis.min.js" defer></script><script src="/assets/site.js?v=%s" defer></script></body></html>'
            % (head, VER, view, sym(), rp, sym(), nav, t(CTA), mnav, at(EMAIL), t(EMAIL), msoc, inner, end_html(end) if end is not None else '', extra, VER))


HOLD_ON = bool(S.get('holding_page'))
PREVIEW_PILL = ('<script>(function(){if(document.cookie.indexOf("ss_preview=")<0)return;var a=document.createElement("a");a.href="/preview/";'
                'a.textContent="Preview mode \u00b7 only you see this";a.style.cssText="position:fixed;z-index:300;left:50%;bottom:calc(16px + env(safe-area-inset-bottom,0px));'
                'transform:translateX(-50%);padding:10px 16px;border-radius:99px;background:#0c0c0d;color:#fff;font:600 12px/1 system-ui,sans-serif;letter-spacing:.06em;'
                'text-transform:uppercase;box-shadow:0 10px 30px -10px #0006";document.body.appendChild(a)})()</script>')


PREVIEW_PAGE = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>Preview — Sharp Story</title><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800&display=swap" rel="stylesheet">
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f1f0eb;color:#0c0c0d;font:400 17px/1.5 "Bricolage Grotesque",system-ui,sans-serif;padding:24px}
main{max-width:520px}h1{font-weight:800;font-stretch:76%%;text-transform:uppercase;font-size:clamp(48px,10vw,88px);line-height:.9;margin:0 0 18px}
p{margin:0 0 14px;color:#0c0c0d99}.b{display:inline-flex;align-items:center;height:52px;padding:0 24px;border-radius:99px;background:#1F3BFF;color:#fff;font-weight:600;border:0;font-size:16px;cursor:pointer;margin:12px 10px 0 0}
.b.o{background:none;color:#0c0c0d;box-shadow:inset 0 0 0 1.5px #0c0c0d}b{color:#0c0c0d}</style></head><body><main>
<h1>Preview</h1><p>The holding page is <b>%s</b> for visitors. Preview mode lets this browser see the full site while you check content. Nobody else sees it.</p>
<p id="state"></p><button class="b" id="on">View the full site</button><button class="b o" id="off">Turn preview off</button></main>
<script>var s=document.getElementById("state");function has(){return document.cookie.indexOf("ss_preview=")>-1}
s.textContent=has()?"Preview mode is on in this browser.":"Preview mode is off in this browser.";
document.getElementById("on").onclick=function(){document.cookie="ss_preview=1; path=/; max-age=2592000; secure; samesite=lax";location.href="/"};
document.getElementById("off").onclick=function(){document.cookie="ss_preview=; path=/; max-age=0; secure; samesite=lax";location.href="/"};</script></body></html>'''


def write(path, h):
    if HOLD_ON:
        h = h.replace('</body>', PREVIEW_PILL + '</body>', 1)
    d = OUT + path
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(h)


def doc_title(p):
    return '%s — %s — Sharp Story' % (p['title'], 'Brand concept' if p.get('concept') else 'Case study')


shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
urls = []
FAQ_LD = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
    {'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in HOME.get('faq', [])]}, ensure_ascii=False) if HOME.get('faq') else ''
for key, data, fn, end in (('home', HOME, home_html, True), ('work', WORK, work_html, True), ('about', ABOUT, about_html, True), ('journal', JOURNAL, journal_html, True),
                           ('contact', CONTACT, contact_html, False), ('services', SERVICES, services_html, True), ('book', BOOK, book_html, False)):
    path = '/' if key == 'home' else '/%s/' % key
    write(path, page(path, key, data['seo_title'], data.get('seo_description') or S['seo_description'], fn(), extra_ld=FAQ_LD if key == 'services' else '', end=end))
    urls.append(path)
for i, p in enumerate(PROJECTS):
    path = '/work/%s/' % p['slug']
    write(path, page(path, 'case', doc_title(p), clip('%s %s' % (p.get('tagline', ''), p.get('challenge', ''))), case_html(p, i), extra=CASE_EXTRA, og=p.get('cover_image')))
    urls.append(path)
for i, a in enumerate(ARTICLES):
    path = '/journal/%s/' % a['slug']
    write(path, page(path, 'article', '%s — Sharp Story' % a['title'], clip(a.get('excerpt')), article_html(a, i), og=a.get('image')))
    urls.append(path)
with open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8') as f:
    f.write(page('/404/', 'notfound', 'Page not found — Sharp Story', S['seo_description'], notfound_html(), noindex=True, end=False))

# ---------------------------------------------------------------- holding page
# While "holding_page" is on in Settings, visitors see /hello/ at the home address and every
# other page sends them there. The booking page, the content manager and the assets stay open.
# Visiting /preview/ sets a cookie that shows the full site to that browser only.
HOLD = load(C('holding.json'))
_lines = [x for x in (HOLD.get('heading') or 'Almost\nsharp.').split('\n')]
_lines_html = '<br>'.join(t(x[:-1]) + '<span class="dot">.</span>' if x.endswith('.') else t(x) for x in _lines)
_hold = open(os.path.join(ROOT, 'src', 'holding.html'), encoding='utf-8').read()
for k, v in {'{{TITLE}}': t('Sharp Story — Branding and packaging for D2C and FMCG brands'), '{{DESC}}': t(S['seo_description']),
             '{{DOMAIN}}': DOMAIN, '{{SYM}}': sym(), '{{STATUS}}': t(HOLD.get('status')), '{{LABEL}}': t(HOLD.get('label')),
             '{{H1_LINES}}': _lines_html, '{{H1_PLAIN}}': t(' '.join(_lines)), '{{TEXT}}': t(HOLD.get('text')), '{{TEXT2}}': t(HOLD.get('text_2')),
             '{{BUTTON}}': t(HOLD.get('button') or 'Book a free call'), '{{EMAIL}}': t(EMAIL), '{{SLUG}}': t(HOLD.get('slug')),
             '{{DATE}}': datetime.date.today().strftime('%d.%m.%Y'),
             '{{SOCIALS}}': ''.join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (at(u), lab) for lab, u in SOCIALS)}.items():
    _hold = _hold.replace(k, v)
os.makedirs(os.path.join(OUT, 'hello'), exist_ok=True)
with open(os.path.join(OUT, 'hello', 'index.html'), 'w', encoding='utf-8') as f:
    f.write(_hold)
os.makedirs(os.path.join(OUT, 'preview'), exist_ok=True)
with open(os.path.join(OUT, 'preview', 'index.html'), 'w', encoding='utf-8') as f:
    f.write(PREVIEW_PAGE % ('on' if HOLD_ON else 'off'))
if HOLD_ON:
    keep = ['/admin', '/book', '/preview', '/hello', '/assets', '/js', '/img', '/selected']
    rules = ['# Generated by build.py while the holding page is on (Settings).',
             '/*  /:splat  200!  Cookie=ss_preview']
    rules += ['%s/*  %s/:splat  200!' % (k, k) for k in keep]
    rules += ['/%s  /%s  200!' % (f, f) for f in ('favicon.svg', 'apple-touch-icon.png', 'og.png', 'robots.txt', 'sitemap.xml')]
    rules += ['/shelf-check/*  /book/  301!', '/*  /hello/index.html  200!']
    with open(os.path.join(OUT, '_redirects'), 'w') as f:
        f.write('\n'.join(rules) + '\n')

shutil.copytree(os.path.join(ROOT, 'static'), OUT, dirs_exist_ok=True)
shutil.copytree(os.path.join(ROOT, 'admin'), os.path.join(OUT, 'admin'), dirs_exist_ok=True)
os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
for name, body in (('site.css', CSS), ('site.js', JS)):
    with open(os.path.join(OUT, 'assets', name), 'w', encoding='utf-8') as f:
        f.write(body)
with open(os.path.join(OUT, 'robots.txt'), 'w') as f:
    f.write('User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /preview/\nDisallow: /hello/\nSitemap: %s/sitemap.xml\n' % DOMAIN)
with open(os.path.join(OUT, 'sitemap.xml'), 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + ''.join('  <url><loc>%s%s</loc></url>\n' % (DOMAIN, u) for u in (['/', '/book/'] if HOLD_ON else urls)) + '</urlset>\n')
print('Built %d pages: %d projects, %d articles. Holding page: %s' % (len(urls), len(PROJECTS), len(ARTICLES), 'ON' if HOLD_ON else 'off'))
