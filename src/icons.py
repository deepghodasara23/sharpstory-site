"""Art-directed line illustrations for the Services page.

Each drawing uses currentColor for lines and one blue accent (#1F3BFF).
Classes drive the reveal animation (see template CSS):
  dr  path draws on        fd  fades in        pp  pops in (scale)
  --t custom property sets the delay of each element.
"""

B = '#1F3BFF'


def _t(x):
    return ' style="--t:%.2fs"' % x


def crop(size):
    """Registration/crop marks in the four corners."""
    s, m, l = size, 6, 12
    d = ('M%d %dh%dM%d %dv%d' % (m, m, l, m, m, l) +
         'M%d %dh-%dM%d %dv%d' % (s - m, m, l, s - m, m, l) +
         'M%d %dh%dM%d %dv-%d' % (m, s - m, l, m, s - m, l) +
         'M%d %dh-%dM%d %dv-%d' % (s - m, s - m, l, s - m, s - m, l))
    return '<path class="fd" d="%s" stroke-width="1" opacity=".45"%s/>' % (d, _t(0))


def svg(size, body, label):
    return ('<svg class="ill" viewBox="0 0 %d %d" role="img" aria-label="%s" fill="none" stroke="currentColor" '
            'stroke-linecap="round" stroke-linejoin="round">%s%s</svg>' % (size, size, label, crop(size), body))


def strategy():
    fx, fy = 186, 120
    pts = [(x, y) for x in (30, 62, 94) for y in (40, 80, 120, 160, 200)]
    lines = ''.join('<path class="dr" pathLength="1" d="M%d %dL%d %d" stroke-width="1" opacity=".38"%s/>'
                    % (x, y, fx, fy, _t(.15 + i * .045)) for i, (x, y) in enumerate(pts))
    dots = ''.join('<circle class="pp" cx="%d" cy="%d" r="3.2" fill="var(--k)" stroke-width="1.5"%s/>'
                   % (x, y, _t(i * .03)) for i, (x, y) in enumerate(pts))
    focal = ('<circle class="fd spin" cx="%d" cy="%d" r="24" stroke-width="1.2" stroke-dasharray="2 5"%s/>' % (fx, fy, _t(1.1)) +
             '<path class="fd" d="M%d %dv10M%d %dv-10M%d %dh10" stroke-width="1.5"%s/>' % (fx, fy - 40, fx, fy + 40, fx + 30, fy, _t(1.2)) +
             '<circle class="pp" cx="%d" cy="%d" r="10" fill="%s" stroke="none"%s/>' % (fx, fy, B, _t(1.15)))
    return svg(240, lines + dots + focal, 'Many inputs narrowed to one idea')


def identity():
    g = ('<g class="fd" stroke-width="1" stroke-dasharray="2 4" opacity=".4"%s>' % _t(0) +
         '<rect x="40" y="40" width="160" height="160"/><path d="M40 40L200 200M200 40L40 200M120 24V216M24 120H216"/></g>')
    blue = ('<clipPath id="ill-c"><circle cx="120" cy="120" r="80"/></clipPath>'
            '<g clip-path="url(#ill-c)"><polygon class="wp" points="24,154 216,106 216,216 24,216" fill="%s" stroke="none"%s/></g>' % (B, _t(1.0)))
    circ = '<circle class="dr" pathLength="1" cx="120" cy="120" r="80" stroke-width="1.6" transform="rotate(-90 120 120)"%s/>' % _t(.3)
    cut = '<path class="dr" pathLength="1" d="M24 154L216 106" stroke-width="1.6"%s/>' % _t(.8)
    anchors = ''.join('<rect class="pp" x="%.1f" y="%.1f" width="7" height="7" fill="var(--k)" stroke-width="1.5"%s/>'
                      % (x - 3.5, y - 3.5, _t(1.3 + i * .06))
                      for i, (x, y) in enumerate([(45.3, 148.7), (199.4, 110.2), (120, 40), (40, 120)]))
    return svg(240, g + blue + circ + cut + anchors, 'A mark built on a precise construction grid')


