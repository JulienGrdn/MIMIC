from src.gui.devices.frontend.mqtt_handler import MqttHandler

_brokers: dict[str, MqttHandler] = {}

def get_shared_handler(broker_address: str) -> MqttHandler:
    """Returns a single shared MqttHandler per broker address."""
    if broker_address not in _brokers:
        handler = MqttHandler(broker_address=broker_address)
        handler.start()
        _brokers[broker_address] = handler
        print(f"[BrokerRegistry] New connection to {broker_address}")
    return _brokers[broker_address]