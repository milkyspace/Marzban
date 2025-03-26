import asyncio
from typing import Union
import typer
from decouple import UndefinedValueError, config
from rich.console import Console
from rich.panel import Panel
from sqlalchemy import func, select, update
from app.db import GetDB, AsyncSession
from app.db.base import get_db
from app.db.models import Admin, User
from app.models.admin import AdminCreate, AdminPartialModify
from app.operation import OperatorType
from app.operation.admin import AdminOperation
from app.utils.system import readable_size
from textual.app import ComposeResult
from textual.widgets import DataTable, Button, Static
from . import utils
from textual.coordinate import Coordinate
from rich.text import Text
from textual.screen import ModalScreen
from textual.containers import Horizontal, Container, Vertical
from textual.widgets import Input

app = typer.Typer(no_args_is_help=True)


class AdminDelete(ModalScreen):
    def __init__(
        self, db: AsyncSession, operation: AdminOperation, username: str, on_close: callable, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.db = db
        self.operation = operation
        self.username = username
        self.on_close = on_close

    def compose(self) -> ComposeResult:
        with Container(classes="modal-box-delete"):
            yield Static("Are you sure about deleting this admin?")
            yield Horizontal(
                Button("Yes", id="yes", variant="success"),
                Button("No", id="no", variant="error"),
                classes="button-container",
            )

    async def key_left(self) -> None:
        """Move focus left on arrow key press."""
        self.app.action_focus_previous()

    async def key_right(self) -> None:
        """Move focus right on arrow key press."""
        self.app.action_focus_next()

    async def key_down(self) -> None:
        """Move focus down on arrow key press."""
        self.app.action_focus_next()

    async def key_up(self) -> None:
        """Move focus up on arrow key press."""
        self.app.action_focus_previous()

    async def key_escape(self) -> None:
        """Close modal when ESC is pressed."""
        self.app.pop_screen()

    async def on_mount(self) -> None:
        """Ensure the first button is focused."""
        yes_button = self.query_one("#no")
        self.set_focus(yes_button)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            await self.operation.remove_admin(self.db, self.username)
            self.on_close()
        await self.key_escape()


class AdminCreateModale(ModalScreen):
    def __init__(self, db: AsyncSession, operation: AdminOperation, on_close: callable, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db = db
        self.operation = operation
        self.on_close = on_close

    def compose(self) -> ComposeResult:
        with Container(classes="modal-box-create"):
            yield Static("Create a new admin", id="title")
            yield Vertical(
                Input(placeholder="Username", id="username"),
                Input(placeholder="Password", password=True, id="password"),
                Input(placeholder="Confirm Password", password=True, id="confirm_password"),
                Input(placeholder="Telegram ID", id="telegram_id"),
                Input(placeholder="Discord Webhook", id="discord_webhook"),
                classes="input-container",
            )
            yield Horizontal(
                Button("Create", id="create", variant="success"),
                Button("Cancel", id="cancel", variant="error"),
                classes="button-container",
            )

    async def key_left(self) -> None:
        """Move focus left on arrow key press."""
        self.app.action_focus_previous()

    async def key_right(self) -> None:
        """Move focus right on arrow key press."""
        self.app.action_focus_next()

    async def key_down(self) -> None:
        """Move focus down on arrow key press."""
        self.app.action_focus_next()

    async def key_up(self) -> None:
        """Move focus up on arrow key press."""
        self.app.action_focus_previous()

    async def key_escape(self) -> None:
        """Close modal when ESC is pressed."""
        self.app.pop_screen()

    async def on_mount(self) -> None:
        """Ensure the first button is focused."""
        username_input = self.query_one("#username")
        self.set_focus(username_input)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            username = self.query_one("#username").value.strip()
            password = self.query_one("#password").value.strip()
            confirm_password = self.query_one("#confirm_password").value.strip()
            telegram_id = self.query_one("#telegram_id").value.strip()
            discord_webhook = self.query_one("#discord_webhook").value.strip()
            if password != confirm_password:
                self.notify("Password and confirm password do not match")
                return
            try:
                await self.operation.create_admin(
                    self.db,
                    AdminCreate(
                        username=username, password=password, telegram_id=telegram_id, discord_webhook=discord_webhook
                    ),
                )
                self.notify("Admin created successfully")
                self.dismiss()
                self.on_close()
            except ValueError as e:
                for error in str(e).split(";"):
                    self.notify(error.strip())
        elif event.button.id == "cancel":
            self.dismiss()


class AdminContent(Static):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db: AsyncSession = None
        self.admin_operator = AdminOperation(OperatorType.CLI)
        self.table: DataTable = None

    BINDINGS = [
        ("c", "create_admin", "Create admin"),
        ("m", "modify_admin", "Modify admin"),
        ("d", "delete_admin", "Delete admin"),
        ("i", "import_from_env", "Import from env"),
    ]

    def compose(self) -> ComposeResult:
        yield DataTable(id="admin-list")

    async def on_mount(self) -> None:
        self.db = await anext(get_db())
        self.table = self.query_one("#admin-list")
        self.table.cursor_type = "row"
        self.table.styles.text_align = "center"
        await self.admins_list()

    def _center_text(self, text, width):
        padding = width - len(text)
        left_padding = padding // 2
        right_padding = padding - left_padding
        return " " * left_padding + text + " " * right_padding

    async def admins_list(self):
        self.table.clear()
        columns = (
            # "Id",
            "Username",
            "Usage",
            "Reseted usage",
            "Users Usage",
            "Is sudo",
            "Is disabled",
            "Created at",
            "Telegram ID",
            "Discord Webhook",
        )
        admins = await self.admin_operator.get_admins(self.db, offset=0, limit=10)
        usage_data = await asyncio.gather(
            *[calculate_admin_usage(admin.id) for admin in admins],
            *[calculate_admin_reseted_usage(admin.id) for admin in admins],
        )
        usages = usage_data[: len(admins)]
        reseted_usages = usage_data[len(admins) :]
        admins_data = [
            (
                # i + 1,
                admin.username,
                usages[i],
                reseted_usages[i],
                readable_size(admin.users_usage),
                "✔️" if admin.is_sudo else "✖️",
                "✔️" if admin.is_disabled else "✖️",
                utils.readable_datetime(admin.created_at),
                str(admin.telegram_id or "✖️"),
                str(admin.discord_webhook or "✖️"),
            )
            for i, admin in enumerate(admins)
        ]
        column_widths = [
            max(len(str(columns[i])), max(len(str(row[i])) for row in admins_data)) for i in range(len(columns))
        ]

        centered_columns = [self._center_text(column, column_widths[i]) for i, column in enumerate(columns)]
        self.table.add_columns(*centered_columns)

        admins = await self.admin_operator.get_admins(self.db, offset=0, limit=10)
        usage_data = await asyncio.gather(
            *[calculate_admin_usage(admin.id) for admin in admins],
            *[calculate_admin_reseted_usage(admin.id) for admin in admins],
        )
        i = 1
        for row, adnin in zip(admins_data, admins):
            centered_row = [self._center_text(str(cell), column_widths[i]) for i, cell in enumerate(row)]
            label = Text(f"{i}")
            i += 1
            self.table.add_row(*centered_row, key=adnin.username, label=label)

    async def action_delete_admin(self):
        index = self.table.cursor_row
        selected_admin = self.table.coordinate_to_cell_key(Coordinate(index, 0)).row_key.value
        self.app.push_screen(AdminDelete(self.db, self.admin_operator, selected_admin, self._refresh_table))

    def _refresh_table(self):
        self.run_worker(self.admins_list)

    async def action_create_admin(self):
        self.app.push_screen(AdminCreateModale(self.db, self.admin_operator, self._refresh_table))

    async def action_modify_admin(self):
        pass

    async def action_import_from_env(self):
        pass


## ==================================================================
def validate_telegram_id(value: Union[int, str]) -> Union[int, None]:
    if not value:
        return 0
    if not isinstance(value, int) and not value.isdigit():
        raise typer.BadParameter("Telegram ID must be an integer.")
    if int(value) < 0:
        raise typer.BadParameter("Telegram ID must be a positive integer.")
    return value


def validate_discord_webhook(value: str) -> Union[str, None]:
    if not value or value == "0":
        return ""
    if not value.startswith("https://discord.com/api/webhooks/"):
        utils.error("Discord webhook must start with 'https://discord.com/api/webhooks/'")
    return value


async def calculate_admin_usage(admin_id: int) -> str:
    async with GetDB() as db:
        usage = await db.execute(select(func.sum(User.used_traffic)).filter_by(admin_id=admin_id))
        return readable_size(int(usage.scalar() or 0))


async def calculate_admin_reseted_usage(admin_id: int) -> str:
    async with GetDB() as db:
        usage = await db.execute(select(func.sum(User.reseted_usage)).filter_by(admin_id=admin_id))
        return readable_size(int(usage.scalar() or 0))


async def _delete_admin(
    username: str,
    yes_to_all: bool = False,
):
    """
    Deletes the specified admin

    Confirmations can be skipped using `--yes/-y` option.
    """
    async with GetDB() as db:
        try:
            admin = await admin_operator.get_validated_admin(db, username=username)
            if yes_to_all or typer.confirm(f'Are you sure about deleting "{username}"?', default=False):
                await admin_operator.remove_admin(db, username, admin)
                utils.success(f'"{username}" deleted successfully.')
            else:
                utils.error("Operation aborted!")
        except ValueError as e:
            utils.error(str(e))


@app.command(name="delete")
def delete_admin(
    username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True),
    yes_to_all: bool = typer.Option(False, *utils.FLAGS["yes_to_all"], help="Skips confirmations"),
):
    """
    Deletes the specified admin

    Confirmations can be skipped using `--yes/-y` option.
    """
    asyncio.run(_delete_admin(username, yes_to_all))


async def _create_admin(
    username: str,
    is_sudo: bool,
    password: str,
    telegram_id: str,
    discord_webhook: str,
):
    """
    Creates an admin

    Password can also be set using the `MARZBAN_ADMIN_PASSWORD` environment variable for non-interactive usages.
    """
    async with GetDB() as db:
        try:
            await admin_operator.create_admin(
                db,
                AdminCreate(
                    username=username,
                    password=password,
                    is_sudo=is_sudo,
                    telegram_id=telegram_id,
                    discord_webhook=discord_webhook,
                ),
            )
            utils.success(f'Admin "{username}" created successfully.')
        except ValueError as e:
            utils.error(str(e))


@app.command(name="create")
def create_admin(
    username: str = typer.Option(..., *utils.FLAGS["username"], show_default=False, prompt=True),
    is_sudo: bool = typer.Option(False, *utils.FLAGS["is_sudo"], prompt=True),
    password: str = typer.Option(
        ..., prompt=True, confirmation_prompt=True, hide_input=True, hidden=True, envvar=utils.PASSWORD_ENVIRON_NAME
    ),
    telegram_id: str = typer.Option(
        "", *utils.FLAGS["telegram_id"], prompt="Telegram ID", show_default=False, callback=validate_telegram_id
    ),
    discord_webhook: str = typer.Option(
        "", *utils.FLAGS["discord_webhook"], prompt=True, show_default=False, callback=validate_discord_webhook
    ),
):
    """
    Creates an admin

    Password can also be set using the `MARZBAN_ADMIN_PASSWORD` environment variable for non-interactive usages.
    """
    asyncio.run(_create_admin(username, is_sudo, password, telegram_id, discord_webhook))


async def _update_admin(username: str):
    """
    Updates the specified admin

    NOTE: This command CAN NOT be used non-interactively.
    """

    async def _get_modify_model(admin: Admin):
        Console().print(Panel(f'Editing "{username}". Just press "Enter" to leave each field unchanged.'))

        is_sudo: bool = typer.confirm("Is sudo", default=admin.is_sudo)
        is_disabled: bool = typer.confirm("Is disabled", default=admin.is_disabled)
        new_password: Union[str, None] = (
            typer.prompt("New password", default="", show_default=False, confirmation_prompt=True, hide_input=True)
            or None
        )

        telegram_id: str = typer.prompt("Telegram ID (Enter 0 to clear current value)", default=admin.telegram_id or "")
        telegram_id = validate_telegram_id(telegram_id)

        discord_webhook: str = typer.prompt(
            "Discord webhook (Enter 0 to clear current value)", default=admin.discord_webhook or ""
        )
        discord_webhook = validate_discord_webhook(discord_webhook)

        return AdminPartialModify(
            is_sudo=is_sudo,
            password=new_password,
            telegram_id=telegram_id,
            discord_webhook=discord_webhook,
            is_disabled=is_disabled,
        )

    async with GetDB() as db:
        try:
            admin = await admin_operator.get_validated_admin(db, username=username)
            await admin_operator.modify_admin(db, username, _get_modify_model(admin), admin)
            utils.success(f'Admin "{username}" updated successfully.')
        except ValueError as e:
            utils.error(str(e))


@app.command(name="update")
def update_admin(username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True, show_default=False)):
    """
    Updates the specified admin

    NOTE: This command CAN NOT be used non-interactively.
    """
    asyncio.run(_update_admin(username))


