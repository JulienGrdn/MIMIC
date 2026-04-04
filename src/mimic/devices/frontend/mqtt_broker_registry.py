import logging

from mimic.devices.frontend.mqtt_handler import MqttHandler

logger = logging.getLogger(__name__)

_brokers: dict[str, MqttHandler] = {}

def get_shared_handler(broker_address: str) -> MqttHandler:
    """Returns a single shared MqttHandler per broker address."""
    if broker_address not in _brokers:
        handler = MqttHandler(broker_address=broker_address)
        handler.start()
        _brokers[broker_address] = handler
        logger.info("New MQTT connection to %s", broker_address)
    return _brokers[broker_address]

def stop_all_brokers():
    for handler in _brokers.values():
        handler.stop()