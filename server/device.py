import gpiozero
from gpiozero.pins.mock import MockFactory
from enum import Enum

# comment this line to test code on non raspberry pi machine
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
        self.set_state(self.state.name)

    def set_state(self, state_str):
        state = State[state_str]
        if state != self.state:
            #print('setting device {} to ', self.name, state_str)
            if state == State.ON:
                self.device.on()
            else:
                self.device.off()
            self.state = state
            return True
        #print("not setting state")
        return False

    def get_state(self):
        return self.state
