from enum import Enum

from pydantic import BaseModel, Field


class Telegram(BaseModel):
    enable: bool
    token: str | None
    webhook_url: str | None
    webhook_secret: str | None

    proxy_url: str | None


class Discord(BaseModel):
    enable: bool
    token: str | None

    proxy_url: str | None


class WebhookData(BaseModel):
    url: str
    secret: str


class NotficationSettings(BaseModel):
    # Define Which Notfication System Work's
    notify_telegram: bool
    notify_discord: bool

    # Telegram Settings
    telegram_api_token: str | None
    telegram_logger_admin_id: int | None
    telegram_logger_channel_id: int | None
    telegram_logger_topic_id: int | None

    # Discord Settings
    discord_webhook_url: str | None

    # Proxy Settings
    notfication_proxy_url: str | None


class Webhook(BaseModel):
    enable: bool
    webhooks: list[WebhookData]
    days_left: list[int]
    usage_percent: list[int]
    timeout: int = Field(gt=1)
    recurrent: int = Field(gt=1)

    proxy_url: str | None


class NotficationEnable(BaseModel):
    admin: bool = False
    core: bool = False
    group: bool = False
    host: bool = False
    login: bool = False
    node: bool = False
    user: bool = False
    user_template: bool = False
    days_left: bool = False
    percentage_reached: bool = False


class ConfigFormat(str, Enum):
    links = "links"
    links_base64 = "links_base64"
    xray = "xray"
    sing_box = "sing_box"
    clash = "clash"
    clash_meta = "clash_meta"
    outline = "outline"


class SubRule(BaseModel):
    regex: str
    target: ConfigFormat


class Subscription(BaseModel):
    url_prefix: str | None
    update_interval: int
    support_url: str
    profile_title: str

    host_status_filter: bool

    # Rules To Seperate Clients And Send Config As Needed
    rules: list[SubRule]


class Settings(BaseModel):
    telegram: Telegram | None = None
    discord: Discord | None = None
    webhook: Webhook | None = None
    notfication_settings: NotficationSettings | None = None
    notfication_enable: NotficationEnable | None = None
    subscription: Subscription | None = None
