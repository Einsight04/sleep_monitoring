import audioop
import glob
import math
import os
import struct
import time

import pyaudio
import wave
from threading import Thread

MIN_RMS = 750
PREVIOUS_RECORDING_SECONDS = 3

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

recording_count = 0

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)


def rms(data: bytes) -> int:
    return audioop.rms(data, 2)


def record_audio() -> None:
    global recording_count

    print("Recording audio")
    frames = []

    """
    1) Add previous 3 seconds of audio
    2) Keep adding audio
    3) When audio is below threshold for more than x seconds, stop recording
    4) If audio snippet has rms > 750 for less than 1 second, discard
    5) Save an extra 3 seconds of audio
    """

    # 1) Add previous 3 seconds of audio
    for i in range(0, int(RATE / CHUNK * PREVIOUS_RECORDING_SECONDS)):
        frames.append(stream.read(CHUNK))

    # 2) Keep adding audio
    while True:
        data = stream.read(CHUNK)
        frames.append(data)
        if rms(data) < MIN_RMS:
            time.sleep(0.1)
            if rms(stream.read(CHUNK)) < MIN_RMS:
                break

    # 3) When audio is below threshold for more than x seconds, stop recording
    # 4) If audio snippet has rms > 750 for less than 1 second, discard
    if rms(b"".join(frames)) < MIN_RMS:
        print("Discarding audio")
        return

    # 5) continue recording for 3 seconds
    for i in range(0, int(RATE / CHUNK * PREVIOUS_RECORDING_SECONDS)):
        frames.append(stream.read(CHUNK))

    wf = wave.open("output/recording_{}.wav".format(recording_count), 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    recording_count += 1
    print("Audio recording saved")


def audio_listener() -> None:
    while True:
        if rms(stream.read(CHUNK)) > MIN_RMS:
            record_audio()


def cleanup() -> None:
    print("Cleanup process started")
    files = glob.glob("output/*")
    for f in files:
        os.remove(f)
    print("Cleanup process finished")


if __name__ == '__main__':
    cleanup()
    audio_listener = Thread(target=audio_listener())
    audio_listener.start()
