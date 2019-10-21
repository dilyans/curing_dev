import React from 'react';
import './App.css';
import {States, Devices, Sensors, Messages} from './components/defines';
import SensorDisplay from "./components/sensordisplay";
import DeviceControl from './components/control'

class App extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            temperature: {},
            humidity: {},
            historicData: []
        };
        // init device states
        for (const d of Devices.enumValues) {
            this.state[d.stateName] = States.OFF;
        }
        // init sensor states
        for (const s of Sensors.enumValues) {
            this.state[s.valueName] = s.defaultValue;
        }
        this.handleDeviceUpdate = this.handleDeviceUpdate.bind(this);
        this.wsConnection = undefined;
    }

    componentDidMount() {

        const wsUri = 'ws://localhost:8080/ws';
        const conn = new WebSocket(wsUri);
        this.wsConnection = conn;
        conn.onopen =  () => {
            console.log('Connected.');
            this.sendWebsocketCmd(Messages.HISTORY,{});
        };
        conn.onmessage = e => {
            console.log('New message ' + e.data);
            this.handleServerPush(e.data);
        };
    }

    handleServerPush(e) {
        const msg = JSON.parse(e);
        const msgType = Messages.enumValueOf(msg['type']);
        if (msgType === Messages.SENSOR_UPDATE) {
            let newState = {};
            Sensors.enumValues.forEach(s => {
                    newState[s.valueName] = msg[s.valueName];
                }
            )
            this.setState(newState);
        }
        if (msgType === Messages.DEVICE_UPDATE) {
            let newState = {};
            Devices.enumValues.forEach( d => {
                newState[d.stateName] =
                    Devices.enumValueOf(msg['payload'][d.stateName]);
            });
            this.setState(newState);
        }
        if (msgType === Messages.HISTORY) {
            this.setState({'history': msg['payload']});
        }
    }

    handleDeviceUpdate(value, device) {
        console.log("Got: " + value.toString() + " " + device);
        let newState = {};
        newState[device.stateName] = value;
        this.setState(newState);
        const payload = {};
        payload[device.stateName] = value.name.toString();
        this.sendWebsocketCmd(Messages.DEVICE_UPDATE, payload);
    }

    sendWebsocketCmd(cmd, payload){
        const newState = {};
        newState['cmd']=cmd.name;
        newState['payload'] = payload;
        const msg = JSON.stringify(newState);
        this.wsConnection.send(msg);
    }

    render() {
        return (
            <div className="App">
                <div>{
                    Sensors.enumValues.map(sensor =>
                        <SensorDisplay
                            key={sensor.name}
                            name={sensor.label}
                            value={this.state[sensor.valueName]}/>)
                }
                </div>
                <div>
                    {
                        Devices.enumValues.map(device =>
                            <DeviceControl
                                key={device.name}
                                device={device}
                                state={this.state[device.stateName]}
                                onDeviceUpdate={this.handleDeviceUpdate}/>
                        )
                    }
                </div>
            </div>
        )
    };
}

export default App;
