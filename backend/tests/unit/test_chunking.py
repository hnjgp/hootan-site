from app.twin.chunking import MAX_CHARS, chunk_markdown, detect_lang, pack_lines

DOC = """# Hootan Seifi — Resume

Intro line.

## Experience
- Cafe Bazaar.

### Details
- MECO.

## تحصیلات
- کارشناسی ارشد هوش مصنوعی.
"""


def test_chunks_carry_title_and_heading_path():
    title, chunks = chunk_markdown(DOC)

    assert title == "Hootan Seifi — Resume"
    assert [c.content for c in chunks] == [
        "Hootan Seifi — Resume\nIntro line.",
        "Hootan Seifi — Resume | Experience\n- Cafe Bazaar.",
        "Hootan Seifi — Resume | Experience > Details\n- MECO.",
        "Hootan Seifi — Resume | تحصیلات\n- کارشناسی ارشد هوش مصنوعی.",
    ]
    assert [c.lang for c in chunks] == ["en", "en", "en", "fa"]


def test_persian_text_with_english_tool_names_is_persian():
    assert detect_lang("مهندسی داده: Spark، Kafka، Airflow، SQL Server") == "fa"
    assert detect_lang("Agent with LangGraph and pgvector") == "en"


def test_long_sections_split_under_the_cap_with_overlap():
    lines = [f"line {i} " + "x" * 190 for i in range(10)]

    pieces = pack_lines(lines)

    assert len(pieces) > 1
    assert all(len(p) <= MAX_CHARS for p in pieces)
    assert pieces[1].splitlines()[0] == pieces[0].splitlines()[-1]


def test_a_single_line_longer_than_the_cap_stays_whole():
    long_line = "y" * (MAX_CHARS + 50)

    assert pack_lines(["a", long_line, "b"]) == ["a", long_line, "b"]
