"""Minimal icons for the Services page.

One outline drawing per icon on a 48 x 48 grid, lines in currentColor,
one blue accent. Pick an icon by name in content/services.json.
"""

B = '#1F3BFF'


def svg(body, label):
    return ('<svg class="ill" viewBox="0 0 48 48" role="img" aria-label="%s" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (label, body))


ICONS = {
    # Services
    'strategy': ('<circle cx="24" cy="24" r="18"/><circle cx="24" cy="24" r="11"/>'
                 '<circle cx="24" cy="24" r="4.5" fill="%s" stroke="none"/>' % B, 'Target'),
    'identity': ('<rect x="6" y="11" width="36" height="26" rx="3"/>'
                 '<circle cx="16.5" cy="24" r="5" fill="%s" stroke="none"/><path d="M26 21H36M26 27H32"/>' % B, 'Brand card'),
    'packaging': ('<path d="M24 24L41 15V34L24 43Z" fill="%s" stroke="none"/>'
                  '<path d="M24 6L41 15L24 24L7 15Z"/><path d="M7 15V34L24 43L41 34V15M24 24V43"/>' % B, 'Box'),
    # Process
    'listen': ('<path d="M9 9H39A3 3 0 0 1 42 12V31A3 3 0 0 1 39 34H21L13 41V34H9A3 3 0 0 1 6 31V12A3 3 0 0 1 9 9Z"/>'
               '<circle cx="16" cy="21.5" r="2" fill="currentColor" stroke="none"/>'
               '<circle cx="24" cy="21.5" r="2" fill="%s" stroke="none"/>'
               '<circle cx="32" cy="21.5" r="2" fill="currentColor" stroke="none"/>' % B, 'Conversation'),
    'cut': ('<path d="M6 8H42L29 24V35L19 40V24Z"/><circle cx="24" cy="44" r="2.6" fill="%s" stroke="none"/>' % B, 'Funnel'),
    'shape': ('<path d="M24 5L35 22L30 36H18L13 22Z"/><path d="M24 5V18"/><path d="M17 41H31"/>'
              '<circle cx="24" cy="21.5" r="3" fill="%s" stroke="none"/>' % B, 'Pen'),
    'launch': ('<path d="M24 4C31 9 33 17 33 24L29 33H19L15 24C15 17 17 9 24 4Z"/><circle cx="24" cy="18" r="3.5"/>'
               '<path d="M15 24L10 30V36L17 32M33 24L38 30V36L31 32"/>'
               '<path d="M20.5 37H27.5L24 44Z" fill="%s" stroke="none"/>' % B, 'Rocket'),
}


def icon(name):
    v = ICONS.get((name or '').strip().lower())
    return svg(*v) if v else ''
