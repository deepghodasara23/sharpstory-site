# -*- coding: utf-8 -*-
"""Build sharpstory.studio from the content/ folder.

Everything editable lives in content/ (edited through /admin). This script turns it
into static pages in dist/. It uses only the Python standard library, so it runs on
Netlify with no install step:  python3 build.py
"""
import glob, html, json, os, re, shutil

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
            out.append('<h%d class="rv">%s</h%d>' % (lvl, inline_md(m.group(2)), lvl))
        elif all(re.match(r'^\s*[-*+]\s+', l) for l in ls):
            out.append('<ul class="rv">%s</ul>' % ''.join('<li>%s</li>' % inline_md(re.sub(r'^\s*[-*+]\s+', '', l)) for l in ls))
        elif all(re.match(r'^\s*\d+[.)]\s+', l) for l in ls):
            out.append('<ol class="rv">%s</ol>' % ''.join('<li>%s</li>' % inline_md(re.sub(r'^\s*\d+[.)]\s+', '', l)) for l in ls))
        elif all(l.startswith('>') for l in ls):
            out.append('<blockquote class="rv">%s</blockquote>' % inline_md(' '.join(l.lstrip('> ').strip() for l in ls)))
        elif re.match(r'^!\[[^\]]*\]\([^)]+\)$', b):
            m = re.match(r'^!\[([^\]]*)\]\(([^)\s]+)\)$', b)
            cap = '<figcaption>%s</figcaption>' % t(m.group(1)) if m.group(1) else ''
            out.append('<figure class="rv"><img src="%s" alt="%s" loading="lazy">%s</figure>' % (at(img(m.group(2))), at(m.group(1)), cap))
        else:
            out.append('<p class="rv">%s</p>' % '<br>'.join(inline_md(l) for l in ls))
    return ''.join(out)


SOCIALS = [(lab, S.get(k, '').strip()) for k, lab in (('instagram', 'Instagram'), ('linkedin', 'LinkedIn'), ('behance', 'Behance'))]
SOCIALS = [(lab, u) for lab, u in SOCIALS if u]


def social_links(sep):
    return sep.join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (at(u), lab) for lab, u in SOCIALS)


def clip(x, n=155):
    x = re.sub(r'\s+', ' ', str(x or '')).strip()
    return x if len(x) <= n else x[:x.rfind(' ', 0, n - 1)] + '…'


# ---------- page sections ----------
def home_html():
    h = HOME
    out = ('<h1 class="sr">%s</h1>' % t(S.get('site_name', 'Sharp Story') + ': ' + (h.get('hero_text') or ''))) + ('<header class="hs" id="top"><div class="st" id="st"><div class="gap"><h2 class="d">%s</h2><p>%s</p></div>'
           '<div class="hf L" id="L"><svg class="wmb" viewBox="0 0 578.45 61.54" role="img" aria-label="Sharp Story"><use href="#wm"/></svg><p>%s</p></div>'
           '<div class="hf R" id="R"><svg class="wmb" viewBox="0 0 578.45 61.54" aria-hidden="true"><use href="#wm"/></svg><p>Scroll to cut <i></i></p></div></div></header>'
           % (br(h['hero_heading']), t(h['hero_text']), t(h.get('hero_label'))))
    svc = SERVICES.get('services', [])
    # What we do: the three disciplines as one big statement, then the short intro and a link to the detail.
    out += ('<section class="cut mn"><span class="lab">%s</span><div id="mnr"><h2 class="e svh2">%s</h2></div>'
            '<div class="mnf"><small>%s</small><div class="mnl"><a class="lk" href="/services/">%s <span>→</span></a>%s</div></div></section>'
            % (t(h.get('services_label') or 'What we do'), lines('\n'.join(s['title'] for s in svc)), t(h['manifesto_text']),
               t(h.get('services_link') or 'See services and process'),
               # the featured journal article shows the studio's specialism, so it gets a link here
               '<a class="jp" href="/journal/%s/"><span class="lab">%s</span>%s <span>→</span></a>' % (ARTICLES[0]['slug'], t(h.get('journal_label') or 'From the journal'), t(ARTICLES[0]['title']))
               if ARTICLES else ''))
    feat = [p for p in PROJECTS if p.get('show_on_home')][:max(1, int(h.get('featured_count') or 4))]
    out += '<section id="hw">'
    for k, p in enumerate(feat):
        i = PROJECTS.index(p)
        concept = p.get('concept')
        out += ('<div class="cs %s" data-cur="Open" data-go="case-%s"><div class="tp"><span>%s %s</span><span>%s · %s</span></div>'
                '<div class="ar" data-bg="%s"></div><div class="bt"><h3 class="d">%s</h3><p>%s</p></div>'
                '<a class="go" href="/work/%s/">%s</a></div>'
                % ('kwkb'[k % 4], p['slug'], 'Concept' if concept else 'Case study', num(i), t(p['sector']), t(', '.join(p.get('services', []))),
                   at(url_css(p.get('cover_image'))), '<br>'.join(t(w) for w in p['title'].split(' ')), t(p.get('tagline')),
                   p['slug'], 'View concept' if concept else 'Read case study'))
    out += '</section>'
    out += ('<section class="cut px sw allw"><a href="/work/" data-cur="Open"><span class="lab">%s</span><span class="d">All work <i>→</i></span></a></section>'
            % t(h.get('all_work_label')))
    return out + call_html('sk')


