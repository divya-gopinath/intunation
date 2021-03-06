from util import *
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, lfilter

def detect_pitch_parabolic(signal, fs):
    """
    Pitch detection of a signal using parabolic interpolation on the STFT.

    TODO: Implement based on YIN algorithm (combine this w/ autocorrelation):
    https://asa.scitation.org/doi/pdf/10.1121/1.1458024

    Inputs:
    signal: real-valued audio signal assumed to be sampled at 44100 Hz. 
    fs: sample rate of signal 
    """
    # PARAMETERS 
    sample_rate = float(fs)
    freq_min, freq_max = 40, 4000 # frequency range of human voice in Hz 
    win_len = 4096
    hop_size = win_len / 4
    max_thresh = 0.1
    eps = 0.0000001

    # Get spectrogram (magnitude STFT) from audio signal and the constituent freqs
    signal -= np.mean(signal)  # Remove DC offset
    spec = stft_mag(signal, win_len, hop_size)
    fft_freqs = freqs_of_fft(sample_rate, win_len)

    # Average points and shift, pad to input size, avoid divide by zero errors
    shift_two = spec[2:]-spec[:-2]
    average = shift_two*0.5
    shift = 2*(spec[1:-1] - shift_two)
    shift[shift < eps] = eps
    shift = average / shift
    avg = np.pad(average, ((1, 1), (0, 0)), mode='constant')
    shift = np.pad(shift, ((1, 1), (0, 0)), mode='constant')
    dskew = 0.5 * avg * shift

    # Create frequency thresholds based on min and max freq
    pitches = np.zeros_like(spec)
    magnitudes = np.zeros_like(spec)
    idx = np.argwhere(column_wise_local_max(spec, max_thresh))

    # Store pitch and magnitude
    pitches[idx[:, 0], idx[:, 1]] = ((idx[:, 0] + shift[idx[:, 0], idx[:, 1]])
                                     * float(sample_rate) / win_len)

    magnitudes[idx[:, 0], idx[:, 1]] = (spec[idx[:, 0], idx[:, 1]]
                                  + dskew[idx[:, 0], idx[:, 1]])
    return pitches[np.argmax(magnitudes, axis=0)]

def column_wise_local_max(x, thresh):
    """
    Finds the column-wise local max of an 2-D array x and returns
    a numpy list containing the indeces of the local maxes, but conditioning on values
    that are atleast within thresh of the pure columnwise max. 
    """
    x = x * (x > thresh * np.max(x, axis=0))
    pad_x = np.pad(x, [(1, 1), (0, 0)], mode='edge')
    dim_1_idx = [slice(0, -2), slice(None)]
    dim_2_idx = [slice(2, pad_x.shape[0]), slice(None)]
    column_local_max  = np.logical_and(x > pad_x[dim_1_idx], x >= pad_x[dim_2_idx])
    return column_local_max

def detect_pitch_autocorr(signal, fs):
    """
    Calculate autocorrelation efficiently using an FFT convolution.
    Use parabolic interpolation on local maxes of autocorrelation 
    to find true fundamental frequencies (better for voice).

    Inputs:
    signal: audio signal
    fs: sample rate of audio signal
    """
    corr = fftconvolve(signal, signal[::-1], mode='full')
    corr = corr[len(corr)//2:]

    # Find the first peak on the left
    peaks = find_peaks(corr)
    interp_peak = parabolic_interp(corr, peaks)[0] if peaks.size != 0 else np.array([])
    return fs/interp_peak if interp_peak.size != 0 else np.array([])

def detect_pitches(fs, snd, window_len=2048, thresh=10):
    """
    Detects pitches given a filepath to the audio sample in question.
    Returns a list of tuples [(a1, b1), (a2, b2), ...] representing (frequency, time) pairs of the pitch.

    Inputs:
    fp: filepath of audio to pitch detect on
    window_len: number of samples to window audio file over
    thresh: threshold in Hz of when to classify a new pitch as "different"

    """
    assert(snd.ndim == 1) # Only allow mono recordings
    
    # Pitch detect in windows
    snd = clean_audio(snd)
    octave_thresh = 5
    all_pitches = []
    pitches = [(0, 0)]
    for i in range(0, len(snd), window_len):
        sig = snd[i:min(len(snd), i+window_len)]
        possible_pitches = detect_pitch_autocorr(sig, fs)
        if len(possible_pitches) != 0:
            pitch = possible_pitches[0]
            last_pitch = pitches[-1][1]
            # Edge case 1: too much of a shift in freq
            if len(possible_pitches) > 1 and i != 0 and np.abs(pitch - last_pitch) > np.abs(last_pitch - possible_pitches[1]) \
             and np.abs((possible_pitches[1] / pitch) - 2) < octave_thresh : 
                pitch = possible_pitches[1]
            all_pitches.append((float(i)/float(fs), pitch))
            if np.abs(pitch - last_pitch) >= thresh:
                pitches.append((float(i)/float(fs), pitch))
    return pitches[1:], all_pitches # get rid of dummy pitch at beginning
