from app.parsers.html_parser import parse_html


def test_parse_html_extracts_required_metrics() -> None:
    page = parse_html(
        """
        <html>
          <head><title>  Example page </title><meta name="description" content=" A short description "></head>
          <body>
            <h1>First</h1><h1>Second</h1>
            <img src="missing-alt.png"><img src="decorative.png" alt=""><img src="blank-alt.png" alt="  ">
            <script>These words must not be counted.</script>
            Visible page words.
          </body>
        </html>
        """
    )

    assert page.title == "Example page"
    assert page.meta_description == "A short description"
    assert page.h1_count == 2
    assert page.images_missing_alt_text == 2
    assert page.approximate_word_count == 5


def test_parse_html_handles_sparse_document() -> None:
    page = parse_html("<html><body></body></html>")

    assert page.title is None
    assert page.meta_description is None
    assert page.h1_count == 0
    assert page.images_missing_alt_text == 0
    assert page.approximate_word_count == 0
