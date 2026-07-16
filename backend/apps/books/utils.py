from pathlib import Path
from django.conf import settings

class BookContentError(Exception):
    pass

def content_path(book):
    value = book.content_file_path
    if not value: raise BookContentError('本书暂无阅读内容')
    relative = Path(value)
    root = Path(settings.MEDIA_ROOT).resolve()
    if relative.is_absolute() or '..' in relative.parts: raise BookContentError('阅读内容路径非法')
    path = (root / relative).resolve()
    if path != root and root not in path.parents: raise BookContentError('阅读内容路径非法')
    if not path.is_file(): raise BookContentError('阅读内容文件不存在')
    return path

def get_book_content(book):
    try:
        path = content_path(book)
        content = path.read_text(encoding='utf-8-sig')
    except (BookContentError, OSError, UnicodeError):
        raise BookContentError('阅读内容不可用')
    if not content: raise BookContentError('阅读内容为空')
    return content

def has_readable_content(book):
    try:
        path = content_path(book)
        if path.stat().st_size == 0: return False
        with path.open('r', encoding='utf-8-sig') as handle:
            return bool(handle.read(1))
    except (BookContentError, OSError, UnicodeError):
        return False

def get_preview_content(book, preview_percent=10):
    full = get_book_content(book); total = len(full)
    length = min(total, max(10, int(total * preview_percent / 100)))
    preview = full[:length]
    return preview, total, len(preview)
