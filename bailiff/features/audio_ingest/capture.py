import logging

import pyaudiowpatch as pyaudio

logger = logging.getLogger("bailiff.audio.capture")


class AudioCaptureManager:
    """
    Manages audio input devices and streams.

    Handles discovery of microphones and loopback devices (system audio), and provides methods
    to open PyAudio streams for capturing audio data.
    """
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        logger.info("PyAudio initialized")

    def get_default_microphone(self) -> int:
        """
        Get the default microphone device index.
        """
        info = self.pa.get_default_input_device_info()
        logger.info("Default microphone: %s (index=%d)", info['name'], info['index'])
        return info['index']

    def get_system_loopback(self) -> dict | None:
        """
        Get the WASAPI loopback device info for system audio capture.
        Returns the device info dict, or None if not found.
        """
        try:
            device = self.pa.get_default_wasapi_loopback()
            logger.info("Loopback device found: %s (index=%d, rate=%.0f)",
                        device['name'], device['index'], device['defaultSampleRate'])
            return device
        except Exception as e:
            logger.warning("No loopback device available: %s", e)
            return None

    def open_stream(self, device_info: dict, sample_rate: int, 
                    chunk_size: int) -> pyaudio.Stream:
        """
        Open a PyAudio input stream for the given device.
        """
        channels = max(1, int(device_info.get('maxInputChannels', 1)))

        logger.debug("Opening stream: device=%s, channels=%d, rate=%d, chunk=%d",
                      device_info['name'], channels, sample_rate, chunk_size)

        return self.pa.open(
            format=pyaudio.paFloat32,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=int(device_info['index']),
            frames_per_buffer=chunk_size,
        )

    def open_mic_stream(self, sample_rate: int, chunk_size: int) -> tuple[pyaudio.Stream, int]:
        """
        Open a stream for the default microphone.
        Returns (stream, channels).
        """
        mic_index = self.get_default_microphone()
        info = self.pa.get_device_info_by_index(mic_index)
        channels = max(1, int(info.get('maxInputChannels', 1)))
        stream = self.open_stream(info, sample_rate, chunk_size)
        logger.info("Mic stream opened: channels=%d, rate=%d", channels, sample_rate)
        return stream, channels

    def open_loopback_stream(self, sample_rate: int, chunk_size: int) -> tuple[pyaudio.Stream, int, int] | None:
        """
        Open a stream for WASAPI loopback (system audio).
        
        WASAPI loopback only supports the device's native sample rate,
        so we open at native rate and return it for downstream resampling.
        
        Returns (stream, channels, actual_sample_rate) or None if not available.
        """
        loopback_info = self.get_system_loopback()
        if loopback_info is None:
            return None
        
        channels = max(1, int(loopback_info.get('maxInputChannels', 1)))
        native_rate = int(loopback_info['defaultSampleRate'])

        # Calculate a proportional chunk size for the native rate
        native_chunk = int(chunk_size * native_rate / sample_rate)

        stream = self.open_stream(loopback_info, native_rate, native_chunk)
        logger.info("Loopback stream opened: channels=%d, native_rate=%d, native_chunk=%d",
                     channels, native_rate, native_chunk)
        return stream, channels, native_rate

    def terminate(self):
        """
        Clean up the PyAudio instance.
        """
        self.pa.terminate()
        logger.info("PyAudio terminated")