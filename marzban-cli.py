#! /usr/bin/env python3
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from cli.admin import AdminContent


class MarzbanCLI(App):
    """A Textual app to manage marzban"""

    CSS_PATH = "cli/style.tcss"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.theme = "textual-dark"

    BINDINGS = [
        # ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
        ("a", "show_admins", "Show admins"),
        ("u", "show_users", "Show users"),
        ("s", "show_subscriptions", "Show subscriptions"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield AdminContent(id="admin-content")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.action_show_admins()

    def action_show_admins(self) -> None:
        """Show the admins section."""
        self.query_one("#admin-content")

    def action_show_users(self) -> None:
        """Show the users section."""
        self.query_one("#main-content").show_section("users")

    def action_show_subscriptions(self) -> None:
        """Show the subscriptions section."""
        self.query_one("#main-content").show_section("subscriptions")

    # def action_toggle_dark(self) -> None:
    #     """An action to toggle dark mode."""
    #     self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"

    async def action_quit(self) -> None:
        """An action to quit the app."""
        self.exit()


if __name__ == "__main__":
    app = MarzbanCLI()
    app.run()