async def _import_from_env(yes_to_all: bool = False):
    """
    Imports the sudo admin from env

    Confirmations can be skipped using `--yes/-y` option.

    What does it do?
      - Creates a sudo admin according to `SUDO_USERNAME` and `SUDO_PASSWORD`.
      - Links any user which doesn't have an `admin_id` to the imported sudo admin.
    """
    try:
        username, password = config("SUDO_USERNAME"), config("SUDO_PASSWORD")
    except UndefinedValueError:
        utils.error(
            "Unable to get SUDO_USERNAME and/or SUDO_PASSWORD.\n"
            "Make sure you have set them in the env file or as environment variables."
        )

    if not (username and password):
        utils.error(
            "Unable to retrieve username and password.\nMake sure both SUDO_USERNAME and SUDO_PASSWORD are set."
        )

    async with GetDB() as db:
        try:
            # Try to get existing admin
            admin = await admin_operator.get_validated_admin(db, username=username)
            if not yes_to_all and not typer.confirm(
                f'Admin "{username}" already exists. Do you want to sync it with env?', default=None
            ):
                utils.error("Aborted.")

            # Update existing admin
            await admin_operator.modify_admin(db, username, AdminPartialModify(password=password, is_sudo=True), admin)
        except ValueError:
            # Create new admin if doesn't exist
            try:
                await admin_operator.create_admin(db, AdminCreate(username=username, password=password, is_sudo=True))
            except ValueError as e:
                utils.error(str(e))

        # Update users without admin_id
        result = await db.execute(update(User).filter_by(admin_id=None).values(admin_id=admin.id))
        await db.commit()

        utils.success(
            f'Admin "{username}" imported successfully.\n'
            f"{result.rowcount} users' admin_id set to the {username}'s id.\n"
            "You must delete SUDO_USERNAME and SUDO_PASSWORD from your env file now."
        )


@app.command(name="import-from-env")
def import_from_env(
    yes_to_all: bool = typer.Option(False, *utils.FLAGS["yes_to_all"], help="Skips confirmations"),
):
    """
    Imports the sudo admin from env

    Confirmations can be skipped using `--yes/-y` option.

    What does it do?
      - Creates a sudo admin according to `SUDO_USERNAME` and `SUDO_PASSWORD`.
      - Links any user which doesn't have an `admin_id` to the imported sudo admin.
    """
    asyncio.run(_import_from_env(yes_to_all))