def call_html(cls='sb'):
    c = SERVICES
    return ('<section class="cut px %s cb"><div class="cbg"><div><span class="lab">%s</span><h2 class="d rv">%s</h2></div>'
            '<div class="rv"><p>%s</p><a class="fbtn pri" href="/book/">%s <span>→</span></a></div></div></section>'
            % (cls, t(c.get('call_label')), br(c.get('call_heading')), t(c.get('call_text')), t(c.get('call_button') or 'Book a free call')))


def faq_html():
    h = HOME
    if not h.get('faq'):
        return ''
    items = ''.join('<details class="fqi rv"><summary><span>%s</span><i></i></summary><div class="fqa"><p>%s</p></div></details>' % (t(f['q']), t(f['a']))
                    for f in h['faq'])
    return ('<section class="cut px sw fq" id="faq"><div class="fqg"><div><span class="lab">%s</span><h2 class="d rv">%s</h2></div><div>%s</div></div></section>'
            % (t(h.get('faq_label')), br(h.get('faq_heading')), items))


def services_html():
    c = SERVICES
    out = ('<section class="pg px sk"><span class="lab">%s</span><h1 class="e hh mk">%s</h1><p class="lead rv">%s</p></section>'
           % (t(c.get('label')), lines(c['heading']), t(c.get('lead'))))
    rows = ''
    for i, x in enumerate(c.get('services', [])):
        rows += ('<div class="svc sv2 rv"><span>%s</span><h2 class="d">%s</h2><div><p class="sl">%s</p><p>%s</p>'
                 '<dl class="sfor"><div><dt>For</dt><dd>%s</dd></div><div><dt>Typical timeline</dt><dd>%s</dd></div></dl>'
                 '<span class="lab">What’s included</span><ul>%s</ul></div></div>'
                 % (num(i), t(x['title']), t(x.get('line')), t(x.get('text')), t(x.get('for')), t(x.get('timeline')),
                    ''.join('<li>%s</li>' % t(v) for v in x.get('includes', []))))
    out += '<section class="px sk svl">%s%s</section>' % (rows, '<p class="svn rv">%s</p>' % t(c['together_note']) if c.get('together_note') else '')
    steps = ''.join('<li class="rv" style="--d:%.2fs"><span>%s</span><h3 class="d">%s</h3><p>%s</p><div class="pg2"><b>You get</b>%s</div></li>'
                    % (i * .12, num(i), t(x['title']), t(x.get('text')), t(x.get('get'))) for i, x in enumerate(c.get('process', [])))
    out += ('<section class="cut px sw pr"><span class="lab">%s</span><h2 class="d rv">%s</h2><ol class="pr4">%s</ol></section>'
            % (t(c.get('process_label')), br(c.get('process_heading')), steps))
    return out + faq_html() + call_html()


def notfound_html():
    return ('<section class="pg px sk nf"><span class="lab">404</span><h1 class="e hh mk">%s</h1><p class="lead rv">%s</p>'
            '<div class="nfb"><a class="fbtn pri" href="/">Go to the home page <span>→</span></a><a class="fbtn" href="/work/">See the work <span>→</span></a>'
            '<a class="fbtn" href="/book/">Book a free call <span>→</span></a></div></section>'
            % (lines('Nothing\nhere.'), 'The page you were looking for has moved or never existed.'))


