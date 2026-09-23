"""A UserError reaches the user as its message and status, not a traceback."""

import pytest

from chatfs.user_error import UserError, reports_user_errors


def run_main(error: Exception) -> None:
    @reports_user_errors
    def main() -> None:
        raise error

    main()


class DescribeReportsUserErrors:
    def it_prints_the_message_and_exits_the_status(
        self, capsys: pytest.CaptureFixture[str]
    ):
        with pytest.raises(SystemExit) as exit_info:
            run_main(UserError("scroll further", status=3))

        assert exit_info.value.code == 3
        assert capsys.readouterr().err == "scroll further\n"

    def it_prints_nothing_for_an_empty_message(
        self, capsys: pytest.CaptureFixture[str]
    ):
        with pytest.raises(SystemExit) as exit_info:
            run_main(UserError(status=4))

        assert exit_info.value.code == 4
        assert capsys.readouterr().err == ""

    def it_lets_any_other_exception_through(self):
        with pytest.raises(ZeroDivisionError):
            run_main(ZeroDivisionError())