def packaging():
    outline = ('M32 80H64L68 48H116L120 80H152L156 48H204L208 80V160L204 192H156L152 160H120L116 192H68L64 160H32'
               'L22 152V88Z')
    folds = 'M32 80V160M64 80V160M120 80V160M152 80V160M64 80H120M152 80H208M64 160H120M152 160H208'
    body = ('<rect class="fd" x="64" y="80" width="56" height="80" fill="%s" stroke="none"%s/>' % (B, _t(1.0)) +
            '<g class="fd" stroke="#fff" stroke-width="2"%s><circle cx="92" cy="106" r="9"/><path d="M78 132H106M84 140H100"/></g>' % _t(1.2) +
            '<path class="dr" pathLength="1" d="%s" stroke-width="1.6"%s/>' % (outline, _t(.1)) +
            '<path class="fd" d="%s" stroke-width="1" stroke-dasharray="3 4" opacity=".6"%s/>' % (folds, _t(.9)) +
            '<path class="fd" d="M22 26H208M22 21V31M208 21V31M224 48V192M219 48H229M219 192H229" stroke-width="1" opacity=".5"%s/>' % _t(1.3))
    return svg(240, body, 'A packaging dieline with the front panel in blue')


def listen():
    arcs = ''.join('<path class="dr" pathLength="1" d="M%.2f %.2fA%d %d 0 0 1 %.2f %.2f" stroke-width="2"%s/>'
                   % (36 + r * .643, 60 - r * .766, r, r, 36 + r * .643, 60 + r * .766, _t(.2 + i * .15))
                   for i, r in enumerate((20, 36, 52)))
    src = ''.join('<circle class="pp" cx="%d" cy="%d" r="3" fill="currentColor" stroke="none"%s/>' % (x, y, _t(.7 + i * .08))
                  for i, (x, y) in enumerate([(98, 36), (106, 60), (98, 84)]))
    return svg(120, arcs + src + '<circle class="pp" cx="36" cy="60" r="7" fill="%s" stroke="none"%s/>' % (B, _t(.1)), 'Listening')


def cut():
    body = ('<polygon points="24,71.4 96,52.6 96,96 24,96" fill="currentColor" stroke="none"/>'
            '<polygon class="sl" points="24,24 96,24 96,52.6 24,71.4" stroke-width="2"%s/>' % _t(.7) +
            '<path class="dr" pathLength="1" d="M12 74.5L108 49.5" stroke="%s" stroke-width="3.5"%s/>' % (B, _t(.2)))
    return svg(120, body, 'One cut')


def shape():
    sq = '<g class="fd" stroke-width="1" stroke-dasharray="2 3" opacity=".45"%s><rect x="30" y="30" width="60" height="60"/><circle cx="60" cy="60" r="30"/></g>' % _t(0)
    blob = ('<path class="dr" pathLength="1" d="M60 30C84 30 90 36 90 60C90 84 84 90 60 90C36 90 30 84 30 60C30 36 36 30 60 30Z" '
            'stroke="%s" stroke-width="2.8"%s/>' % (B, _t(.2)))
    hd = '<path class="fd" d="M44 30H76M44 90H76M30 44V76M90 44V76" stroke-width="1.2"%s/>' % _t(.9)
    ends = ''.join('<circle class="pp" cx="%d" cy="%d" r="2.4" fill="currentColor" stroke="none"%s/>' % (x, y, _t(1))
                   for x, y in [(44, 30), (76, 30), (44, 90), (76, 90), (30, 44), (30, 76), (90, 44), (90, 76)])
    an = ''.join('<rect class="pp" x="%d" y="%d" width="7" height="7" fill="var(--w)" stroke-width="1.6"%s/>' % (x - 3.5, y - 3.5, _t(1.05))
                 for x, y in [(60, 30), (90, 60), (60, 90), (30, 60)])
    return svg(120, '<g transform="translate(60 60) scale(1.32) translate(-60 -60)">%s</g>' % (sq + blob + hd + ends + an), 'Shaping the idea')


def launch():
    body = ('<path class="dr" pathLength="1" d="M10 104H110" stroke-width="2"%s/>' % _t(0) +
            '<rect class="up" x="16" y="72" width="24" height="32" stroke-width="2" style="--t:.25s;--o:.3"/>' +
            '<rect class="up" x="48" y="54" width="24" height="32" stroke-width="2" style="--t:.45s;--o:.6"/>' +
            '<rect class="up" x="80" y="36" width="24" height="32" fill="%s" stroke="none"%s/>' % (B, _t(.65)) +
            '<path class="fd" d="M86 28L99 19M93 19H99V25" stroke-width="2"%s/>' % _t(1.1))
    return svg(120, body, 'Launch')


ICONS = {'strategy': strategy, 'identity': identity, 'packaging': packaging,
         'listen': listen, 'cut': cut, 'shape': shape, 'launch': launch}


def icon(name):
    f = ICONS.get((name or '').strip().lower())
    return f() if f else ''
