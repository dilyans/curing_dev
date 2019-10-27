import gpiozero
from gpiozero.pins.mock import MockFactory
from enum import Enum

# Set the default pin factory to a mock factory
gpiozero.Device.pin_factory = MockFactory()

class State(Enum):
    ON = 'on'
    OFF = 'off'

class Device:
    def __init__(self, name, pin, state):
        self.name = name
        self.pin = pin
        self.device = gpiozero.LED(pin)
        self.state = State(state)

    def set_state(self, state_str):
        state = State[state_str]
        print('setting device {} to ', self.name, state_str)
        if state == State.ON:
            self.device.on()
        else:
            self.device.off()
        self.state = state
