from telebot import types


class InlineKeyboardPaginator:
    SEPARATOR = '%*%/%'

    def __init__(self, buttons_content: [str], buttons_per_page: int, callback_prefix):
        """
            Prefix shouldn't contain sequence of SEPARATOR, it used to split content
        """

        self._content = buttons_content
        self._amount_per_page = buttons_per_page
        self._buttons_size = len(buttons_content)
        self._amount_of_pages = self._buttons_size // buttons_per_page + (self._buttons_size % buttons_per_page > 0)
        self._callback_prefix = callback_prefix

    def get(self, page: int) -> types.InlineKeyboardMarkup:
        if page >= self._amount_of_pages:
            raise IndexError

        keyboard = types.InlineKeyboardMarkup()
        buttons = []
        if page > 0:
            buttons.append(types.InlineKeyboardButton(text='<',
                                                      callback_data=self._callback_prefix + self.SEPARATOR + 'Page' +
                                                                    self.SEPARATOR + str(page - 1)))
        button_begin_index = self._amount_per_page * page
        button_end_index = self._amount_per_page * (page + 1) if \
            self._amount_per_page * (page + 1) <= self._buttons_size else self._buttons_size
        buttons.extend(([types.InlineKeyboardButton(text=x, callback_data=self._callback_prefix + self.SEPARATOR + x)
                         for x in self._content[button_begin_index: button_end_index]]))
        if page < self._amount_of_pages - 1:
            buttons.append(types.InlineKeyboardButton(text='>',
                                                      callback_data=self._callback_prefix + self.SEPARATOR + 'Page' +
                                                                    self.SEPARATOR + str(page + 1)))
        keyboard.row(*buttons)
        return keyboard

    def corresponds_to_keyboard(self, data: str) -> bool:
        return self._callback_prefix in data

    def get_content(self, data) -> (True, str) or (False, int):
        """"
            Returns tuple with True and content from query data in case of matching to provided content
            Returns tuple with False and number of page to use in case of page switching
            raise Exception in case of incorrect prefix
        """
        if not self.corresponds_to_keyboard(data):
            raise Exception
        params = data.split(self.SEPARATOR)
        if "Page" in params:
            return False, int(params[2])
        return True, params[1]
