import pyaudiowpatch as pyaudio

pa = pyaudio.PyAudio()

for device in pa.get_loopback_device_info_generator():
    print(device)

loopback_device = pa.get_default_wasapi_loopback()

stream = pa.open(
    format=pyaudio.paFloat32,
    channels=loopback_device['maxInputChannels'],
    rate=int(loopback_device['defaultSampleRate']),
    input=True,
    input_device_index=loopback_device['index'],
    frames_per_buffer=1024,
)

while True:
    data = stream.read(1024)
    print(data)

pa.terminate()