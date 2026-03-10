"""float is rejected by format_timestamp and node_filename to prevent silent precision loss."""

from bukzor.chatgpt_export.splat import format_timestamp, node_filename

format_timestamp(1234567890.123456789)  # E: Argument of type "float" cannot be assigned to parameter "unix_ts" of type "Decimal | str" in function "format_timestamp"
node_filename("abc", 1700000000.0, "user")  # E: Argument of type "float" cannot be assigned to parameter "timestamp" of type "Decimal | str" in function "node_filename"
