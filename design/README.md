# design/

- `mockup/*.dc.html`: the approved final design (Main, Twin, JobFit, Trading). Source of truth for layout, colors, sizes, motion, and all English/Persian copy (see the `T` dictionary in each file's script).
- `/_blob/<id>` URLs inside the mockups map to files in `assets/` — see the table in CLAUDE.md section 15.7.
- `assets/originals/`: the original portrait images Hootan generated.
- The mockup files use a design-tool runtime (`support.js`, `<x-dc>`, `{{ }}` holes); they are a reference, not production code. Rebuild them as Next.js components.
