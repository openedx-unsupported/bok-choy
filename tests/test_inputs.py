"""
Test basic HTML form input interactions.
"""
from __future__ import absolute_import

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
        assert button.output == 'button was clicked'

    def test_textfield(self):
        text_field = TextFieldPage(self.browser)
        text_field.visit()
        text_field.enter_text('Lorem ipsum')
        assert text_field.output == 'Lorem ipsum'

    def test_select(self):
        select = SelectPage(self.browser)
        select.visit()
        select.select_car('fiat')
        assert select.output == 'Fiat'
        self.assertTrue(select.is_car_selected('fiat'))
        self.assertFalse(select.is_car_selected('saab'))
        self.assertFalse(select.is_car_selected('sedan'))

    def test_checkbox(self):
        checkbox = CheckboxPage(self.browser)
        checkbox.visit()
        checkbox.toggle_pill('red')
        assert checkbox.output == 'red'
