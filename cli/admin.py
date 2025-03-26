import asyncio
from typing import Union
import typer
from decouple import UndefinedValueError, config
from sqlalchemy import func, select, update
from app.db import GetDB, AsyncSession
from app.db.base import get_db
from app.db.models import Admin, User
from app.models.admin import AdminCreate, AdminPartialModify
from app.operation import OperatorType
from app.operation.admin import AdminOperation
from app.utils.system import readable_size
from textual.app import ComposeResult
from textual.widgets import DataTable, Button, Static, Input, Switch
from . import utils
from textual.coordinate import Coordinate
from rich.text import Text
from textual.containers import Horizontal, Container, Vertical
from cli import BaseModal
from pydantic import ValidationError

app = typer.Typer(no_args_is_help=True)


class AdminDelete(BaseModal):
    def __init__(
        self, db: AsyncSession, operation: AdminOperation, username: str, on_close: callable, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.db = db
        self.operation = operation
        self.username = username
        self.on_close = on_close

    async def on_mount(self) -> None:
        """Ensure the first button is focused."""
        yes_button = self.query_one("#no")
        self.set_focus(yes_button)

    def compose(self) -> ComposeResult:
        with Container(classes="modal-box-delete"):
            yield Static("Are you sure about deleting this admin?", classes="title")
            yield Horizontal(
                Button("Yes", id="yes", variant="success"),
                Button("No", id="no", variant="error"),
                classes="button-container",
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            try:
                await self.operation.remove_admin(self.db, self.username)
                self.on_close()
            except ValueError as e:
                self.notify(str(e), severity="error", title="Error")
        await self.key_escape()


class AdminCreateModale(BaseModal):
    def __init__(self, db: AsyncSession, operation: AdminOperation, on_close: callable, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db = db
        self.operation = operation
        self.on_close = on_close

    def compose(self) -> ComposeResult:
        with Container(classes="modal-box-form"):
            yield Static("Create a new admin", classes="title")
            yield Vertical(
                Input(placeholder="Username", id="username"),
                Input(placeholder="Password", password=True, id="password"),
                Input(placeholder="Confirm Password", password=True, id="confirm_password"),
                Input(placeholder="Telegram ID", id="telegram_id", type="integer"),
                Input(placeholder="Discord Webhook", id="discord_webhook"),
                Horizontal(
                    Static("Is sudo:     ", classes="label"),
                    Switch(animate=False, id="is_sudo"),
                    classes="switch-container",
                ),
                classes="input-container",
            )
            yield Horizontal(
                Button("Create", id="create", variant="success"),
                Button("Cancel", id="cancel", variant="error"),
                classes="button-container",
            )

    async def on_mount(self) -> None:
        """Ensure the first button is focused."""
        username_input = self.query_one("#username")
        self.set_focus(username_input)

    async def key_enter(self) -> None:
        """Create admin when Enter is pressed."""
        await self.on_button_pressed(Button.Pressed(self.query_one("#create")))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            username = self.query_one("#username").value.strip()
            password = self.query_one("#password").value.strip()
            confirm_password = self.query_one("#confirm_password").value.strip()
            telegram_id = self.query_one("#telegram_id").value or None
            discord_webhook = self.query_one("#discord_webhook").value.strip() or None
            is_sudo = self.query_one("#is_sudo").value
            if password != confirm_password:
                self.notify("Password and confirm password do not match", severity="error", title="Error")
                return
            try:
                await self.operation.create_admin(
                    self.db,
                    AdminCreate(
                        username=username,
                        password=password,
                        telegram_id=telegram_id,
                        discord_webhook=discord_webhook,
                        is_sudo=is_sudo,
                    ),
                )
                self.notify("Admin created successfully", severity="success", title="Success")
                await self.key_escape()
                self.on_close()
            except ValidationError as e:
                for error in e.errors():
                    for err in error["msg"].split(";"):
                        self.notify(
                            err.strip(),
                            severity="error",
                            title=f"Error: {error['loc'][0].replace('_', ' ').capitalize()}",
                        )
            except ValueError as e:
                self.notify(str(e), severity="error", title="Error")
        elif event.button.id == "cancel":
            await self.key_escape()


class AdminModifyModale(BaseModal):
    def __init__(
        self, db: AsyncSession, operation: AdminOperation, admin: Admin, on_close: callable, *args, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.db = db
        self.operation = operation
        self.admin = admin
        self.on_close = on_close

    def compose(self) -> ComposeResult:
        with Container(classes="modal-box-form"):
            yield Static("Modify admin", classes="title")
            yield Vertical(
                Input(placeholder="Password", password=True, id="password"),
                Input(placeholder="Confirm Password", password=True, id="confirm_password"),
                Input(placeholder="Telegram ID", id="telegram_id", type="integer"),
                Input(placeholder="Discord Webhook", id="discord_webhook"),
                Horizontal(
                    Static("Is sudo:     ", classes="label"),
                    Switch(animate=False, id="is_sudo"),
                    Static("Is disabled: ", classes="label"),
                    Switch(animate=False, id="is_disabled"),
                    classes="switch-container",
                ),
                classes="input-container",
            )
            yield Horizontal(
                Button("Save", id="save", variant="success"),
                Button("Cancel", id="cancel", variant="error"),
                classes="button-container",
            )

    async def on_mount(self) -> None:
        if self.admin.telegram_id:
            self.query_one("#telegram_id").value = str(self.admin.telegram_id)
        if self.admin.discord_webhook:
            self.query_one("#discord_webhook").value = self.admin.discord_webhook
        self.query_one("#is_sudo").value = self.admin.is_sudo
        self.query_one("#is_disabled").value = self.admin.is_disabled
        password_input = self.query_one("#password")
        self.set_focus(password_input)

    async def key_enter(self) -> None:
        """Create admin when Enter is pressed."""
        await self.on_button_pressed(Button.Pressed(self.query_one("#save")))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            password = self.query_one("#password").value.strip()
            confirm_password = self.query_one("#confirm_password").value.strip()
            telegram_id = self.query_one("#telegram_id").value or None
            discord_webhook = self.query_one("#discord_webhook").value.strip() or None
            is_sudo = self.query_one("#is_sudo").value
            is_disabled = self.query_one("#is_disabled").value

            if password != confirm_password:
                self.notify("Password and confirm password do not match", severity="error", title="Error")
                return
            try:
                await self.operation.modify_admin(
                    self.db,
                    self.admin.username,
                    AdminPartialModify(
                        password=password,
                        telegram_id=telegram_id,
                        discord_webhook=discord_webhook,
                        is_sudo=is_sudo,
                        is_disabled=is_disabled,
                    ),
                )
                self.notify("Admin modified successfully", severity="success", title="Success")
                await self.key_escape()
                self.on_close()
            except ValidationError as e:
                for error in e.errors():
                    for err in error["msg"].split(";"):
                        self.notify(
                            err.strip(),
                            severity="error",
                            title=f"Error: {error['loc'][0].replace('_', ' ').capitalize()}",
                        )
            except ValueError as e:
                self.notify(str(e), severity="error", title="Error")
        elif event.button.id == "cancel":
            await self.key_escape()


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

    @property
    def selected_admin(self):
        return self.table.coordinate_to_cell_key(Coordinate(self.table.cursor_row, 0)).row_key.value

    async def action_delete_admin(self):
        self.app.push_screen(AdminDelete(self.db, self.admin_operator, self.selected_admin, self._refresh_table))

    def _refresh_table(self):
        self.run_worker(self.admins_list)

    async def action_create_admin(self):
        self.app.push_screen(AdminCreateModale(self.db, self.admin_operator, self._refresh_table))

    async def action_modify_admin(self):
        admin = await self.admin_operator.get_validated_admin(self.db, username=self.selected_admin)
        self.app.push_screen(AdminModifyModale(self.db, self.admin_operator, admin, self._refresh_table))

    async def action_import_from_env(self):
        pass


## ==================================================================


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
