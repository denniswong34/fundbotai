"""Internationalization (i18n) utility for FundBot AI.

Provides a simple translation function `t()` that loads locale dictionaries
and resolves keys in dot-notation (e.g. 'auth.login_success').

Supported languages: en (English), zh_Hant (Traditional Chinese), zh_Hans (Simplified Chinese).
"""

from typing import Dict, Optional

# ── English ────────────────────────────────────────────

EN: Dict[str, Dict[str, str]] = {
    "common": {
        "welcome": "Welcome",
        "login": "Login",
        "logout": "Logout",
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "confirm": "Confirm",
        "search": "Search",
        "filter": "Filter",
        "loading": "Loading...",
        "error": "Error",
        "success": "Success",
        "warning": "Warning",
        "no_data": "No data available",
        "back": "Back",
        "next": "Next",
        "submit": "Submit",
        "reset": "Reset",
        "app_name": "FundBot AI",
    },
    "auth": {
        "login_success": "Login successful",
        "login_failed": "Invalid credentials",
        "register_success": "Account created successfully",
        "token_expired": "Session expired, please login again",
        "unauthorized": "You are not authorized to perform this action",
        "login_title": "Welcome Back",
        "login_subtitle": "Sign in to your account",
        "register_title": "Create Account",
        "email": "Email",
        "password": "Password",
        "username": "Username",
        "forgot_password": "Forgot password?",
        "no_account": "Don't have an account?",
        "have_account": "Already have an account?",
    },
    "portfolio": {
        "portfolio_created": "Portfolio created successfully",
        "portfolio_deleted": "Portfolio deleted successfully",
        "holding_added": "Holding added successfully",
        "holding_removed": "Holding removed successfully",
        "rebalance_started": "Rebalance started",
        "rebalance_completed": "Rebalance completed successfully",
        "drift_detected": "Drift detected in portfolio",
        "title": "Portfolios",
        "create": "Create Portfolio",
        "edit": "Edit Portfolio",
        "delete": "Delete Portfolio",
        "total_value": "Total Value",
        "total_pnl": "Total P&L",
        "holdings": "Holdings",
        "add_holding": "Add Holding",
        "rebalance": "Rebalance",
        "rebalance_preview": "Preview Rebalance",
        "drift": "Drift",
        "target_weight": "Target Weight",
        "current_weight": "Current Weight",
        "performance": "Performance",
    },
    "org": {
        "org_created": "Organization created successfully",
        "member_added": "Member added successfully",
        "member_removed": "Member removed successfully",
        "org_settings_updated": "Organization settings updated",
        "title": "Organization",
        "members": "Members",
        "invite": "Invite Member",
        "remove": "Remove Member",
        "role": "Role",
        "owner": "Owner",
        "admin": "Admin",
        "member": "Member",
    },
    "broker": {
        "connection_created": "Broker connection created successfully",
        "connection_tested": "Connection tested successfully",
        "connection_failed": "Connection test failed",
    },
    "error": {
        "not_found": "Resource not found",
        "already_exists": "Resource already exists",
        "permission_denied": "Permission denied",
        "validation_error": "Validation error",
        "internal_error": "Internal server error",
    },
    "nav": {
        "dashboard": "Dashboard",
        "portfolios": "Portfolios",
        "brokers": "Brokers",
        "performance": "Performance",
        "settings": "Settings",
        "org_admin": "Organization",
    },
    "settings": {
        "title": "Settings",
        "language": "Language",
        "theme": "Theme",
        "dark": "Dark",
        "light": "Light",
        "timezone": "Timezone",
        "telegram": "Telegram Notifications",
    },
}

# ── Traditional Chinese (繁體中文) ───────────────────────

