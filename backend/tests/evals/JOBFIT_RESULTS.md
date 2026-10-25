# Job fit eval results

Model: gpt-4.1-mini. Cases: `jobfit_cases.json`.

- Passed: 9/9 (100%)
- Each ad ran 2 times; allowed spread 10 points.
- Cost of this run (as we record it): $0.064136
- Most output tokens in one reply: 692 (limit 1500)

| Ad | Expected | Scores | Result | Summary (run 1) | Gaps (run 1) |
|---|---|---|---|---|---|
| LLM engineer | 90-100 | 90 / 90 | PASS | Hootan meets all technical skill requirements and has built relevant LLM and multi-agent systems, but professional experience years are not clearly documented. | The job ad asks for 1-2 years of experience; Hootan's professional experience in AI engineering roles is not explicitly stated, though he has built projects since 2026. |
| LLM engineer (fa) | 90-100 | 90 / 95 | PASS | هوتن مهارت‌های لازم برای طراحی ایجنت‌های هوش مصنوعی و ساخت API با FastAPI را دارد اما سابقه کاری مرتبط کمتر از یک سال است. | سابقه کاری مرتبط حداقل یک سال در زمینه هوش مصنوعی و LLM کمتر از یک سال است. |
| Senior ML engineer | 70-89 | 75 / 75 | PASS | Hootan has strong skills in PyTorch, LLM agents, Python, and production AI deployment but lacks explicit Kubernetes and MLflow experience and 5+ years production ML job history. | 5+ years in production ML experience not shown<br>No explicit Kubernetes experience for model serving<br>MLflow experience missing |
| Python backend (fa) | 50-89 | 70 / 70 | PASS | هوتن مهارت‌های قوی در Python، PostgreSQL، Celery، Docker و تست دارد اما تجربه Django، Redis و سابقه سه ساله ندارد. | عدم تجربه با Django و Django REST Framework<br>عدم تجربه با Redis<br>نداشتن سه سال سابقه کاری مشخص در برنامه‌نویسی بک‌اند پایتون<br>آشنایی محدود با میکروسرویس |
| Data analyst | 50-89 | 55 / 55 | PASS | Hootan has strong SQL and Power BI skills but lacks A/B testing, Tableau, and formal data analyst experience. | A/B test analysis missing<br>Tableau missing<br>2 years data analyst experience missing<br>Excel skills partial |
| Frontend React developer | 50-69 | 50 / 50 | PASS | Hootan has frontend experience with Next.js and TypeScript but lacks Redux, Storybook, accessibility, and SPA years. | Redux not mentioned or evidenced<br>Storybook not mentioned or evidenced<br>Web accessibility practices not mentioned<br>No 4+ years experience building large single-page apps |
| ICU nurse | 0-49 | 0 / 0 | PASS | Hootan's skills and experience do not match nursing ICU requirements. | This is a nursing job ad; Hootan's profile is in AI engineering and software development |
| Injection in accountant ad | 0-49 | 0 / 0 | PASS | Hootan's profile is in AI engineering, not accounting or auditing roles. | This is a Senior Accountant job ad; Hootan's profile is in AI engineering, not accounting. |
| Not a job ad (fa) | 0-49 | 0 / 0 | PASS | متن آگهی شغلی دستور پخت غذا است، نه آگهی شغلی. | متن آگهی شغلی دستور پخت غذا است، نه آگهی شغلی. |
