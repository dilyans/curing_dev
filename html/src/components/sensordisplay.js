import React from 'react';

const SensorDisplay = props => {
    const value = props.value ||  "NA";
    const label = props.name || "Name Not Set";

    return (
        <div >
            {label}:{value}
        </div>
    )
}

export default SensorDisplay;