ZH_HANT: Dict[str, Dict[str, str]] = {
    "common": {
        "welcome": "歡迎",
        "login": "登入",
        "logout": "登出",
        "save": "儲存",
        "cancel": "取消",
        "delete": "刪除",
        "confirm": "確認",
        "search": "搜尋",
        "filter": "篩選",
        "loading": "載入中...",
        "error": "錯誤",
        "success": "成功",
        "warning": "警告",
        "no_data": "無可用資料",
        "back": "返回",
        "next": "下一步",
        "submit": "提交",
        "reset": "重置",
        "app_name": "FundBot AI",
    },
    "auth": {
        "login_success": "登入成功",
        "login_failed": "帳號或密碼錯誤",
        "register_success": "帳號建立成功",
        "token_expired": "會話已過期，請重新登入",
        "unauthorized": "您無權執行此操作",
        "login_title": "歡迎回來",
        "login_subtitle": "登入您的帳戶",
        "register_title": "建立帳戶",
        "email": "電子郵件",
        "password": "密碼",
        "username": "使用者名稱",
        "forgot_password": "忘記密碼？",
        "no_account": "還沒有帳戶？",
        "have_account": "已經有帳戶？",
    },
    "portfolio": {
        "portfolio_created": "投資組合建立成功",
        "portfolio_deleted": "投資組合刪除成功",
        "holding_added": "持股新增成功",
        "holding_removed": "持股移除成功",
        "rebalance_started": "再平衡已開始",
        "rebalance_completed": "再平衡完成成功",
        "drift_detected": "偵測到投資組合偏離",
        "title": "投資組合",
        "create": "建立投資組合",
        "edit": "編輯投資組合",
        "delete": "刪除投資組合",
        "total_value": "總價值",
        "total_pnl": "總損益",
        "holdings": "持股",
        "add_holding": "新增持股",
        "rebalance": "再平衡",
        "rebalance_preview": "預覽再平衡",
        "drift": "偏離",
        "target_weight": "目標權重",
        "current_weight": "目前權重",
        "performance": "績效",
    },
    "org": {
        "org_created": "組織建立成功",
        "member_added": "成員新增成功",
        "member_removed": "成員移除成功",
        "org_settings_updated": "組織設定已更新",
        "title": "組織",
        "members": "成員",
        "invite": "邀請成員",
        "remove": "移除成員",
        "role": "角色",
        "owner": "擁有者",
        "admin": "管理員",
        "member": "成員",
    },
    "broker": {
        "connection_created": "經紀商連線建立成功",
        "connection_tested": "連線測試成功",
        "connection_failed": "連線測試失敗",
    },
    "error": {
        "not_found": "找不到資源",
        "already_exists": "資源已存在",
        "permission_denied": "權限不足",
        "validation_error": "驗證錯誤",
        "internal_error": "伺服器內部錯誤",
    },
    "nav": {
        "dashboard": "儀表板",
        "portfolios": "投資組合",
        "brokers": "經紀商",
        "performance": "績效",
        "settings": "設定",
        "org_admin": "組織管理",
    },
    "settings": {
        "title": "設定",
        "language": "語言",
        "theme": "主題",
        "dark": "深色",
        "light": "淺色",
        "timezone": "時區",
        "telegram": "Telegram 通知",
    },
}

# ── Simplified Chinese (简体中文) ────────────────────────

