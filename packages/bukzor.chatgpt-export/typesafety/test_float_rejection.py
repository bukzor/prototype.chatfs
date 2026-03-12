"""float is rejected by format_timestamp and Message to prevent silent precision loss."""

from bukzor.chatgpt_export.splat import Message, format_timestamp

format_timestamp(1234567890.123456789)  # E: Argument of type "float" cannot be assigned to parameter "unix_ts" of type "Decimal | str" in function "format_timestamp"
Message(uuid="abc", timestamp=1700000000.0, role="user", text_content=None, raw={})  # E: Argument of type "float" cannot be assigned to parameter "timestamp" of type "Decimal" in function "__init__"
