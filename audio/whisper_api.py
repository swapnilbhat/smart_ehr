from openai import OpenAI
client = OpenAI()

audio_file = open("/home/miko/ai/smart_ehr/output.wav", "rb")
transcription = client.audio.transcriptions.create(
  model="whisper-1", 
  file=audio_file, 
  response_format="text"
)
print(transcription)