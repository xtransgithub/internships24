// Function to fetch sensor data from the server
async function fetchSensorData() {
    try {
        const response = await fetch('http://169.254.154.212:5000/sensor-data');
        
        // Check if the response is ok
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        // Parse the JSON data
        const data = await response.json();
        console.log('Fetched sensor data:', data); // Debugging line
        return data;
    } catch (error) {
        console.error('Error fetching sensor data:', error);
        return null; // Return null if an error occurred
    }
}

// Function to update text boxes for temperature, humidity, light status, and gas sensor
function updateBoxes(temperature, humidity, light, gas) {
    document.getElementById("temperature").innerHTML = `${temperature} °C`;
    document.getElementById("humidity").innerHTML = `${humidity} %`;
    document.getElementById("light-status").innerHTML = light ? "1" : "0";
    document.getElementById("gas").innerHTML = gas;
}

// Function to update sensor readings
async function updateSensorReadings() {
    const sensorData = await fetchSensorData();
    if (sensorData) {
        const temperature = sensorData.temperature ? sensorData.temperature.toFixed(2) : "N/A";
        const humidity = sensorData.humidity ? sensorData.humidity.toFixed(2) : "N/A";
        const light = sensorData.light ? 1 : 0;
        const gas = sensorData.gas !== null ? sensorData.gas : "N/A";

        updateBoxes(temperature, humidity, light, gas);
    } else {
        console.error('No sensor data available or an error occurred.');
    }
}

// Periodically update sensor readings every 5 seconds
setInterval(updateSensorReadings, 5000);

// Function to toggle LED state with voice command and popup notification
async function toggleLED(ledNumber, state) {
    const payload = {};

    if (ledNumber === 2) {
        payload.led2 = state;
    } else if (ledNumber === 3) {
        payload.led3 = state;
    } else if (ledNumber === 4) {
        payload.led4 = state;
    }

    try {
        const response = await fetch('http://169.254.154.212:5000/led-control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            throw new Error(`Failed to toggle LED ${ledNumber}`);
        }

        // Log success and show popup
        const message = `LED ${ledNumber} has been turned ${state ? 'ON' : 'OFF'}`;
        console.log(message);
        showPopup(message);
    } catch (error) {
        console.error(`Error toggling LED ${ledNumber}:`, error);
        showPopup(`Error: Could not toggle LED ${ledNumber}`);
    }
}

// Display a popup notification
function showPopup(message) {
    const popup = document.createElement('div');
    popup.className = 'popup';
    popup.innerText = message;
    document.body.appendChild(popup);

    setTimeout(() => {
        popup.remove();
    }, 3000); // Remove popup after 3 seconds
}

// Voice command integration
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.lang = 'en-US';

recognition.onresult = function (event) {
    const transcript = event.results[event.results.length - 1][0].transcript.trim().toLowerCase();
    console.log('Voice Command:', transcript);

    if (transcript.includes('turn on led 2')) {
        toggleLED(2, 1);
    } else if (transcript.includes('turn off led 2')) {
        toggleLED(2, 0);
    } else if (transcript.includes('turn on led 3')) {
        toggleLED(3, 1);
    } else if (transcript.includes('turn off led 3')) {
        toggleLED(3, 0);
    } else if (transcript.includes('turn on led 4')) {
        toggleLED(4, 1);
    } else if (transcript.includes('turn off led 4')) {
        toggleLED(4, 0);
    } else {
        console.log('Voice command not recognized.');
    }
};

// Start voice recognition
recognition.start();

// Handle recognition errors
recognition.onerror = function (event) {
    console.error('Voice recognition error:', event.error);
    showPopup('Voice recognition error: ' + event.error);
};

// CSS for popups
const style = document.createElement('style');
style.textContent = `
.popup {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #333;
    color: #fff;
    padding: 10px 20px;
    border-radius: 5px;
    font-size: 14px;
    z-index: 1000;
    animation: fadeInOut 3s ease-in-out;
}

@keyframes fadeInOut {
    0% { opacity: 0; transform: translateY(10px); }
    10%, 90% { opacity: 1; transform: translateY(0); }
    100% { opacity: 0; transform: translateY(10px); }
}
`;
document.head.appendChild(style);
