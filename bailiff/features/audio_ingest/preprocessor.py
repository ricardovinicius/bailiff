import numpy as np
from scipy.signal import butter, lfilter

class AudioPreprocessor:
    def __init__(self, sample_rate=16000, cutoff=85):
        self.sample_rate = sample_rate
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff / nyquist
        self.b, self.a = butter(5, normal_cutoff, btype='high', analog=False)
        
        from scipy.signal import lfilter_zi
        self.zi = lfilter_zi(self.b, self.a)

    def process(self, chunk_data: np.float32) -> np.float32:
        filtered_data, self.zi = lfilter(self.b, self.a, chunk_data, zi=self.zi)
        return filtered_data.astype(np.float32)

def get_preprocessor(sample_rate=16000, cutoff=85):
    return AudioPreprocessor(sample_rate, cutoff)