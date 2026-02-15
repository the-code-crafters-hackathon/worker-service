import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.infrastructure.queue.sqs_consumer import SQSConsumer


class TestSQSConsumer:
    
    @patch('app.infrastructure.queue.sqs_consumer.boto3')
    def test_receive_message_success(self, mock_boto3):
        """Test successful message receive"""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        mock_client.receive_message.return_value = {
            'Messages': [{
                'MessageId': '123',
                'ReceiptHandle': 'abc',
                'Body': json.dumps({
                    'video_id': 1,
                    'video_path': '/videos/test.mp4',
                    'timestamp': '20240215_103045'
                })
            }]
        }
        
        consumer = SQSConsumer()
        message = consumer.receive_message()
        
        assert message is not None
        assert message['MessageId'] == '123'
    
    @patch('app.infrastructure.queue.sqs_consumer.boto3')
    def test_receive_message_empty_queue(self, mock_boto3):
        """Test receiving from empty queue"""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        mock_client.receive_message.return_value = {}
        
        consumer = SQSConsumer()
        message = consumer.receive_message()
        
        assert message is None
    
    @patch('app.infrastructure.queue.sqs_consumer.boto3')
    def test_delete_message_success(self, mock_boto3):
        """Test successful message deletion"""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        consumer = SQSConsumer()
        result = consumer.delete_message('receipt-handle')
        
        assert result is True
        mock_client.delete_message.assert_called_once()
    
    @patch('app.infrastructure.queue.sqs_consumer.boto3')
    def test_parse_message_valid_json(self, mock_boto3):
        """Test parsing valid JSON message"""
        mock_boto3.client.return_value = MagicMock()
        
        consumer = SQSConsumer()
        message = {
            'Body': json.dumps({
                'video_id': 1,
                'video_path': '/videos/test.mp4',
                'timestamp': '20240215_103045'
            })
        }
        
        parsed = consumer.parse_message(message)
        
        assert parsed is not None
        assert parsed['video_id'] == 1
        assert parsed['video_path'] == '/videos/test.mp4'
    
    @patch('app.infrastructure.queue.sqs_consumer.boto3')
    def test_parse_message_invalid_json(self, mock_boto3):
        """Test parsing invalid JSON message"""
        mock_boto3.client.return_value = MagicMock()
        
        consumer = SQSConsumer()
        message = {'Body': 'invalid json'}
        
        parsed = consumer.parse_message(message)
        
        assert parsed is None
