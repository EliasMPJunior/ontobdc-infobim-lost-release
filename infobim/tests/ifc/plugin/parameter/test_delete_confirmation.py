from __future__ import annotations

from typing import Any, Dict, List, Optional

from infobim.ifc.plugin.parameter.delete_confirmation import (
    DeleteConfirmationStrategy,
)


class FakeContext:
    def __init__(
        self,
        *,
        raw_args: Optional[List[str]] = None,
        language: Optional[str] = None,
        **parameters: Any,
    ) -> None:
        self.raw_args: List[str] = list(raw_args or [])
        self.language: Optional[str] = language
        self._parameters: Dict[str, Any] = dict(parameters)

    def has_parameter(self, name: str) -> bool:
        return name in self._parameters

    def get_parameter_value(self, name: str) -> Any:
        return self._parameters.get(name)

    def set_parameter_value(self, name: str, value: Any) -> None:
        self._parameters[name] = value


class RecordingPromptChoice:
    def __init__(self, answer: str) -> None:
        self.answer: str = answer
        self.calls: List[Dict[str, Any]] = []

    def __call__(self, *args: Any, **kwargs: Any) -> str:
        self.calls.append({"args": args, "kwargs": kwargs})
        return self.answer


def test_short_yes_flag_skips_the_prompt() -> None:
    context = FakeContext(raw_args=["-y"], element_global_id="G1")
    prompt_choice = RecordingPromptChoice("No")
    strategy = DeleteConfirmationStrategy()
    strategy.set_prompt_choice(prompt_choice)

    strategy.execute(context)

    assert context.get_parameter_value("confirmed") is True
    assert prompt_choice.calls == []


def test_long_yes_flag_skips_the_prompt() -> None:
    context = FakeContext(raw_args=["--yes"], element_global_id="G1")
    prompt_choice = RecordingPromptChoice("No")
    strategy = DeleteConfirmationStrategy()
    strategy.set_prompt_choice(prompt_choice)

    strategy.execute(context)

    assert context.get_parameter_value("confirmed") is True
    assert prompt_choice.calls == []


def test_missing_yes_flag_calls_the_injected_prompt_choice_callback() -> None:
    context = FakeContext(raw_args=[], element_global_id="G1")
    prompt_choice = RecordingPromptChoice("No")
    strategy = DeleteConfirmationStrategy()
    strategy.set_prompt_choice(prompt_choice)

    strategy.execute(context)

    assert len(prompt_choice.calls) == 1


def test_prompt_choice_question_names_the_target_global_id() -> None:
    context = FakeContext(raw_args=[], element_global_id="G1")
    prompt_choice = RecordingPromptChoice("No")
    strategy = DeleteConfirmationStrategy()
    strategy.set_prompt_choice(prompt_choice)

    strategy.execute(context)

    call = prompt_choice.calls[0]
    assert "G1" in call["args"][1]


def test_yes_answer_confirms() -> None:
    context = FakeContext(raw_args=[], element_global_id="G1")
    strategy = DeleteConfirmationStrategy()
    strategy.set_prompt_choice(RecordingPromptChoice("Yes"))

    strategy.execute(context)

    assert context.get_parameter_value("confirmed") is True


def test_no_answer_cancels() -> None:
    context = FakeContext(raw_args=[], element_global_id="G1")
    strategy = DeleteConfirmationStrategy()
    strategy.set_prompt_choice(RecordingPromptChoice("No"))

    strategy.execute(context)

    assert context.get_parameter_value("confirmed") is False


def test_no_is_the_default_option_offered_to_the_prompt() -> None:
    context = FakeContext(raw_args=[], element_global_id="G1")
    prompt_choice = RecordingPromptChoice("No")
    strategy = DeleteConfirmationStrategy()
    strategy.set_prompt_choice(prompt_choice)

    strategy.execute(context)

    call = prompt_choice.calls[0]
    assert call["kwargs"]["default"] == "No"
    assert call["kwargs"]["options"] == ["Yes", "No"]


def test_without_yes_flag_and_without_a_prompt_callback_defaults_to_not_confirmed() -> None:
    context = FakeContext(raw_args=[], element_global_id="G1")
    strategy = DeleteConfirmationStrategy()

    strategy.execute(context)

    assert context.get_parameter_value("confirmed") is False
