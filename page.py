from driver import LCDDriver

def format_title(title: str, width: int) -> str:
    title_len = len(title)
    if title_len > width:
        raise ValueError("Title too long")
    
    if title_len == width:
        return title
    
    if title_len == width - 1:
        return f"{title} "

    title = f" {title} "
    title_len = len(title)
    if title_len == width:
        return title

    width_diff = width - title_len
    equal_signs = width_diff // 2
    if width_diff % 2:
        title = f" {title}"
    return f"{'=' * equal_signs}{title}{'=' * equal_signs}"

class LCDPage():
    def __init__(self, config, default_title: str = "UNTITLED"):
        self.title = default_title
        if "title" in config:
            self.title = config["title"]

    def render(self, driver: LCDDriver) -> None:
        driver.set_line(0, format_title(self.title, driver.lcd_width))
