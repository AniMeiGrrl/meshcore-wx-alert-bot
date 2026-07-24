# Contributing

Bug reports and focused pull requests are welcome.

1. Create a virtual environment with Python 3.11 or newer.
2. Install development dependencies with `pip install -e '.[test]'`.
3. Add or update tests for behavior changes.
4. Run `pytest` before opening a pull request.

Do not include real private channel secrets, precise private locations, email
addresses, serial-device identifiers, SQLite databases, or captured alert data
containing sensitive information in issues or commits.

Formatting changes must preserve the configured UTF-8 byte ceiling and keep
protective instructions such as `TAKE SHELTER NOW.` from being truncated.
