from unittest import TestCase

from utils.tenhou.helper import parse_names_from_tenhou_chat_message


class TenhouCalculatorTestCase(TestCase):
    def test_parse_end_game_message_from_tenhou_chat(self):
        message = (
            "#END %D0%93%D0%BE%D0%B3%D0%BE%D0%BB%D1%8C(%2B43.0) "
            "%D0%91%D0%BB%D0%BE%D0%BA(%2B18.0) "
            "%D0%9D%D0%B5%D0%BA%D1%80%D0%B0%D1%81%D0%BE%D0%B2(-22.0) "
            "%D0%A2%D0%BE%D0%BB%D1%81%D1%82%D0%BE%D0%B9(-39.0) "
        )
        result = parse_names_from_tenhou_chat_message(message)
        self.assertEqual(result, ["Гоголь", "Блок", "Некрасов", "Толстой"])
