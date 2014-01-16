"""
Test basic HTML form input interactions.
"""

from bok_choy.web_app_test import WebAppTest
from nose.tools import assert_equal
from .pages import ButtonPage, TextFieldPage, SelectPage, CheckboxPage


class InputTest(WebAppTest):
    """
    Test basic HTML form input interactions.
    """

    def test_button(self):
        button = ButtonPage(self.ui)
        button.visit()
        button.click_button()
        assert_equal(button.output, 'button was clicked')

    def test_textfield(self):
        text_field = TextFieldPage(self.ui)
        text_field.visit()
        text_field.enter_text('Lorem ipsum')
        assert_equal(text_field.output, 'Lorem ipsum')

    def test_select(self):
        select = SelectPage(self.ui)
        select.visit()
        select.select_car('fiat')
        assert_equal(select.output, 'Fiat')

    def test_checkbox(self):
        checkbox = CheckboxPage(self.ui)
        checkbox.visit()
        checkbox.toggle_pill('red')
        assert_equal(checkbox.output, 'red')
