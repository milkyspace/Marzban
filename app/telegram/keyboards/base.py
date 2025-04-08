from aiogram.utils.keyboard import ReplyKeyboardBuilder


class Cancelkeyboard(ReplyKeyboardBuilder):
    cancel = "❌ cancel"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.button(text=self.cancel)
        self.adjust(1, 1)
