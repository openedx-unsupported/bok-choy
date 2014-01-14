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

    page_object_classes = [ButtonPage, TextFieldPage, SelectPage, CheckboxPage]

    def test_button(self):
        self.ui.visit('button')
        self.ui['button'].click_button()
        assert_equal(self.ui['button'].output, 'button was clicked')

    def test_textfield(self):
        self.ui.visit('text_field')
        self.ui['text_field'].enter_text('Lorem ipsum')
        assert_equal(self.ui['text_field'].output, 'Lorem ipsum')

    def test_select(self):
        self.ui.visit('select')
        self.ui['select'].select_car('fiat')
        assert_equal(self.ui['select'].output, 'Fiat')

    def test_checkbox(self):
        self.ui.visit('checkbox')
        self.ui['checkbox'].toggle_pill('red')
        assert_equal(self.ui['checkbox'].output, 'red')