def book_html():
    c = BOOK
    pts = ''.join('<li class="rv"><span>%s</span><p>%s</p></li>' % (num(i), t(x)) for i, x in enumerate(c.get('points', [])))
    u = c.get('booking_url', '').strip()
    embed = u + ('&' if '?' in u else '?') + 'gv=true'
    return ('<section class="pg px sk bkh"><span class="lab">%s</span><h1 class="e hh mk">%s</h1><p class="lead rv">%s</p></section>'
            '<section class="px sk bkb"><div class="bkg"><div><span class="lab">%s</span><ol class="shl">%s</ol>'
            '<p class="bkn"><a href="%s" target="_blank" rel="noopener">%s ↗</a><a href="/contact/">%s →</a></p></div>'
            '<div class="bkf rv" data-lenis-prevent><iframe data-src="%s" title="Book a free brand clarity call" loading="lazy"></iframe></div></div></section>'
            % (t(c.get('label')), lines(c['heading']), t(c.get('lead')), t(c.get('points_label')), pts, at(u), t(c.get('fallback')),
               t(c.get('brief_note')), at(embed)))


def work_html():
    w = WORK
    pick = lambda p: p.get('gallery_image') or p.get('cover_image')
    tiles = ''.join(
        '<article class="tile wr%s" data-t="%s"><span class="wg e" aria-hidden="true">%s</span>'
        '<a class="wi" href="/work/%s/" data-cur="View" tabindex="-1" aria-hidden="true"><div class="im">%s</div></a>'
        '<div class="wt"><span class="lab">%s %s · %s</span><h2 class="e"><a href="/work/%s/">%s</a></h2><p class="wl">%s</p>'
        '<ul class="wtags">%s</ul><p class="wx">%s</p><a class="lk" href="/work/%s/">%s <span>→</span></a></div></article>'
        % (' r' if i % 2 else '', tags(p), t(p['title']), p['slug'],
           img_tag(p.get('cover_image') or pick(p), '%s, %s' % (p['title'], p['sector'].lower()), 'v', '(max-width: 800px) 100vw, 60vw'),
           'Concept' if p.get('concept') else 'Case study', num(i), t(p['sector']), p['slug'], t(p['title']), t(p.get('tagline')),
           ''.join('<li>%s</li>' % t(x) for x in p.get('services', [])), t(clip(p.get('challenge'), 170)),
           p['slug'], 'View concept' if p.get('concept') else 'Read case study')
        for i, p in enumerate(PROJECTS))
    rows = ''.join(
        '<a class="jr ir" href="/work/%s/" data-cur="View" data-t="%s" data-img="%s"><span>%s</span><h3 class="d">%s</h3><span>%s</span><span>%s</span></a>'
        % (p['slug'], tags(p), at(img(p.get('detail_image') or p.get('cover_image'))), num(i), t(p['title']), t(p['sector']), t(', '.join(p.get('services', []))))
        for i, p in enumerate(PROJECTS))
    chips = ('<button class="chip on" data-f="all">All</button><button class="chip" data-f="strategy">Brand strategy</button>'
             '<button class="chip" data-f="branding">Branding</button><button class="chip" data-f="packaging">Packaging</button>')
    return ('<section class="pg px sk wk2" id="wk" data-m="gal"><span class="lab">Work</span><h1 class="e hh mk">%s</h1><p class="lead rv">%s</p>'
            '<div class="bar2"><div class="flt" id="flt">%s</div><div class="flt" id="vt"><button class="chip on" data-m="gal">Visual</button><button class="chip" data-m="idx">Index</button></div></div>'
            '<div class="gal">%s</div><div class="idx">%s</div></section>'
            % (lines(w['heading']), t(w['lead']), chips, tiles, rows))


