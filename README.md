# sharpstory.studio

Website for Sharp Story. Content is edited at **https://sharpstory.studio/admin** (Sveltia CMS).

- `content/` — all text, case studies and journal articles (JSON). Edited through /admin.
- `static/` — images and icons. Uploads from /admin go to `static/img/uploads/`.
- `src/template.html` — page design, styles and animations.
- `admin/` — content editor setup.
- `build.py` — builds `dist/` from the above. No dependencies: `python3 build.py`.

Netlify runs the build on every push to `main`.
