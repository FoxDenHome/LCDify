from drivers.paged import PagedLCDDriver

class LCDPage():
    should_run: bool
    driver: PagedLCDDriver
    formatted_title: str
    title: str

    def __init__(self, config, driver: PagedLCDDriver, default_title: str = "UNTITLED"):
        self.driver = driver
        self.title = default_title
        if "title" in config:
            self.title = config["title"]
        self.should_run = False
        self.formatted_title = None

    def is_current(self) -> bool:
        return self.driver.pages[self.driver.current_page] == self

    def do_render_if_current(self) -> None:
        if self.is_current():
            self.driver.do_render()

    def start(self):
        self.should_run = True
        self.formatted_title = self.format_text_center(self.title, "=")

    def stop(self):
        self.should_run = False

    def render(self) -> None:
        self.driver.set_line(0, self.formatted_title)

    def format_text_center(self, text: str, pad_char: str) -> str:
        text_len = len(text)
        if text_len > self.driver.lcd_width:
            raise ValueError("Title too long")
        
        if text_len == self.driver.lcd_width:
            return text

        if (text_len % 2) != (self.driver.lcd_width % 2):
            if " " in text:
                center_space = -1
                center_idx = text_len / 2
                center_offset = 0.5
                while center_offset < text_len:
                    idx = round(center_idx + center_offset)
                    if text[idx] == " ":
                        center_space = idx
                        break
                    idx = center_idx - center_offset
                    if text[idx] == " ":
                        center_space = idx
                        break
                    center_offset += 1
                assert(center_space >= 0)
                text = text[:center_space] + " " + text[center_space:]
            else:
                text = f"{text} "

        text_len = len(text)
        if text_len == self.driver.lcd_width:
            return text

        text = f" {text} "
        text_len = len(text)
        if text_len == self.driver.lcd_width:
            return text

        equal_signs = (self.driver.lcd_width - text_len) // 2
        return f"{pad_char * equal_signs}{text}{pad_char * equal_signs}"