def about_html():
    a = ABOUT
    photo = img(a.get('founder_photo'))
    face = '<i style="background:%s center/cover"></i>' % at(url_css(photo)) if photo else '<i></i>'
    out = ('<section class="pg px sw"><span class="lab">About</span><h1 class="e hh mk">%s</h1><p class="lead rv">%s</p></section>'
           % (lines(a['heading']), t(a['lead'])))
    out += ('<section class="cut px sk"><div class="s2 ab"><h2 class="d rv">%s</h2><div class="rv">%s<div class="fd">%s<div><b>%s</b>%s</div></div></div></div></section>'
            % (t(a['statement']), ''.join('<p>%s</p>' % t(x) for x in a.get('story', [])), face, t(a.get('founder_name')), t(a.get('founder_role'))))
    out += ('<section class="cut px sw"><span class="lab">%s</span><div class="who">%s</div></section>'
            % (t(a.get('audience_label')), ''.join('<div class="rv"><h3 class="d">%s</h3><p>%s</p></div>' % (t(x['title']), t(x['text'])) for x in a.get('audiences', []))))
    out += ('<section class="cut px sk"><span class="lab">%s</span>%s</section>'
            % (t(a.get('principles_label')), ''.join('<div class="pc rv"><span>%s</span><h3 class="d">%s</h3><p>%s</p></div>' % (num(i), t(x['title']), t(x['text']))
                                                      for i, x in enumerate(a.get('principles', [])))))
    return out + call_html()


def journal_html():
    j = JOURNAL
    out = ('<section class="pg px sw"><span class="lab">Journal</span><h1 class="e hh mk">%s</h1><p class="lead rv">%s</p></section>'
           % (lines(j['heading']), t(j['lead'])))
    if ARTICLES:
        f = ARTICLES[0]
        out += ('<section class="cut px sk"><a class="jf hv" href="/journal/%s/" data-cur="Read"><div class="ar2" data-bg="%s"></div>'
                '<div><span class="lab">Featured · %s · %s</span><h2 class="d">%s</h2><p>%s</p><span class="lk">Read article</span></div></a></section>'
                % (f['slug'], at(url_css(f.get('image'))), t(f.get('category')), t(f.get('read_time')), t(f['title']), t(f.get('excerpt'))))
    if len(ARTICLES) > 1:
        out += '<section class="cut px sw jl"><span class="lab">%s</span>%s</section>' % (
            t(j.get('more_label')),
            ''.join('<a class="jr" href="/journal/%s/" data-cur="Read"><span>%s</span><h3 class="d">%s</h3><span>%s</span></a>'
                    % (a['slug'], t(a.get('category')), t(a['title']), t(a.get('read_time'))) for a in ARTICLES[1:]))
    return out


def contact_html():
    c = CONTACT
    chips = lambda xs: ''.join('<button type="button" class="chip">%s</button>' % t(n) for n in xs)
    needs = chips(c.get('needs', []))
    extra = ''.join('<span class="lab fq2">%s</span><div class="flt" id="%s" data-g="1">%s</div>' % (t(c.get(k + '_label')), gid, chips(c.get(k, [])))
                    for k, gid in (('skus', 'skus'), ('timeline', 'tml')) if c.get(k))
    steps = ''.join('<p>%d. %s</p>' % (i + 1, t(x)) for i, x in enumerate(c.get('next_steps', [])))
    social = ('<div><h4>Elsewhere</h4><p>%s</p></div>' % social_links(' · ')) if SOCIALS else ''
    return ('<section class="pg px sk"><span class="lab">Contact</span><h1 class="e hh mk">%s</h1><p class="lead rv">%s</p><div class="ct">'
            '<form name="brief" method="POST" data-netlify="true" netlify-honeypot="bot-field" id="bf" novalidate><input type="hidden" name="form-name" value="brief">'
            '<input type="hidden" name="needs" id="fneeds"><input type="hidden" name="skus" id="fskus"><input type="hidden" name="timeline" id="ftime"><p hidden><label>Leave this empty <input name="bot-field"></label></p>'
            '<label class="fl"><span>Your name</span><input id="fn" name="name" autocomplete="name" required><em class="em">Please add your name.</em></label>'
            '<label class="fl"><span>Email</span><input id="fe" name="email" type="email" autocomplete="email" required><em class="em">Please add a valid email.</em></label>'
            '<label class="fl"><span>Company or brand</span><input id="fc" name="company" autocomplete="organization"></label>'
            '<span class="lab" style="margin-top:34px">%s</span><div class="flt" id="need" data-g="1">%s</div>%s'
            '<label class="fl"><span>Tell us about the project</span><textarea id="fm" name="message" rows="4" required placeholder="%s"></textarea>'
            '<em class="em">A line or two about the project helps us reply properly.</em></label>'
            '<button type="submit" class="chip snd" id="snd" data-l="%s">%s</button><p class="note">%s</p><p class="ok" id="ok" role="status">%s</p></form>'
            '<aside><div class="acall"><h4>%s</h4><p><a href="/book/">%s →</a></p></div><div><h4>Email</h4><p><a href="mailto:%s">%s</a></p></div><div><h4>%s</h4>%s</div>%s</aside></div></section>'
            % (lines(c['heading']), t(c['lead']), t(c.get('needs_label')), needs, extra, at(c.get('message_placeholder')), at(c.get('button')), t(c.get('button')),
               t(c.get('form_note')), t(c.get('success_message')), t(c.get('call_heading') or 'Prefer to talk?'), t(c.get('call_text') or 'Book a free call'),
               at(EMAIL), t(EMAIL), t(c.get('next_heading')), steps, social))


