import speech_recognition as sr
import whisper
import numpy as np
import threading
import queue
import time
from openai import OpenAI
import io
import wave
import tempfile

client = OpenAI()

# Initialize the queue
audio_queue = queue.Queue()
results_queue = queue.Queue()


def producer():
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=16000) as source:
        r.adjust_for_ambient_noise(source)
        print("Environment noise adjusted. Please say 'start recording' to begin.")

        while True:
            audio = r.listen(source)
            audio_queue.put(audio)
            print("Audio chunk queued for processing.")

def consumer():
    while True:
        audio = audio_queue.get()
        if audio is None:
            break
        try:
            print("Sending audio to OpenAI for transcription...")
            # Create a temporary file to hold the audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                with wave.open(tmp_file, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(audio.sample_width)
                    wf.setframerate(audio.sample_rate)
                    wf.writeframes(audio.get_wav_data())
                print('tempfile created')
                # Read back the temporary file for sending
                with open(tmp_file.name, 'rb') as file_to_send:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=file_to_send,
                        response_format="text"
                    )
                    print('file recieved')
                    print(response)
                    # results_queue.put(text)
                    print("Transcription added to results queue.")
        except Exception as e:
            print(f"Error during transcription: {e}")

def main():
    producer_thread=threading.Thread(target=producer)
    consumer_thread=threading.Thread(target=consumer)

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    audio_queue.put(None)  # Signal the consumer to exit
    consumer_thread.join()

if __name__=='__main__':
    main()

# def play_audio_from_queue():
#     # Get the audio chunk from the queue
#     # audio_chunk = audio_queue.get()
#     # p = pyaudio.PyAudio()
#     # stream = p.open(format=pyaudio.paInt16,  # Fixed format
#     #                 channels=1,  # Mono audio
#     #                 rate=16000,  # Sample rate from producer
#     #                 output=True)

#     # # Play the chunk
#     # data = audio_chunk.get_wav_data()
#     # stream.write(data)

#     # # Cleanup
#     # stream.stop_stream()
#     # stream.close()
#     # p.terminate()
#     # print("Audio playback completed.")

#      # Get the audio chunk from the queue
#     audio_chunk = audio_queue.get()

#     # Extract the audio data from the chunk
#     audio_data = audio_chunk.get_wav_data()

#     # Use PyAudio to play back the audio
#     p = pyaudio.PyAudio()

#     # Open a stream based on the audio properties
#     stream = p.open(format=p.get_format_from_width(audio_chunk.sample_width),
#                     channels=1,  # This should actually be the number of channels
#                     rate=audio_chunk.sample_rate,
#                     output=True)

#     # Write the audio data to the stream in chunks
#     chunk_size = 1024
#     for i in range(0, len(audio_data), chunk_size):
#         stream.write(audio_data[i:i+chunk_size])

#     # Close and terminate everything properly
#     stream.stop_stream()
#     stream.close()
#     p.terminate()
#     print("Audio playback completed.")

# def main():
#     producer()
#     if not audio_queue.empty():
#         play_audio_from_queue()

# if __name__ == "__main__":
#     main()