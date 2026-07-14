"""Chinese descriptions for env vars shown in the Web Keys page.

Loaded from ``env_descriptions_zh.yaml`` beside this module.  Used when
``display.language`` is ``zh`` (or ``zh-hant`` for now shares zh catalog).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_ZH_FILE = Path(__file__).with_name("env_descriptions_zh.yaml")

# web_server._MESSAGING_ENV_FALLBACKS entries not in OPTIONAL_ENV_VARS
_MESSAGING_FALLBACK_ZH: dict[str, str] = {
    "SIGNAL_HTTP_URL": "signal-cli REST API 基础 URL，如 http://127.0.0.1:8080",
    "SIGNAL_ACCOUNT": "已在网桥注册的 Signal 账号电话号码",
    "SIGNAL_ALLOWED_USERS": "允许使用机器人的 Signal 用户（逗号分隔）",
    "WHATSAPP_ENABLED": "启用 WhatsApp 网关适配器",
    "WHATSAPP_MODE": "WhatsApp 网桥模式",
    "WHATSAPP_ALLOWED_USERS": "允许使用机器人的 WhatsApp 用户（逗号分隔）",
    "EMAIL_ADDRESS": "收发邮件使用的邮箱地址",
    "EMAIL_PASSWORD": "邮箱密码或应用专用密码",
    "EMAIL_IMAP_HOST": "IMAP 服务器主机（如 imap.gmail.com）",
    "EMAIL_SMTP_HOST": "SMTP 服务器主机（如 smtp.gmail.com）",
    "TWILIO_ACCOUNT_SID": "Twilio Account SID",
    "TWILIO_AUTH_TOKEN": "Twilio Auth Token",
    "WECOM_BOT_ID": "企业微信群机器人 ID",
    "WECOM_SECRET": "企业微信群机器人密钥",
    "WECOM_CALLBACK_CORP_ID": "企业微信 Corp ID",
    "WECOM_CALLBACK_CORP_SECRET": "企业微信应用 Corp Secret",
    "WECOM_CALLBACK_AGENT_ID": "企业微信应用 Agent ID",
    "WECOM_CALLBACK_TOKEN": "企业微信回调验证 Token",
    "WECOM_CALLBACK_ENCODING_AES_KEY": "企业微信回调 AES 加密密钥",
    "WEIXIN_ACCOUNT_ID": "通过 lenlion gateway setup 扫码登录获得的 iLink Bot 账号 ID",
    "WEIXIN_TOKEN": "通过 lenlion gateway setup 扫码登录获得的 iLink Bot 令牌",
    "WEIXIN_BASE_URL": "扫码登录保存的 iLink API 基础 URL（默认 https://ilinkai.weixin.qq.com）",
    "FEISHU_APP_ID": "飞书 / Lark 应用 ID",
    "FEISHU_APP_SECRET": "飞书 / Lark 应用密钥",
    "FEISHU_ENCRYPT_KEY": "飞书 / Lark 加密密钥",
    "FEISHU_VERIFICATION_TOKEN": "飞书 / Lark 验证令牌",
    "DINGTALK_CLIENT_ID": "钉钉 Client ID（AppKey）",
    "DINGTALK_CLIENT_SECRET": "钉钉 Client Secret（AppSecret）",
}


@lru_cache(maxsize=1)
def _load_zh_catalog() -> dict[str, str]:
    if not _ZH_FILE.is_file():
        return {}
    with _ZH_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return {}
    merged = {str(k): str(v) for k, v in data.items()}
    merged.update(_MESSAGING_FALLBACK_ZH)
    return merged


def _normalize_lang(lang: str | None) -> str:
    if not lang:
        return "en"
    lang = lang.strip().lower().replace("_", "-")
    if lang.startswith("zh"):
        return "zh"
    return lang


def localize_env_description(
    var_name: str,
    english_description: str,
    *,
    lang: str | None = None,
) -> str:
    """Return a localized env-var description for the Web UI."""
    if _normalize_lang(lang) != "zh":
        return english_description
    catalog = _load_zh_catalog()
    return catalog.get(var_name) or _MESSAGING_FALLBACK_ZH.get(var_name) or english_description


def localize_env_entry(
    var_name: str,
    info: dict[str, Any],
    *,
    lang: str | None = None,
) -> dict[str, Any]:
    """Return a copy of an env info dict with localized description."""
    if _normalize_lang(lang) == "en":
        return info
    out = dict(info)
    out["description"] = localize_env_description(
        var_name,
        str(info.get("description") or ""),
        lang=lang,
    )
    return out
