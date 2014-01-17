"""
Test basic HTML form input interactions.
"""

from bok_choy.web_app_test import WebAppTest
from .pages import ButtonPage, TextFieldPage, SelectPage, CheckboxPage


class InputTest(WebAppTest):
    """
    Test basic HTML form input interactions.
    """

    def test_button(self):
        button = ButtonPage(self.browser)
        button.visit()
        button.click_button()
        self.assertEquals(button.output, 'button was clicked')

    def test_textfield(self):
        text_field = TextFieldPage(self.browser)
        text_field.visit()
        text_field.enter_text('Lorem ipsum')
        self.assertEquals(text_field.output, 'Lorem ipsum')

    def test_select(self):
        select = SelectPage(self.browser)
        select.visit()
        select.select_car('fiat')
        self.assertEquals(select.output, 'Fiat')

    def test_checkbox(self):
        checkbox = CheckboxPage(self.browser)
        checkbox.visit()
        checkbox.toggle_pill('red')
        self.assertEquals(checkbox.output, 'red')