ZH_HANS: Dict[str, Dict[str, str]] = {
    "common": {
        "welcome": "欢迎",
        "login": "登录",
        "logout": "登出",
        "save": "保存",
        "cancel": "取消",
        "delete": "删除",
        "confirm": "确认",
        "search": "搜索",
        "filter": "筛选",
        "loading": "加载中...",
        "error": "错误",
        "success": "成功",
        "warning": "警告",
        "no_data": "无可用数据",
        "back": "返回",
        "next": "下一步",
        "submit": "提交",
        "reset": "重置",
        "app_name": "FundBot AI",
    },
    "auth": {
        "login_success": "登录成功",
        "login_failed": "账号或密码错误",
        "register_success": "账号创建成功",
        "token_expired": "会话已过期，请重新登录",
        "unauthorized": "您无权执行此操作",
        "login_title": "欢迎回来",
        "login_subtitle": "登录您的账户",
        "register_title": "创建账户",
        "email": "电子邮件",
        "password": "密码",
        "username": "用户名",
        "forgot_password": "忘记密码？",
        "no_account": "还没有账户？",
        "have_account": "已经有账户？",
    },
    "portfolio": {
        "portfolio_created": "投资组合创建成功",
        "portfolio_deleted": "投资组合删除成功",
        "holding_added": "持股添加成功",
        "holding_removed": "持股移除成功",
        "rebalance_started": "再平衡已开始",
        "rebalance_completed": "再平衡完成成功",
        "drift_detected": "检测到投资组合偏离",
        "title": "投资组合",
        "create": "创建投资组合",
        "edit": "编辑投资组合",
        "delete": "删除投资组合",
        "total_value": "总价值",
        "total_pnl": "总损益",
        "holdings": "持股",
        "add_holding": "添加持股",
        "rebalance": "再平衡",
        "rebalance_preview": "预览再平衡",
        "drift": "偏离",
        "target_weight": "目标权重",
        "current_weight": "当前权重",
        "performance": "绩效",
    },
    "org": {
        "org_created": "组织创建成功",
        "member_added": "成员添加成功",
        "member_removed": "成员移除成功",
        "org_settings_updated": "组织设置已更新",
        "title": "组织",
        "members": "成员",
        "invite": "邀请成员",
        "remove": "移除成员",
        "role": "角色",
        "owner": "拥有者",
        "admin": "管理员",
        "member": "成员",
    },
    "broker": {
        "connection_created": "经纪商连接创建成功",
        "connection_tested": "连接测试成功",
        "connection_failed": "连接测试失败",
    },
    "error": {
        "not_found": "找不到资源",
        "already_exists": "资源已存在",
        "permission_denied": "权限不足",
        "validation_error": "验证错误",
        "internal_error": "服务器内部错误",
    },
    "nav": {
        "dashboard": "仪表板",
        "portfolios": "投资组合",
        "brokers": "经纪商",
        "performance": "绩效",
        "settings": "设置",
        "org_admin": "组织管理",
    },
    "settings": {
        "title": "设置",
        "language": "语言",
        "theme": "主题",
        "dark": "深色",
        "light": "浅色",
        "timezone": "时区",
        "telegram": "Telegram 通知",
    },
}

# ── Translation registry ────────────────────────────────

_LOCALES: Dict[str, Dict[str, Dict[str, str]]] = {
    "en": EN,
    "zh_Hant": ZH_HANT,
    "zh_Hans": ZH_HANS,
}

_DEFAULT_LOCALE = "en"


def load_translations() -> None:
    """Pre-load translations into memory. Called during app startup."""
    # Already loaded as module-level dicts; this function exists for
    # explicit startup logging or future lazy-loading from files.
    pass


def t(key: str, lang: str = _DEFAULT_LOCALE) -> str:
    """Translate a dot-notation key into the target language.

    Usage:
        t('auth.login_success', lang='zh_Hant')  → "登入成功"
        t('common.welcome')                       → "Welcome"

    Falls back to English, then to the raw key if not found.
    """
    locale = _LOCALES.get(lang, _LOCALES[_DEFAULT_LOCALE])
    parts = key.split(".")
    module = parts[0]
    sub_key = parts[1] if len(parts) > 1 else None

    if sub_key:
        value = locale.get(module, {}).get(sub_key)
        if value is not None:
            return value
        # Fallback to English
        value = _LOCALES[_DEFAULT_LOCALE].get(module, {}).get(sub_key)
        if value is not None:
            return value
    else:
        value = locale.get(module)
        if value is not None:
            return str(value)

    return key


def available_languages() -> Dict[str, str]:
    """Return a dict of language code → display name."""
    return {
        "en": "English",
        "zh_Hant": "繁體中文",
        "zh_Hans": "简体中文",
    }
