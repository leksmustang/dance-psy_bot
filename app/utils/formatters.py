import html

def safe_username(user) -> str:
    if user.username:
        return f"@{html.escape(user.username)}"
    return "пользователь"

def escape_html(text: str) -> str:
    return html.escape(text)