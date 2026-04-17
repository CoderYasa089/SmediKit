from nicegui import ui, app
import paho.mqtt.client as mqtt
import json
from datetime import datetime
# --- Global State ---
vitals = {'bpm': 0, 'spo2': 0, 'temp': 0.0}
history = {'time': [], 'bpm': [], 'spo2': [], 'temp': []}
time_counter = 0

# --- MQTT Setup ---
# UPGRADED TO VERSION 2 (Added reason_code and properties to silence warnings)
def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to Mosquitto Broker")
    client.subscribe("smedikit/vitals")

def on_message(client, userdata, msg):
    global vitals
    try:
        data = json.loads(msg.payload.decode())
        vitals['bpm'] = data.get('bpm', 0)
        vitals['spo2'] = data.get('spo2', 0)
        vitals['temp'] = data.get('temp', 0.0)
    except Exception as e:
        pass

# UPGRADED TO VERSION 2
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("127.0.0.1", 1883, 60)
client.loop_start()

# --- UI Setup ---
ui.dark_mode().enable()
ui.colors(primary='#1a2332', secondary='#2c3e50', accent='#e74c3c')

with ui.header().classes('items-center justify-between p-4 bg-primary'):
    ui.label('SmediKit V4: Edge Triage UI').classes('text-2xl font-bold text-white')
    ui.label('Status: FEDERATED EDGE NODE ACTIVE | Zero Cloud Data Transmission').classes('text-green-400 font-mono text-sm')

with ui.row().classes('w-full justify-center gap-8 mt-8'):
    # Temp Card
    with ui.card().classes('w-64 items-center bg-secondary'):
        ui.icon('thermostat', size='3rem', color='blue-400')
        ui.label('Wrist Temperature').classes('text-gray-400 mt-2')
        temp_label = ui.label('0.0 °C').classes('text-4xl font-bold text-blue-400 mt-2')
        temp_status = ui.label('Waiting...').classes('font-bold mt-2')

    # BPM Card
    with ui.card().classes('w-64 items-center bg-secondary'):
        ui.icon('favorite', size='3rem', color='red-400')
        ui.label('Heart Rate').classes('text-gray-400 mt-2')
        bpm_label = ui.label('0 BPM').classes('text-4xl font-bold text-red-400 mt-2')
        bpm_status = ui.label('Waiting...').classes('font-bold mt-2')

    # SpO2 Card
    with ui.card().classes('w-64 items-center bg-secondary'):
        ui.icon('air', size='3rem', color='teal-400')
        ui.label('Blood Oxygen').classes('text-gray-400 mt-2')
        spo2_label = ui.label('0 %').classes('text-4xl font-bold text-teal-400 mt-2')
        spo2_status = ui.label('Waiting...').classes('font-bold mt-2')

# ECharts Graph
echart = ui.echart({
    'tooltip': {'trigger': 'axis'},
    'legend': {'data': ['Temp (°C)', 'BPM', 'SpO2 (%)'], 'textStyle': {'color': '#e5e7eb'}},
    'xAxis': {
        'type': 'category', 
        'data': [], 
        'axisLine': {'lineStyle': {'color': '#555'}},
        'axisLabel': {'color': '#e5e7eb'} # FIX: Light font for time
    },
    'yAxis': [
        {
            'type': 'value', 'name': 'Temp', 'min': 25, 'max': 45, 'position': 'left',
            'axisLabel': {'color': '#e5e7eb'}, # FIX: Light font
            'nameTextStyle': {'color': '#e5e7eb'},
            'splitLine': {'lineStyle': {'color': '#333'}}
        },
        {
            'type': 'value', 'name': 'BPM / SpO2', 'min': 0, 'max': 150, 'position': 'right',
            'axisLabel': {'color': '#e5e7eb'}, # FIX: Light font
            'nameTextStyle': {'color': '#e5e7eb'},
            'splitLine': {'show': False}
        }
    ],
    'series': [
        {'name': 'Temp (°C)', 'type': 'line', 'data': [], 'yAxisIndex': 0, 'itemStyle': {'color': '#60a5fa'}},
        {'name': 'BPM', 'type': 'line', 'data': [], 'yAxisIndex': 1, 'itemStyle': {'color': '#f87171'}},
        {'name': 'SpO2 (%)', 'type': 'line', 'data': [], 'yAxisIndex': 1, 'itemStyle': {'color': '#2dd4bf'}}
    ],
}).classes('w-11/12 h-96 mx-auto mt-8 bg-secondary p-4 rounded-lg')

# --- Update Logic ---
# --- Update Logic ---
def update_ui():
    global time_counter
    t = vitals['temp']
    b = vitals['bpm']
    s = vitals['spo2']

    # Update Big Numbers
    temp_label.set_text(f"{t:.1f} °C")
    bpm_label.set_text(f"{b} BPM")
    spo2_label.set_text(f"{s} %")

    # Safe Local AI Triage (0-Proof)
    # Safe Local AI Triage (Chain-Proof & 0-Proof)
    if t > 37.5:
        temp_status.set_text('FEVER DETECTED')
        temp_status.style('color: #f87171')
    elif t > 0:
        temp_status.set_text('Normal')
        temp_status.style('color: #4ade80')
    else:
        temp_status.set_text('Waiting...')
        temp_status.style('color: #9ca3af')

    if b > 100 or (b < 50 and b > 0):
        bpm_status.set_text('IRREGULAR RHYTHM')
        bpm_status.style('color: #f87171')
    elif b >= 50:
        bpm_status.set_text('Normal')
        bpm_status.style('color: #4ade80')
    else:
        bpm_status.set_text('Waiting...')
        bpm_status.style('color: #9ca3af')
        
    if s < 92 and s > 0:
        spo2_status.set_text('LOW OXYGEN')
        spo2_status.style('color: #f87171')
    elif s >= 92:
        spo2_status.set_text('Normal')
        spo2_status.style('color: #4ade80')
    else:
        spo2_status.set_text('Waiting...')
        spo2_status.style('color: #9ca3af')

    # Update Graph History (Uses actual PC System Time)
    if b > 0 or t > 0:
        current_time = datetime.now().strftime("%H:%M:%S")
        history['time'].append(current_time)
        history['temp'].append(t)
        history['bpm'].append(b)
        history['spo2'].append(s)

        # Keep graph moving by popping oldest data
        if len(history['time']) > 30:
            history['time'].pop(0)
            history['temp'].pop(0)
            history['bpm'].pop(0)
            history['spo2'].pop(0)

        echart.options['xAxis']['data'] = history['time']
        echart.options['series'][0]['data'] = history['temp']
        echart.options['series'][1]['data'] = history['bpm']
        echart.options['series'][2]['data'] = history['spo2']
        echart.update() 

# --- ADD THESE TWO LINES BACK TO THE VERY BOTTOM ---
ui.timer(1.0, update_ui)
ui.run(title="SmediKit UI", port=8080)