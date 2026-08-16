"""Regression tests for splat's turn classification and rendering."""

from chatfs.provider.aistudio.conversation.splat import basename_for, render_turn, turn_kind
from chatfs.provider.aistudio.types import Turn


class DescribeTurnKind:
    def it_classifies_a_user_turn(self):
        turn: Turn = {"role": "user", "text": "hi"}
        assert turn_kind(turn) == "user"

    def it_classifies_a_completed_model_turn_as_answer(self):
        turn: Turn = {"role": "model", "text": "hello", "finishReason": 1}
        assert turn_kind(turn) == "answer"

    def it_classifies_a_thought_turn(self):
        turn: Turn = {"role": "model", "text": "**Thinking**", "isThought": 1}
        assert turn_kind(turn) == "thought"

    def it_classifies_a_model_turn_that_is_neither_thought_nor_answer_as_unmodeled(self):
        # e.g. a model turn still in progress when captured -- no
        # finishReason yet, not marked as a thought either.
        turn: Turn = {"role": "model", "text": "..."}
        assert turn_kind(turn) == "unmodeled"

    def it_classifies_an_unrecognized_role_as_unmodeled(self):
        # the wire format is a third party's and unversioned -- a role this
        # parser has never seen is expected drift, not a crash.
        turn: Turn = {"role": "system", "text": "..."}
        assert turn_kind(turn) == "unmodeled"


class DescribeRenderTurn:
    def it_passes_through_an_unmodeled_turn_as_raw_json(self):
        turn: Turn = {"role": "system", "text": "hi"}
        text = render_turn(turn, "unmodeled")
        assert 'type="unmodeled"' in text
        assert '"role": "system"' in text


class DescribeBasenameFor:
    def it_names_a_user_turn(self):
        assert basename_for(0, "user", "user") == "000.user"

    def it_suffixes_a_thought_turn(self):
        assert basename_for(1, "model", "thought") == "001.model.thought"

    def it_suffixes_an_unmodeled_turn_with_its_actual_role(self):
        # the role is the turn's own, not guessed from kind -- a novel role
        # stays visible in the filename rather than being mislabeled "model".
        assert basename_for(2, "system", "unmodeled") == "002.system.unmodeled"
