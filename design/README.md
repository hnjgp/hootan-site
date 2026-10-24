# design/

- `mockup/*.dc.html`: the approved final design (Main, Twin, JobFit, Trading). Source of truth for layout, colors, sizes, motion, and all English/Persian copy (see the `T` dictionary in each file's script).
- The mockup files use a design-tool runtime (`support.js`, `<x-dc>`, `{{ }}` holes); they are a reference, not production code. Rebuild them as Next.js components.
- `/_blob/<id>` URLs inside the mockups map to files in `assets/` (table below).

## Assets

| File | Use | Mockup blob id |
|---|---|---|
| `building.png` | Empty trading building (1672x941) | - |
| `crew_idle.png`, `crew_talk.png` | Sheet of the seven agents (idle / talking) | - |
| `office_idle.jpg` | Building with all agents idle (base image on the site) | 708bd5d4... |
| `office_bear.jpg` | Building with the bear talking | f726eaf8... |
| `talk_{data,news,bull,bear,risk,trader,pm}.jpg` | Talking face, sized to each agent's window | 5adc, 445f, eee6, a6a7, 63bd, 4f95, 0a46 |
| `av_{data,news,bull,bear,risk,trader,pm}.jpg` | Round 160px avatars | 6dbd, 5e5f, aaab, f410, 5f7e, 9a3f, 572b |
| `me_smile.jpg` | Hootan at the desk (home page) | 576e... |
| `me_listen.jpg`, `me_think.jpg`, `me_talk.jpg` | Digital twin states (same frame) | b504, 3680, aec2 |
| `me_avatar.jpg`, `me_avatar_sm.jpg` | Hootan avatar | 5407... |

## Agent windows on `building.png` (1672x941)

On the site, `office_idle.jpg` is the base and the speaker's `talk_*.jpg` is layered over their window.

| Agent | x, y, w, h (px) | left%, top%, width%, height% |
|---|---|---|
| Data analyst | 400, 289, 168, 156 | 23.92, 30.71, 10.05, 16.58 |
| News analyst | 636, 289, 167, 156 | 38.04, 30.71, 9.99, 16.58 |
| Bull | 872, 289, 169, 156 | 52.15, 30.71, 10.11, 16.58 |
| Bear | 1105, 289, 168, 156 | 66.09, 30.71, 10.05, 16.58 |
| Risk manager | 427, 556, 103, 172 | 25.54, 59.09, 6.16, 18.28 |
| Trader | 534, 556, 104, 172 | 31.94, 59.09, 6.22, 18.28 |
| Portfolio manager | 1049, 556, 220, 172 | 62.74, 59.09, 13.16, 18.28 |

Sun center: (1432, 145), i.e. (85.65%, 15.4%).