def footer_html():
    return ('<footer class="cut ft"><div class="fg"><div><span class="lab">%s</span><h2 class="d fh">%s</h2></div>'
            '<div class="fc"><a class="mail" href="mailto:%s">%s</a><div class="fbs"><a class="fbtn pri" href="/book/">%s <span>→</span></a><a class="fbtn" href="/contact/">%s <span>→</span></a></div></div></div>'
            '<div class="crw"><svg class="big" viewBox="0 0 578.45 61.54" role="img" aria-label="Sharp Story"><use href="#wm"/></svg></div>'
            '<div class="fnav"><a href="/work/">Work</a><a href="/services/">Services</a><a href="/about/">About</a><a href="/journal/">Journal</a><a href="/book/">Book a free call</a><a href="/contact/">Contact</a></div>'
            '<div class="f"><span>%s</span><a href="#" id="totop">Back to top ↑</a><span>© Sharp Story</span></div></footer>'
            % (t(S.get('footer_label')), br(S.get('footer_heading')), at(EMAIL), t(EMAIL), t(S.get('footer_button')), t(S.get('footer_secondary') or 'Send a brief'), social_links(' &nbsp; ')))


def fig(src, cls, cap, alt, name):
    if not img(src):
        return ''
    return ('<figure class="ci %s"><div class="cw">%s</div>%s</figure>'
            % (cls, img_tag(src, '%s, %s' % (name, alt), sizes='100vw' if 'wide' in cls or 'full' in cls else '(max-width: 800px) 100vw, 60vw'),
               '<figcaption>%s</figcaption>' % t(cap) if cap else ''))


