import unittest
import json
from os.path import exists
import threading
from unittest import mock
import logging
from zoho_iot_sdk.ZohoIoTClient import ZohoIoTClient
from zoho_iot_sdk.MqttConstants import TransactionStatus, ClientStatus, CommandAckResponseCodes, ConfigAckResponseCodes, DEFAULT_PAYLOAD_SIZE, MAXIMUM_PAYLOAD_SIZE, MIN_RETRY_DELAY, MAX_RETRY_DELAY
import paho.mqtt.client as mqtt_client
from unittest.mock import patch

client = ZohoIoTClient()
non_tls_client = ZohoIoTClient()
tls_client = ZohoIoTClient(secure_connection=True)
tls_client_certificat = ZohoIoTClient(secure_connection=True,use_client_certificates=True)

logger = logging.getLogger(__name__)
sample_data = {"key1":"value1","key2":22}
payload_size_mb = 1
payload_size_bytes = payload_size_mb * 1024 * 1024
sample_data_2 = {
    "key1": "value1",
    "key2": ["item1", "item2", "item3"],
    "key3": {"subkey1": 42, "subkey2": "data"},
}
repeated_data = [sample_data_2] * (payload_size_bytes // len(json.dumps(sample_data_2)))
payload1 = {"out": repeated_data}
max_payload = json.dumps(payload1)
def test():
    pass

class MainTestCases(unittest.TestCase):

    def test_enable_logger(self):

        self.assertFalse(client.enable_logger())
        self.assertTrue(client.enable_logger(logger))
        self.assertTrue(client.enable_logger(logger,"logfile.txt"))
            
    #is_blank
    def test_is_blank_without_arguments(self):

        with self.assertRaises(TypeError):
            client.is_blank()
    
    def test_is_blank_with_None_l_argumnts(self):
        
        self.assertTrue(client.is_blank(None))
        self.assertTrue(client.is_blank(""))
        
    def test_is_blank_with_proper_arguments_should_return_false(self):
        
        self.assertFalse(client.is_blank("proper argument"))


    #extract_host_name_and_client_id()
    def test_extract_host_name_and_client_id_with_proper_argument_should_return_true(self):

        self.assertTrue(client.extract_host_name_and_client_id("/___/___/USER_NAME/___/___"))

    def test_extract_host_name_and_client_id_with_invalid_argument_should_return_false(self):

        self.assertFalse(client.extract_host_name_and_client_id("invalid argument"))

    #int()
    #non_tls
    def test_init_non_tls_mode_with_proper_arguments_should_success(self):
        
        result = non_tls_client.init("/___/___/USER_NAME/___/___","password")
        self.assertEqual(result,0)

    def test_init_non_tls_mode_with_improper_arguments_should_fail(self):
        
        result = non_tls_client.init(None,None)
        self.assertEqual(result,-1)
        result = non_tls_client.init(None,"password")
        self.assertEqual(result,-1)
        result = non_tls_client.init("/___/___/USER_NAME/___/___",None)
        self.assertEqual(result,-1)
        result = non_tls_client.init("invalid argument","password")
        self.assertEqual(result,-1)
        result = non_tls_client.init("/___/___/USER_NAME/___/___")
        self.assertEqual(result,-1)

    def test_init_non_tls_mode_with_no_arguments_should_raise_error(self):

        with self.assertRaises(TypeError):
            non_tls_client.init()

    #tls
    @patch('zoho_iot_sdk.ZohoIoTClient.exists', return_value=True)
    def test_init_tls_mode_with_proper_arguments_should_success(self,mock_exists):

        result = tls_client.init("/___/___/USER_NAME/___/___","password",ca_certificate = "path/to/root_ca")
        self.assertEqual(result,0)


    def test_init_tls_mode_with_improper_arguments_should_fail(self):

        result = tls_client.init(None,None,None)
        self.assertEqual(result,-1)
        result = tls_client.init("","","")
        self.assertEqual(result,-1)
        result = tls_client.init("/___/___/USER_NAME/___/___","password","")
        self.assertEqual(result,-1)
        result = tls_client.init("invalid argument","password","path/to/root_ca")
        self.assertEqual(result,-1)
        result = tls_client.init("/___/___/USER_NAME/___/___","","path/to/root_ca")
        self.assertEqual(result,-1)
        result = tls_client.init("/___/___/USER_NAME/___/___",None,"path/to/root_ca")
        self.assertEqual(result,-1)
        result = tls_client.init("/___/___/USER_NAME/___/___","password")
        self.assertEqual(result,-1)
        result = tls_client.init("/___/___/USER_NAME/___/___")
        self.assertEqual(result,-1)

    def test_init_tls_mode_with_no_arguments_should_raise_error(self):

        with self.assertRaises(TypeError):
            tls_client.init(mqtt_password="password",ca_certificate = "path/to/root_ca")

    #tls_client_certificate_mode
    @patch('zoho_iot_sdk.ZohoIoTClient.exists', return_value=True)
    def test_int_tls_client_certificate_mode_with_proper_arguments_should_success(self,mock_exists):

        result = tls_client_certificat.init("/___/___/USER_NAME/___/___","password",ca_certificate="path/to/root_ca",client_certificate="path/to/client_certificate",private_key="path/to/private_key")
        self.assertEqual(result,0)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___",ca_certificate="path/to/root_ca",client_certificate="path/to/client_certificate",private_key="path/to/private_key")
        self.assertEqual(result,0)

    def test_init_tls_client_certificate_mode_with_improper_arguments_should_fail(self):
        
        result = tls_client_certificat.init(None)
        self.assertEqual(result,-1)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___",ca_certificate="path/to/root_ca",client_certificate="path/to/client_certificate",private_key="path/to/private_key")
        self.assertEqual(result,-1)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___",ca_certificate="path/to/root_ca",client_certificate="path/to/client_certificate")
        self.assertEqual(result,-1)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___",ca_certificate="path/to/root_ca",private_key="path/to/private_key")
        self.assertEqual(result,-1)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___",client_certificate="path/to/client_certificate",private_key="path/to/private_key")
        self.assertEqual(result,-1)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___",ca_certificate="path/to/root_ca")
        self.assertEqual(result,-1)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___",private_key="path/to/private_key")
        self.assertEqual(result,-1)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___",client_certificate="path/to/client_certificate")
        self.assertEqual(result,-1)
        result = tls_client_certificat.init(mqtt_user_name="/___/___/USER_NAME/___/___")
        self.assertEqual(result,-1)

    def test_init_tls_client_certificate_mode_mode_with_no_arguments_should_raise_error(self):

        with self.assertRaises(TypeError):
            tls_client_certificat.init(ca_certificate="path/to/root_ca",client_certificate="path/to/client_certificate",private_key="path/to/private_key")
        
    #add_data_point()
    def test_add_datapoint_with_proper_argument_should_suceess(self):

        result = client.add_data_point("key","value")
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["key"],"value")

        result = client.add_data_point("key","")
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["key"],"")

        result = client.add_data_point("key",None)
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["key"],None)

        result = client.add_data_point("key","value",asset_name="asser_name")
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["asser_name"]["key"],"value")
        
        result = client.add_data_point("key",222,asset_name="asser_name")
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["asser_name"]["key"],222)

        result = client.add_data_point("key",222,asset_name="")
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["key"],222)

    def test_add_datapoint_with_improper_argument_should_fail(self):
        result = client.add_data_point("","value")
        self.assertEqual(result,-1)

        result = client.add_data_point(None,"value",)
        self.assertEqual(result,-1)

    def test_add_datapoint_with_no_argument_should_raise_error(self):
        
        with self.assertRaises(TypeError):
            client.add_data_point(key="key")

        with self.assertRaises(TypeError):
            client.add_data_point(value="value")

        with self.assertRaises(TypeError):
            client.add_data_point()

    #mark_data_point_as_error()
    def test_mark_data_point_as_error_with_proper_argument_should_success(self):

        result = client.mark_data_point_as_error("key")
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["key"],"<ERROR>")

        result = client.mark_data_point_as_error("key","assert_name")
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["assert_name"]["key"],"<ERROR>")

        result = client.mark_data_point_as_error("key","")
        self.assertEqual(result,0)

        result = client.mark_data_point_as_error("key",None)
        self.assertEqual(result,0)

    def test_mark_data_point_as_error_with_improper_argument_should_fail(self):

        result = client.mark_data_point_as_error("")
        self.assertEqual(result,-1)

        result = client.mark_data_point_as_error(None)
        self.assertEqual(result,-1)

    def test_mark_data_point_as_error_with_no_argument_should_raise_error(self):
        
        with self.assertRaises(TypeError):
            client.mark_data_point_as_error()

        with self.assertRaises(TypeError):
            client.mark_data_point_as_error(asset_name="key")

    #def add_json()
    def test_add_json_with_proper_argument_should_suceess(self):

        result = client.add_json("test",sample_data)
        self.assertEqual(result,0)
        self.assertEqual(client.payloadJSON["test"]["key1"],"value1")


    def test_add_json_with_improper_argument_should_fail(self):

        result = client.add_json("test",[])
        self.assertEqual(result,-1)

        result = client.add_json("test","")
        self.assertEqual(result,-1)

        result = client.add_json("",sample_data)
        self.assertEqual(result,-1)
        
        result = client.add_json(None,sample_data)
        self.assertEqual(result,-1)

        result = client.add_json(sample_data,sample_data)
        self.assertEqual(result,-1)

        result = client.add_json(22,sample_data)
        self.assertEqual(result,-1)

        
    def test_add_json_with_no_argument_should_raise_error(self):
        
        with self.assertRaises(TypeError):
            client.add_json()
        
        with self.assertRaises(TypeError):
            client.add_json(key="test")
        
        with self.assertRaises(TypeError):
            client.add_json(json_data=sample_data)
        
    #is_connected()
    def test_is_conected_return_true_if_connected(self):
        client.pahoClient = mqtt_client.Client()
        
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        mock_is_connected = patcher1.start()
        mock_is_connected.return_value = True

        result = client.is_connected()    
        self.assertTrue(result)
        assert mock_is_connected.call_count == 1
        patcher1.stop()

    def test_is_conected_return_false_if_not_connected(self):
        client.pahoClient = mqtt_client.Client()
        
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        mock_is_connected = patcher1.start()
        mock_is_connected.return_value = False

        result = client.is_connected()    
        self.assertFalse(result)
        assert mock_is_connected.call_count == 1
        patcher1.stop()

    #connect()
    def test_connect_when_already_connected_return_success(self):

        client.clientStatus = ClientStatus.CONNECTED
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        mock_is_connected = patcher1.start()
        mock_is_connected.return_value = True

        result = client.connect()
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        patcher1.stop()
        
    def test_connect_when_connection_successful_return_success(self):
        
        client.init("/___/___/USER_NAME/___/___","password")
        client.set_autoreconnect(True)
        patcher1 = mock.patch.object(mqtt_client.Client,"connect")
        patcher2 = mock.patch.object(mqtt_client.Client,"loop_start")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_connect = patcher1.start()
        mock_loop_start = patcher2.start()
        mock_wait = patcher3.start()
        client.connectResponseCode = 0
        mock_wait.return_value = True
        
        result = client.connect()
        self.assertEqual(result,0)
        assert mock_connect.call_count == 1
        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_connect_when_connection_fails_return_failure(self):

        client.init("/___/___/USER_NAME/___/___","password")
        client.set_autoreconnect(True)
        patcher1 = mock.patch.object(mqtt_client.Client,"connect")
        patcher2 = mock.patch.object(mqtt_client.Client,"loop_start")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_connect = patcher1.start()
        mock_loop_start = patcher2.start()
        mock_wait = patcher3.start()

        client.connectResponseCode = 0
        mock_wait.return_value = False

        result = client.connect()
        self.assertEqual(result,-1)
        assert mock_connect.call_count == 1
        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_connect_when_client_not_initialized_should_fail(self):
        
        client.clientStatus = ClientStatus.INITIALIZED
        result = client.connect()
        self.assertEqual(result,-1)

    #reconnect()
    def test_reconnect_with_proper_arguments_should_success(self):
        client.init("/___/___/USER_NAME/___/___","password")
        client.set_autoreconnect(False)
        patcher1 = mock.patch.object(mqtt_client.Client,"connect")
        patcher2 = mock.patch.object(mqtt_client.Client,"loop_start")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_connect = patcher1.start()
        mock_loop_start = patcher2.start()
        mock_wait = patcher3.start()

        mock_wait.return_value = True
        client.connectResponseCode = 0
        
        result = client.reconnect()
        self.assertEqual(result,0)
        assert mock_connect.call_count == 1
        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_reconnect_with_proper_arguments_resend_failed_ack_should_success(self):

        client.init("/___/___/USER_NAME/___/___","password")
        client.set_autoreconnect(False)
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"connect")
        patcher2 = mock.patch.object(mqtt_client.Client,"loop_start")
        patcher3 = mock.patch.object(threading.Event,"wait")
        patcher5 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher4 = mock.patch.object(mqtt_client.Client,"publish")
        mock_is_connected = patcher5.start()
        mock_publish = patcher4.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]

        client.connectResponseCode = 0
        mock_connect = patcher1.start()
        mock_loop_start = patcher2.start()
        mock_wait = patcher3.start()
        mock_wait.return_value = True
        
        client.failedAck ={"topic":"ack_message"}
        result = client.reconnect()
        self.assertEqual(result,0)
        assert mock_connect.call_count == 1
        patcher1.stop()
        patcher2.stop()
        patcher3.stop()
        patcher4.stop()
        patcher5.stop()

    def test_reconnect_when_auto_reconnect_is_enabled_the_calling_reconnect_should_fail(self):

        client.init("/___/___/USER_NAME/___/___","password")
        client.set_autoreconnect(True)
        
        result = client.reconnect()
        self.assertEqual(result,-1)

    #subscribe
    def test_subscribe_with_proper_arguments_should_success(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"subscribe")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_subscribe = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_subscribe.return_value = [0]
        mock_wait.return_value = True
        client.clientStatus = ClientStatus.CONNECTED

        client.subscriptionTopicsList = ["topic1","topic2"]
        result = client.subscribe(["topic1","topic2"])

        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_subscribe.call_count == 2
        assert mock_wait.call_count == 2

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_subscribe_with_improper_arguments_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"subscribe")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_subscribe = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_subscribe.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.subscriptionTopicsList = ["topic1","topic2"]
        result = client.subscribe(None)
        self.assertEqual(result,-1)

        result = client.subscribe([])
        self.assertEqual(result,-1)

        result = client.subscribe(["topic3"]) #topic3 not in subscriptionTopicsList
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_subscribe_when_client_not_connected_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"subscribe")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_subscribe = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_subscribe.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.DISCONNECTED
        client.subscriptionTopicsList = ["topic1","topic2"]
        result = client.subscribe(["topic1","topic2"])

        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_subscribe_when_subscription_fails_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"subscribe")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_subscribe = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_subscribe.return_value = [0]
        mock_wait.return_value = False

        client.clientStatus = ClientStatus.CONNECTED
        client.subscriptionTopicsList = ["topic1","topic2"]
        result = client.subscribe(["topic1","topic2"])

        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #validate_client_state()
    def test_vaidate_client_state_with_proper_arguments_should_success(self):

        client.clientStatus = ClientStatus.CONNECTED
        client.pahoClient = mqtt_client.Client()
        
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        mock_is_connected = patcher1.start()
        mock_is_connected.return_value = True

        result = client.validate_client_state()
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        patcher1.stop()

    def test_vaidate_client_state_when_not_in_connected_state_should_fail(self):

        client.clientStatus = ClientStatus.INITIALIZED
        client.pahoClient = mqtt_client.Client()

        result = client.validate_client_state()
        self.assertEqual(result,-1)

        client.clientStatus = ClientStatus.NOT_INITIALIZED
        client.pahoClient = mqtt_client.Client()
        result = client.validate_client_state()
        self.assertEqual(result,-1)

        client.clientStatus = ClientStatus.DISCONNECTED
        client.pahoClient = mqtt_client.Client()
        result = client.validate_client_state()
        self.assertEqual(result,-2)

    def test_vaidate_client_state_when_client_is_not_connected_should_fail(self):

        client.clientStatus = ClientStatus.CONNECTED
        client.pahoClient = mqtt_client.Client()
        
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        mock_is_connected = patcher1.start()
        mock_is_connected.return_value = False

        result = client.validate_client_state()
        self.assertEqual(result,-1)
        # assert mock_is_connected.call_count == 1
        patcher1.stop()

    #publish_with_topic()
    def test_publish_with_topic_with_proper_arguments_should_success(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED

        result = client.publish_with_topic("topic","message")
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()


    def test_publish_with_invalid_argument_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED

        result = client.publish_with_topic("","message")
        self.assertEqual(result,-1)
        result1 = client.publish_with_topic("topic","")
        self.assertEqual(result1,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_publish_when_client_not_connected_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.INITIALIZED

        result = client.publish_with_topic("topic","message")
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_publish_when_payloadsized_exceed_maximum_size_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.INITIALIZED

        result = client.publish_with_topic("topic",max_payload)
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_publish_when_publish_fails_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = False

        client.clientStatus = ClientStatus.CONNECTED

        result = client.publish_with_topic("topic","message")
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #dispatch()
    def test_dispatch_with_proper_arguments_should_success(self):
            
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.payloadJSON = {"key":"value"}

        result = client.dispatch()
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_dispatch_with_empty_payload_should_success(self):
            
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.payloadJSON = {}

        result = client.dispatch()
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_dispatch_when_disconnected_should_fail(self):
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.DISCONNECTED
        client.payloadJSON = {"key":"value"}

        result = client.dispatch()
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #publish()
    def test_publish_with_proper_arguments_should_success(self):
        
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        message = {"key":"value"}

        result = client.publish(message)
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_publish_with_non_json_arguments_should_fail(self):
        
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        message = "HELLO"

        result = client.publish(message)
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_publish_when_disconnect_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.DISCONNECTED
        message = {"key":"value"}

        result = client.publish(message)
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #dispatch_event
    def test_dispatch_event_with_proper_arguments_should_success(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        message = {"key":"value"}

        result = client.dispatch_event("event_type","event_description",message,"assert_name")
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_dispatch_event_with_empty_arguments_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        
        result = client.dispatch_event()
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #dispatch_assert()
    def test_dispatch_asset_with_proper_arguments_should_success(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.payloadJSON = {"key":"value"}

        result = client.dispatch_asset("assert_name")
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_dispatch_asset_with_improper_arguments_should_fail(self):

        result = client.dispatch_asset("")
        self.assertEqual(result,-1)

    def test_dispatch_asset_with_no_payload_should_success(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.payloadJSON = {}

        result = client.dispatch_asset("assert_name")
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()


    #publish_ack()
    def test_publish_ack_with_proper_arguments_should_success(self):
            
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED

        result = client.publish_ack("topic","1234567890",CommandAckResponseCodes.SUCCESSFULLY_EXECUTED ,"command_response")
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()   

    def test_publish_ack_with_disconnected_state_proper_should_fail(self):
            
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.DISCONNECTED

        result = client.publish_ack("topic","1234567890",CommandAckResponseCodes.SUCCESSFULLY_EXECUTED ,"command_response")
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()   
    
    def test_publish_ack_with_improper_arguments_should_fail(self):
        
        result = client.publish_ack("","",CommandAckResponseCodes.SUCCESSFULLY_EXECUTED ,"")
        self.assertEqual(result,-1)
   
    #publish_config_ack()
    def test_publish_config_ack_with_proper_arguments_should_success(self):
            
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED

        result = client.publish_config_ack("1234567890",ConfigAckResponseCodes.SUCCESSFULLY_EXECUTED ,"config_response")
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_publish_config_ack_with_improper_statuscode_should_success(self):
            
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED

        result = client.publish_config_ack("1234567890",CommandAckResponseCodes.SUCCESSFULLY_EXECUTED ,"config_response")
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()
    
    #publish_command_ack()
    def test_publish_command_ack_with_proper_arguments_should_success(self):    
    
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED

        result = client.publish_command_ack("1234567890",CommandAckResponseCodes.SUCCESSFULLY_EXECUTED ,"command_response")
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_publish_command_ack_with_improper_statuscode_should_fail(self):
                
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED

        result = client.publish_command_ack("1234567890",ConfigAckResponseCodes.SUCCESSFULLY_EXECUTED ,"command_response")
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #send_first_ack
    
    def test_send_first_ack_with_proper_arguments_should_success(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        message = '[{"payload":[{"edge_command_key":"${light.MODBUS}","value":"on"}],"command_name":"light","correlation_id":"143c5dc0-aabf-11ee-b726-5354005d2854"}]'

        result = client.send_first_ack(message,"topic",ConfigAckResponseCodes.CONFIG_RECEIVED_ACK_CODE)
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_send_first_ack_when_topic_null_will_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        message = '[{"payload":[{"edge_command_key":"${light.MODBUS}","value":"on"}],"command_name":"light","correlation_id":"143c5dc0-aabf-11ee-b726-5354005d2854"}]'

        result = client.send_first_ack(message,"",ConfigAckResponseCodes.CONFIG_RECEIVED_ACK_CODE)
        self.assertEqual(result,-1)
        result = client.send_first_ack(message,None,ConfigAckResponseCodes.CONFIG_RECEIVED_ACK_CODE)
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #handle_config()
    def test_handle_config_with_proper_arguments_should_success(self):
        
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.subscribe_config_callback(test)

        print(client.callBackList)
        message = mqtt_client.MQTTMessage()
        message.payload = '[{"payload":[{"edge_command_key":"${light.MODBUS}","value":"on"}],"command_name":"light","correlation_id":"143c5dc0-aabf-11ee-b726-5354005d2854"}]'

        result = client.handle_config(message)
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_handle_config_when_client_disconnected_should_fail(self):
        
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.DISCONNECTED
        client.subscribe_config_callback(test)

        message = mqtt_client.MQTTMessage()
        message.payload = '[{"payload":[{"edge_command_key":"${light.MODBUS}","value":"on"}],"command_name":"light","correlation_id":"143c5dc0-aabf-11ee-b726-5354005d2854"}]'

        result = client.handle_config(message)
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_handle_config_when_no_subscribe_config_callback_should_fail(self):
        
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.callBackList={}
        

        message = mqtt_client.MQTTMessage()
        message.payload = '[{"payload":[{"edge_command_key":"${light.MODBUS}","value":"on"}],"command_name":"light","correlation_id":"143c5dc0-aabf-11ee-b726-5354005d2854"}]'

        result = client.handle_config(message)
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #handle_command()
    def test_handle_command_with_proper_arguments_should_success(self):
        
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.subscribe_command_callback(test)
        client.clientStatus = ClientStatus.CONNECTED

        message = mqtt_client.MQTTMessage()
        message.payload = '[{"payload":[{"edge_command_key":"${light.MODBUS}","value":"on"}],"command_name":"light","correlation_id":"143c5dc0-aabf-11ee-b726-5354005d2854"}]'

        result = client.handle_command(message)
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_publish.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_handle_command_when_client_disconnected_should_fail(self):
                
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.subscribe_command_callback(test)
        client.clientStatus = ClientStatus.DISCONNECTED

        message = mqtt_client.MQTTMessage()
        message.payload = '[{"payload":[{"edge_command_key":"${light.MODBUS}","value":"on"}],"command_name":"light","correlation_id":"143c5dc0-aabf-11ee-b726-5354005d2854"}]'

        result = client.handle_command(message)
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def test_handle_command_when_no_subscribe_command_callback_should_fail(self):
                
        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"publish")
        patcher3 = mock.patch.object(threading.Event,"wait")
        mock_is_connected = patcher1.start()
        mock_publish = patcher2.start()
        mock_wait = patcher3.start()
        mock_is_connected.return_value = True
        mock_publish.return_value = [0]
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.callBackList={}

        message = mqtt_client.MQTTMessage()
        message.payload = '[{"payload":[{"edge_command_key":"${light.MODBUS}","value":"on"}],"command_name":"light","correlation_id":"143c5dc0-aabf-11ee-b726-5354005d2854"}]'

        result = client.handle_command(message)
        self.assertEqual(result,-1)

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    #disconnect()
    def test_disconnect_already_in_disconnected_state_should_success(self):

        client.clientStatus = ClientStatus.DISCONNECTED
        result = client.disconnect()
        self.assertEqual(result,0)

    def test_disconnect_in_connected_state_should_success(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"disconnect")
        patcher3 = mock.patch.object(mqtt_client.Client,"loop_stop")
        patcher4 = mock.patch.object(threading.Event,"wait")    
        mock_is_connected = patcher1.start()
        mock_disconnect = patcher2.start()
        mock_loop_stop = patcher3.start()
        mock_wait = patcher4.start()
        mock_is_connected.return_value = True
        mock_wait.return_value = True

        client.clientStatus = ClientStatus.CONNECTED
        client.disconnectResponseCode = 0

        result = client.disconnect()
        self.assertEqual(result,0)
        assert mock_is_connected.call_count == 1
        assert mock_disconnect.call_count == 1 
        assert mock_loop_stop.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()
        patcher4.stop()

    def test_disconnect_when_disconnect_fails_should_fail(self):

        client.pahoClient = mqtt_client.Client()
        patcher1 = mock.patch.object(mqtt_client.Client,"is_connected")
        patcher2 = mock.patch.object(mqtt_client.Client,"disconnect")
        patcher3 = mock.patch.object(mqtt_client.Client,"loop_stop")
        patcher4 = mock.patch.object(threading.Event,"wait")    
        mock_is_connected = patcher1.start()
        mock_disconnect = patcher2.start()
        mock_loop_stop = patcher3.start()
        mock_wait = patcher4.start()
        mock_is_connected.return_value = True
        mock_wait.return_value = False

        client.clientStatus = ClientStatus.CONNECTED
        client.disconnectResponseCode = 0

        result = client.disconnect()
        self.assertEqual(result,-1)
        assert mock_is_connected.call_count == 1
        assert mock_disconnect.call_count == 1 
        assert mock_loop_stop.call_count == 1
        assert mock_wait.call_count == 1

        patcher1.stop()
        patcher2.stop()
        patcher3.stop()
        patcher4.stop()

    #set_maximum_payload_size()
    def test_set_maximum_payload_size_with_proper_arguments_should_success(self):

        result = client.set_maximum_payload_size(40000)
        self.assertEqual(result,0)
        self.assertEqual(client.payload_size,40000)

    def test_set_maximum_payload_size_with_maximum_or_minimum_limit_should_fail(self):

        result = client.set_maximum_payload_size(4000)
        self.assertEqual(result,-1)
        result = client.set_maximum_payload_size(400000)
        self.assertEqual(result,-1)


if __name__ == '__main__':
    unittest.main()