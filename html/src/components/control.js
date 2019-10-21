import React from 'react';

class DeviceControl extends React.Component {
    constructor(props) {
        super(props);
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange() {
        const state = this.props.state.next;
        this.props.onDeviceUpdate(state, this.props.device);
    }

    render() {
        const device = this.props.device;
        const value = this.props.state;
        return (
            <div>
                <label htmlFor='id'>{device.label}</label>
                <button id='id' onClick={this.handleChange}>
                    {value.name}
                </button>
            </div>
        )
    }
}

export default DeviceControl;