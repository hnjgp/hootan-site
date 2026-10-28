from app.twin.keyword import bm25_scores, rare_words, tokens

DOCS = [
    "Skills | اتوماسیون (خودکارسازی فرایندها) با n8n",
    "Skills | برنامه‌نویسی پایتون با pandas",
    "FAQ | نقاط قوتت چیست؟ ساخت سیستم با تست",
]


def test_tokens_lowercase_and_unify_arabic_letters():
    assert tokens("Power BI يادگيري كار n8n") == [
        "power",
        "bi",
        "یادگیری",
        "کار",
        "n8n",
    ]


def test_rare_word_finds_its_chunk():
    scores = bm25_scores("آیا تجربه اتوماسیون داشتی؟", DOCS)

    assert scores[0] > 0
    assert scores[1] == scores[2] == 0


def test_word_in_every_chunk_counts_less_than_a_rare_one():
    scores = bm25_scores("با پایتون", DOCS)

    assert scores[1] > scores[0] > 0


def test_no_shared_word_scores_zero():
    assert bm25_scores("World Cup", DOCS) == [0, 0, 0]


def test_rare_words_skip_words_found_everywhere():
    docs = [f"Skills | topic {i} with Python" for i in range(10)] + DOCS

    assert rare_words("آیا تجربه اتوماسیون با Python داشتی؟", docs) == {"اتوماسیون"}
