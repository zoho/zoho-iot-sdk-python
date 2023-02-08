from zoho_iot_sdk import ZohoIoTClient
from zoho_iot_sdk.Utils import Utils
from unittest.mock import patch

import unittest


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.ZohoIoTClient = ZohoIoTClient()

    def tearDown(self):
        self.ZohoIoTClient = None

    def test_is_blank_should_return_true_for_empty_string(self):
        self.assertEqual(Utils.is_blank(""), True)

    @patch('zoho_iot_sdk.Utils.is_blank', return_value=False)
    def test_is_blank_should_return_false_for_empty_string(self):
        self.assertEqual(Utils.is_blank(""), False)
