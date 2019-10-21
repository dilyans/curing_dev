import {Enum} from 'enumify';

class States extends Enum{}
States.initEnum({
    ON:{
        get next() { return States.OFF },
    },
    OFF:{
        get next() { return States.ON },
    }
});
class Sensors extends Enum{}
Sensors.initEnum({
    TEMPERATURE: {
        label: "Temperature",
        valueName: "t",
        defaultValue: 15
    },
    HUMIDITY: {
        label: "Humidity",
        valueName: "h",
        defaultValue: 50
    }
})

const Scale = Object.freeze({
    Celsius: Symbol("c"),
    Fahrenheit: Symbol("f")
})

const TempRange = Object.freeze({
    Min: 10,
    Max: 15
});

const HumidityRange = Object.freeze({
    Min: 65,
    Max: 75
});

class Devices extends Enum{}
Devices.initEnum({
    FRIDGE: {
        label: "Fridge",
        stateName: "fridge"
    },
    FAN: {
        label: "Fan",
        stateName: "fan"
    },
    HUMIDIFIER: {
        label: "Humidifier",
        stateName: "humidifier"
    },
    DEHUMIDIFIER: {
        label: "Dehumidifier",
        stateName: "dehumidifier"
    }
});

class Messages extends Enum {}
Messages.initEnum(['SENSOR_UPDATE', 'DEVICE_UPDATE', 'HISTORY']);

export {States, Sensors, Messages, TempRange, HumidityRange, Scale, Devices};