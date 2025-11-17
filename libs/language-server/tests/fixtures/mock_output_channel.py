"""Mock VS Code output channel for testing."""


class MockOutputChannel:
    """Mock implementation of VS Code OutputChannel.

    Used for testing language server logging and error output
    without requiring actual VS Code environment.

    Attributes:
        name: Channel name (for debugging)
        lines: List of output lines
        show_called: Whether show() was called
        hide_called: Whether hide() was called
        clear_called: Whether clear() was called
    """

    def __init__(self, name: str = "Test Channel") -> None:
        """Initialize mock output channel.

        Args:
            name: Channel name (for debugging)
        """
        self.name = name
        self.lines: list[str] = []
        self.show_called = False
        self.hide_called = False
        self.clear_called = False

    def append_line(self, line: str) -> None:
        """Append line to output.

        Args:
            line: Line to append
        """
        self.lines.append(line)

    def append(self, value: str) -> None:
        """Append value without newline.

        Args:
            value: Value to append
        """
        if self.lines and not self.lines[-1].endswith("\n"):
            self.lines[-1] += value
        else:
            self.lines.append(value)

    def clear(self) -> None:
        """Clear all output."""
        self.lines = []
        self.clear_called = True

    def show(self, preserve_focus: bool = True) -> None:
        """Show the channel.

        Args:
            preserve_focus: Whether to preserve focus
        """
        self.show_called = True

    def hide(self) -> None:
        """Hide the channel."""
        self.hide_called = True

    def dispose(self) -> None:
        """Dispose of the channel."""
        self.clear()

    def get_output(self) -> str:
        """Get all output as string.

        Returns:
            All output lines joined with newlines
        """
        return "\n".join(self.lines)

    def get_lines(self) -> list[str]:
        """Get output lines.

        Returns:
            List of output lines
        """
        return self.lines.copy()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"MockOutputChannel(name={self.name!r}, lines={len(self.lines)})"