def case_html(p, i):
    x = PROJECTS[(i + 1) % len(PROJECTS)]
    cc = p.get('concept')
    li = lambda a: '<ul>%s</ul>' % ''.join('<li>%s</li>' % t(v) for v in a)
    n = p['title']
    hero_m = p.get('detail_image') or p.get('cover_image')
    out = ('<section class="sw cht"><a class="bk" href="/work/">← All work</a><span class="lab">%s %s · %s</span><h1 class="d mk"><span class="ln"><span>%s</span></span></h1>%s</section>'
           '<section class="ch"><div class="chi" id="kvi"><div class="chz" style="background-image:%s;--m:%s"></div></div></section>'
           % ('Brand concept' if cc else 'Case study', num(i), t(p['sector']), t(n),
              '<p class="cnote rv">A self-initiated brand concept by Sharp Story, not a client project.</p>' if cc else '',
              at(url_css(p.get('cover_image'))), at(url_css(hero_m))))
    out += ('<section class="sw px cov"><div class="covg"><dl class="cmeta rv"><div><dt>%s</dt><dd>%s</dd></div><div><dt>Sector</dt><dd>%s</dd></div>'
            '<div><dt>Services</dt><dd>%s</dd></div></dl><div><p class="clede rv">%s</p><span class="lab rv">%s</span><p class="cbody rv">%s</p></div></div></section>'
            % ('Concept' if cc else 'Client', t(n), t(p['sector']), li(p.get('services', [])), t(p.get('tagline')),
               'The brief' if cc else 'The problem', t(p.get('challenge'))))
    r = fig(p.get('range_image'), 'full', p.get('range_caption'), 'product range', n)
    if r:
        out += '<section class="sw cfb">%s</section>' % r
    if p.get('insight'):
        out += '<section class="sw px cbeat"><span class="lab rv">The insight</span><p class="bp cq rv">%s</p></section>' % t(p['insight'])
    two = fig(p.get('detail_image'), 'a', p.get('detail_caption'), 'detail', n) + fig(p.get('poster_image'), 'b', p.get('poster_caption'), 'poster', n)
    if two:
        out += '<section class="sw px c2up">%s</section>' % two
    out += ('<section class="cut px sk cbeat"><span class="lab rv">%s</span><p class="bp rv">%s</p>%s%s</section>'
            % ('The idea' if cc else 'The one idea', t(p.get('idea')), fig(p.get('identity_image'), 'wide', p.get('identity_caption'), 'identity', n),
               fig(p.get('stationery_image'), 'off', p.get('stationery_caption'), 'stationery', n)))
    out += ('<section class="cut px sb cout"><span class="lab rv">%s</span><p class="stm d rv">%s</p><div class="cdel rv"><span class="lab">%s</span>%s</div></section>'
            % ('The aim' if cc else 'The result', t(p.get('outcome')), 'What we made' if cc else 'The system', li(p.get('deliverables', []))))
    out += ('<a class="cnext" href="/work/%s/" data-cur="Next"><div class="cnb" data-bg="%s"></div><div class="cnt"><span class="lab">%s · %s</span><span class="d">%s <i>→</i></span></div></a>'
            % (x['slug'], at(url_css(x.get('cover_image'))), 'Next concept' if x.get('concept') else 'Next project', t(x['sector']), t(x['title'])))
    return out


def article_html(a, i):
    x = ARTICLES[(i + 1) % len(ARTICLES)]
    picture = '<figure class="ci afig"><div class="cw">%s</div></figure>' % img_tag(a['image'], '') if img(a.get('image')) else ''
    return ('<section class="pg sw"><a class="bk" href="/journal/">← Journal</a><span class="lab">%s · %s</span><h1 class="d hh2 mk"><span class="ln"><span>%s</span></span></h1><p class="lead rv">%s</p></section>'
            '%s<section class="px sk abody"><div class="body">%s</div></section>'
            '<a class="cut px sb nxt" href="/journal/%s/" data-cur="Next"><span class="lab">Next article</span><span class="d">%s</span></a>'
            % (t(a.get('category')), t(a.get('read_time')), t(a['title']), t(a.get('excerpt')), picture, markdown(a.get('body')), x['slug'], t(x['title'])))


# ---------- assemble ----------
def doc_title(p):
    return '%s — %s — Sharp Story' % (p['title'], 'Brand concept' if p.get('concept') else 'Case study')


CASES = [case_html(p, i) for i, p in enumerate(PROJECTS)]
POSTS = [article_html(a, i) for i, a in enumerate(ARTICLES)]
DATA = {'P': [{'s': p['slug'], 'title': doc_title(p), 'html': CASES[i]} for i, p in enumerate(PROJECTS)],
        'A': [{'s': a['slug'], 'title': '%s — Sharp Story' % a['title'], 'html': POSTS[i]} for i, a in enumerate(ARTICLES)]}
TT = {'home': HOME['seo_title'], 'work': WORK['seo_title'], 'about': ABOUT['seo_title'], 'journal': JOURNAL['seo_title'], 'contact': CONTACT['seo_title'],
      'services': SERVICES['seo_title'], 'book': BOOK['seo_title'], 'notfound': 'Page not found — Sharp Story'}

T = open(os.path.join(ROOT, 'src', 'template.html'), encoding='utf-8').read()
js_str = lambda v: json.dumps(v, ensure_ascii=False).replace('</', '<\\/')
BASE = (T.replace('{{home}}', home_html()).replace('{{work}}', work_html()).replace('{{about}}', about_html())
        .replace('{{journal}}', journal_html()).replace('{{contact}}', contact_html()).replace('{{footer}}', footer_html())
        .replace('{{services}}', services_html()).replace('{{notfound}}', notfound_html()).replace('{{book}}', book_html())
        .replace('{{menu_social}}', social_links('')).replace('{{nav_cta}}', t(S.get('nav_cta') or 'Book a free call')).replace('{{nav_cta_short}}', t(S.get('nav_cta_short') or 'Free call'))
        .replace('{{data}}', js_str(DATA)).replace('{{tt}}', js_str(TT)).replace('{{email}}', EMAIL.replace("'", "\\'")))
