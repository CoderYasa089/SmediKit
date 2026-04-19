from nicegui import ui, app
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# --- Global State ---
vitals = {'bpm': 0, 'spo2': 0, 'temp': 0.0}
history = {'time': [], 'bpm': [], 'spo2': [], 'temp': []}
time_counter = 0

# --- MQTT Setup ---
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

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect("127.0.0.1", 1883, 60)
client.loop_start()

# --- UI Setup ---
ui.dark_mode().enable()
# Darker, more modern background colors
ui.colors(primary='#0f172a', secondary='#1e293b', accent='#38bdf8')

# Header
with ui.header().classes('items-center justify-between p-5 bg-primary border-b border-gray-800'):
    with ui.column().classes('gap-1'):
        ui.label('SmediKit: AI-Powered Telemedicine & Remote Vitals Monitoring Hub').classes('text-2xl font-bold text-white tracking-wide')
        ui.label('Architecture: LOCAL FOG NODE | No Cloud Data Transmission').classes('text-gray-300 font-mono text-lg font-semibold')

# System Status Bar
with ui.row().classes('w-full justify-between items-center px-10 mt-6'):
    # Dynamic Hardware Badge
    system_status_badge = ui.label('HARDWARE STANDBY').classes('px-4 py-1.5 rounded-md bg-gray-700 text-gray-300 font-bold text-sm tracking-wider shadow-inner')
    
    # User Instruction
    with ui.row().classes('items-center gap-2'):
        ui.icon('info', color='blue-400', size='sm')
        ui.label('Please allow 5-10 seconds after activation for Heart Rate and SpO2 algorithms to stabilize.').classes('text-blue-300/80 text-sm italic')

# Main Cards (Upgraded Tailwind Styling to mimic modern UI)
card_style = 'w-72 flex flex-col items-center bg-secondary border border-gray-700/50 rounded-2xl shadow-xl p-6 transition-all duration-300'

with ui.row().classes('w-full justify-center gap-10 mt-6'):
    # Temp Card
    with ui.card().classes(card_style):
        ui.icon('thermostat', size='3.5rem', color='blue-400').classes('mb-2')
        ui.label('Wrist Temperature').classes('text-gray-400 font-medium')
        temp_label = ui.label('0.0 °C').classes('text-5xl font-bold text-blue-400 mt-3 drop-shadow-md')
        temp_status = ui.label('Waiting...').classes('font-bold mt-4 tracking-wide text-gray-500')

    # BPM Card
    with ui.card().classes(card_style):
        ui.icon('favorite', size='3.5rem', color='red-400').classes('mb-2')
        ui.label('Heart Rate').classes('text-gray-400 font-medium')
        bpm_label = ui.label('0 BPM').classes('text-5xl font-bold text-red-400 mt-3 drop-shadow-md')
        bpm_status = ui.label('Waiting...').classes('font-bold mt-4 tracking-wide text-gray-500')

    # SpO2 Card
    with ui.card().classes(card_style):
        ui.icon('air', size='3.5rem', color='teal-400').classes('mb-2')
        ui.label('Blood Oxygen').classes('text-gray-400 font-medium')
        spo2_label = ui.label('0 %').classes('text-5xl font-bold text-teal-400 mt-3 drop-shadow-md')
        spo2_status = ui.label('Waiting...').classes('font-bold mt-4 tracking-wide text-gray-500')

# ECharts Graph (With slightly darker background and lighter fonts)
echart = ui.echart({
    'tooltip': {'trigger': 'axis'},
    'legend': {'data': ['Temp (°C)', 'BPM', 'SpO2 (%)'], 'textStyle': {'color': '#e5e7eb'}},
    'xAxis': {
        'type': 'category', 
        'data': [], 
        'axisLine': {'lineStyle': {'color': '#475569'}},
        'axisLabel': {'color': '#94a3b8'} 
    },
    'yAxis': [
        {
            'type': 'value', 'name': 'Temp', 'min': 25, 'max': 45, 'position': 'left',
            'axisLabel': {'color': '#94a3b8'}, 
            'nameTextStyle': {'color': '#94a3b8'},
            'splitLine': {'lineStyle': {'color': '#1e293b'}}
        },
        {
            'type': 'value', 'name': 'BPM / SpO2', 'min': 0, 'max': 150, 'position': 'right',
            'axisLabel': {'color': '#94a3b8'}, 
            'nameTextStyle': {'color': '#94a3b8'},
            'splitLine': {'show': False}
        }
    ],
    'series': [
        {'name': 'Temp (°C)', 'type': 'line', 'data': [], 'yAxisIndex': 0, 'itemStyle': {'color': '#60a5fa'}, 'smooth': True},
        {'name': 'BPM', 'type': 'line', 'data': [], 'yAxisIndex': 1, 'itemStyle': {'color': '#f87171'}, 'smooth': True},
        {'name': 'SpO2 (%)', 'type': 'line', 'data': [], 'yAxisIndex': 1, 'itemStyle': {'color': '#2dd4bf'}, 'smooth': True}
    ],
}).classes('w-11/12 h-96 mx-auto mt-8 bg-secondary border border-gray-700/50 p-6 rounded-2xl shadow-xl')

# --- Update Logic ---
def update_ui():
    global time_counter
    t = vitals['temp']
    b = vitals['bpm']
    s = vitals['spo2']

    # Update Dynamic Hardware Status Badge
    if t == 0.0 and b == 0 and s == 0:
        system_status_badge.set_text('HARDWARE STANDBY')
        system_status_badge.classes('bg-gray-700 text-gray-300', replace='bg-red-600 text-white animate-pulse shadow-[0_0_15px_rgba(22,163,74,0.5)]')
    else:
        system_status_badge.set_text('SCAN ACTIVE')
        system_status_badge.classes('bg-green-600 text-white animate-pulse shadow-[0_0_15px_rgba(22,163,74,0.5)]', replace='bg-gray-700 text-gray-300')

    # Update Big Numbers
    temp_label.set_text(f"{t:.1f} °C")
    bpm_label.set_text(f"{b} BPM")
    spo2_label.set_text(f"{s} %")

    # Safe Local AI Triage
    if t > 37.5:
        temp_status.set_text('FEVER DETECTED')
        temp_status.style('color: #f87171')
    elif t > 0:
        temp_status.set_text('Normal')
        temp_status.style('color: #4ade80')
    else:
        temp_status.set_text('Waiting...')
        temp_status.style('color: #64748b')

    if b > 100 or (b < 50 and b > 0):
        bpm_status.set_text('IRREGULAR RHYTHM')
        bpm_status.style('color: #f87171')
    elif b >= 50:
        bpm_status.set_text('Normal')
        bpm_status.style('color: #4ade80')
    else:
        bpm_status.set_text('Waiting...')
        bpm_status.style('color: #64748b')
        
    if s < 92 and s > 0:
        spo2_status.set_text('LOW OXYGEN')
        spo2_status.style('color: #f87171')
    elif s >= 92:
        spo2_status.set_text('Normal')
        spo2_status.style('color: #4ade80')
    else:
        spo2_status.set_text('Waiting...')
        spo2_status.style('color: #64748b')

    # Update Graph History
    if b > 0 or t > 0:
        current_time = datetime.now().strftime("%H:%M:%S")
        history['time'].append(current_time)
        history['temp'].append(t)
        history['bpm'].append(b)
        history['spo2'].append(s)

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

ui.timer(1.0, update_ui)
ui.run(title="SmediKit Hub", port=8080)