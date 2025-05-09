from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, field_validator

from .validators import ProxyValidator, DiscordValidator, ListValidator


class Telegram(BaseModel):
    enable: bool
    token: str | None
    webhook_url: str | None
    webhook_secret: str | None

    proxy_url: str | None

    @field_validator("proxy_url")
    @classmethod
    def validate_proxy_url(cls, v):
        return ProxyValidator.validate_proxy_url(v)


class Discord(BaseModel):
    enable: bool
    token: str | None

    proxy_url: str | None

    @field_validator("proxy_url")
    @classmethod
    def validate_proxy_url(cls, v):
        return ProxyValidator.validate_proxy_url(v)


class WebhookInfo(BaseModel):
    url: HttpUrl
    secret: str


class Webhook(BaseModel):
    enable: bool
    webhooks: list[WebhookInfo]
    days_left: list[int]
    usage_percent: list[int]
    timeout: int = Field(gt=1)
    recurrent: int = Field(gt=1)

    proxy_url: str | None

    @field_validator("proxy_url", mode="before")
    @classmethod
    def validate_proxy_url(cls, v):
        return ProxyValidator.validate_proxy_url(v)

    @field_validator("days_left", "usage_percent", mode="before")
    @classmethod
    def validate_lists(cls, v):
        return ListValidator.not_null_list(v, "list")


class NotficationSettings(BaseModel):
    # Define Which Notfication System Work's
    notify_telegram: bool
    notify_discord: bool

    # Telegram Settings
    telegram_api_token: str | None
    telegram_admin_id: int | None
    telegram_channel_id: int | None
    telegram_topic_id: int | None

    # Discord Settings
    discord_webhook_url: str | None

    # Proxy Settings
    proxy_url: str | None

    max_retries: int = Field(gt=1)

    @field_validator("proxy_url", mode="before")
    @classmethod
    def validate_proxy_url(cls, v):
        return ProxyValidator.validate_proxy_url(v)

    @field_validator("discord_webhook_url", mode="before")
    @classmethod
    def validate_discord_webhook(cls, value):
        return DiscordValidator.validate_webhook(value)


class NotficationEnable(BaseModel):
    admin: bool = Field(default=True)
    core: bool = Field(default=True)
    group: bool = Field(default=True)
    host: bool = Field(default=True)
    login: bool = Field(default=True)
    node: bool = Field(default=True)
    user: bool = Field(default=True)
    user_template: bool = Field(default=True)
    days_left: bool = Field(default=True)
    percentage_reached: bool = Field(default=True)


class ConfigFormat(str, Enum):
    links = "links"
    links_base64 = "links_base64"
    xray = "xray"
    sing_box = "sing_box"
    clash = "clash"
    clash_meta = "clash_meta"
    outline = "outline"
    block = "block"


class SubRule(BaseModel):
    pattern: str
    target: ConfigFormat


class SubFormatEnable(BaseModel):
    links: bool = Field(default=True)
    links_base64: bool = Field(default=True)
    xray: bool = Field(default=True)
    sing_box: bool = Field(default=True)
    clash: bool = Field(default=True)
    clash_meta: bool = Field(default=True)
    outline: bool = Field(default=True)


class Subscription(BaseModel):
    url_prefix: str = ""
    update_interval: int
    support_url: str
    profile_title: str

    host_status_filter: bool

    # Rules To Seperate Clients And Send Config As Needed
    rules: list[SubRule]
    manual_sub_request: SubFormatEnable = Field(default_factory=SubFormatEnable)


class SettingsSchema(BaseModel):
    telegram: Telegram | None = None
    discord: Discord | None = None
    webhook: Webhook | None = None
    notfication_settings: NotficationSettings = Field(default_factory=NotficationSettings)
    notfication_enable: NotficationEnable = Field(default_factory=NotficationEnable)
    subscription: Subscription = Field(default_factory=Subscription)
