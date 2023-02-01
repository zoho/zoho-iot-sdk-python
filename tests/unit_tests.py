import unittest
from zoho_iot_sdk import ZohoIoTClient


class MainTestCases(unittest.TestCase):
    def setUp(self):
        self.ZohoIoTClient = ZohoIoTClient("Shahul")

    def test_print(self):

        result = self.ZohoIoTClient.print("Mr. ")
        self.assertEqual(result, "Mr. Shahul")


if __name__ == '__main__':
    unittest.main()