assert '{{' not in BASE.replace('{{head}}', ''), re.findall(r'\{\{\w+\}\}', BASE)

LD = json.dumps({'@context': 'https://schema.org', '@type': 'Organization', 'name': S.get('site_name', 'Sharp Story'), 'url': DOMAIN + '/',
                 'logo': DOMAIN + '/apple-touch-icon.png', 'description': S['seo_description'],
                 'knowsAbout': ['Brand strategy', 'Branding', 'Visual identity', 'Packaging design'], 'email': EMAIL}, ensure_ascii=False)




def page(path, view, title, desc, inner=None, noindex=False, extra_ld=''):
    e = lambda v: html.escape(v, quote=True)
    head = ('<title>%s</title>\n<meta name="description" content="%s">\n<meta property="og:title" content="%s"><meta property="og:description" content="%s">'
            '<meta property="og:type" content="website"><meta property="og:image" content="%s/og.png"><meta property="og:url" content="%s%s">'
            '<meta name="twitter:card" content="summary_large_image"><link rel="canonical" href="%s%s">\n<script type="application/ld+json">%s</script>'
            % (e(title), e(desc), e(title), e(desc), DOMAIN, DOMAIN, path, DOMAIN, path, LD.replace('</', '<\\/')))
    if extra_ld:
        head += '\n<script type="application/ld+json">%s</script>' % extra_ld.replace('</', '<\\/')
    h = BASE.replace('{{head}}', head, 1)
    h = h.replace('<main class="vw" id="v-%s">' % view, '<main class="vw on" id="v-%s">' % view, 1)
    if inner is not None:
        h = h.replace('<main class="vw on" id="v-%s"></main>' % view, '<main class="vw on" id="v-%s">%s</main>' % (view, inner), 1)
    if noindex:
        h = h.replace('<meta name="viewport"', '<meta name="robots" content="noindex"><meta name="viewport"', 1)
    return h.replace('<body>', '<body data-v="%s">' % view, 1)


def write(path, h):
    d = OUT + path
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(h)


shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
urls = []
FAQ_LD = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
    {'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in HOME.get('faq', [])]}, ensure_ascii=False) if HOME.get('faq') else ''
for key, data in (('home', HOME), ('work', WORK), ('about', ABOUT), ('journal', JOURNAL), ('contact', CONTACT), ('services', SERVICES), ('book', BOOK)):
    path = '/' if key == 'home' else '/%s/' % key
    write(path, page(path, key, data['seo_title'], data.get('seo_description') or S['seo_description'], extra_ld=FAQ_LD if key == 'services' else ''))
    urls.append(path)
for i, p in enumerate(PROJECTS):
    path = '/work/%s/' % p['slug']
    write(path, page(path, 'case', doc_title(p), clip('%s %s' % (p.get('tagline', ''), p.get('challenge', ''))), CASES[i]))
    urls.append(path)
for i, a in enumerate(ARTICLES):
    path = '/journal/%s/' % a['slug']
    write(path, page(path, 'article', '%s — Sharp Story' % a['title'], clip(a.get('excerpt')), POSTS[i]))
    urls.append(path)
with open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8') as f:
    f.write(page('/404/', 'notfound', 'Page not found — Sharp Story', S['seo_description'], noindex=True))

# static files, editor, search files
shutil.copytree(os.path.join(ROOT, 'static'), OUT, dirs_exist_ok=True)
shutil.copytree(os.path.join(ROOT, 'admin'), os.path.join(OUT, 'admin'), dirs_exist_ok=True)
with open(os.path.join(OUT, 'robots.txt'), 'w') as f:
    f.write('User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: %s/sitemap.xml\n' % DOMAIN)
with open(os.path.join(OUT, 'sitemap.xml'), 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + ''.join('  <url><loc>%s%s</loc></url>\n' % (DOMAIN, u) for u in urls) + '</urlset>\n')
print('Built %d pages: %d projects, %d articles' % (len(urls), len(PROJECTS), len(ARTICLES)))
