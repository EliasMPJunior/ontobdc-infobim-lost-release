from ontobdc.view.component.widget.python import TextWidget


def test_text_widget_renders_heading_then_wrapped_body() -> None:
    widget = TextWidget(heading="Title", body="one two three four five")

    lines = widget.render(available_columns=11)

    assert lines[0] == "Title"
    assert lines[1] == ""
    assert all(len(line) <= 11 for line in lines[2:])
    assert " ".join(lines[2:]) == "one two three four five"


def test_text_widget_renders_headings_and_bullets_from_markdown_lite_body() -> None:
    widget = TextWidget(body="# Heading\n\nintro\n\n- first\n- second")

    lines = widget.render(available_columns=40)

    assert "Heading" in lines
    assert "intro" in lines
    assert "• first" in lines
    assert "• second" in lines


def test_text_widget_strips_bold_and_inline_code_markers() -> None:
    widget = TextWidget(body="this is **bold** and `code`")

    lines = widget.render(available_columns=80)

    assert lines == ["this is bold and code"]


def test_text_widget_with_nothing_set_renders_no_lines() -> None:
    assert TextWidget().render(available_columns=80) == []
