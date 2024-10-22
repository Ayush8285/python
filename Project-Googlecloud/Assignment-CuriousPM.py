#on line  20     ----- add your own api key for azure openai
#on line 95, 40  ----- add your google cloud credentials json file



from openai import OpenAI
from pydub import AudioSegment
from google.oauth2 import service_account
from google.cloud import speech
from google.cloud import texttospeech
import moviepy.editor as mp
import streamlit as st
import pytubefix
import io
import os



client = OpenAI(
    api_key="<YOUR-OWN-API-KEY>",    #I didn't write because of security
)



#Downloading any video from youtube and extracting audio from it
def download_youtube_video(video_url):
    yt = pytubefix.YouTube(video_url)
    stream = yt.streams.get_highest_resolution()
    stream.download(filename="video.mp4")

    clip = mp.VideoFileClip("video.mp4")
    audio = clip.audio
    audio.write_audiofile("audio.wav")




#converting audio into text using google cloud
def transcribe_audio_to_text(audio_file):
    client_file = "<YOUR-OWN-CREDENTIALS-JSON-FILE>"
    credentials = service_account.Credentials.from_service_account_file(client_file)
    client = speech.SpeechClient(credentials=credentials)

    #load the audio file
    audio_file_path = 'audio.wav'
    audio = AudioSegment.from_wav(audio_file_path)

    # Convert to mono
    mono_audio = audio.set_channels(1)

    mono_audio.export('audio_mono.wav', format='wav')
    audio_file = 'audio_mono.wav'

    with io.open(audio_file, 'rb') as f:
        content = f.read()
        audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code='en-US'
    )

    response = client.recognize(config=config, audio=audio)
    response1 = ""
    for result in response.results:
        response1 = response1 + " " + result.alternatives[0].transcript
    
    return response1



#Removing hmm and umm from the text using Azure OpenAi with gpt-4o model
def correct_grammar(text):
    
    prompt = f"Please rephrase the following text, removing any filler words like 'hmm' and 'umm': {text}"

    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="GPT-4o",     
    )
    # Extracting the response text
    corrected_text = response['choices'][0]['message']['content']
    
    return corrected_text
    



#Now Converting the corrected text to AI generated audio using journey voice model
def text_to_audio(text):
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "<YOUR-OWN-CREDENTIALS-JSON-FILE>"

    # Create a Text-to-Speech client
    client = texttospeech.TextToSpeechClient()

    # Set the text input
    input_text = texttospeech.SynthesisInput(text=text)

    # Building the voice request, select the language code and the Journey voice model
    voice = texttospeech.VoiceSelectionParams(
        language_code='en-US',
        name='en-US-Journey-D'                          #use this name for setting pitch and speaking_rate    (en-US-Standard-B) 
    )

    # Selecting the type of audio file you want to returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        effects_profile_id=['small-bluetooth-speaker-class-device'],
        # speaking_rate=0.6,
        # pitch=1
    )

    # Performing the text-to-speech request
    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )

    # Writing the response to the output file
    with open('corrected_audio.mp3', 'wb') as f:
        f.write(response.audio_content)




#Merging AI generating audio with the original audio
def merge_audio_with_video(original_video_path, corrected_audio_path):

    # Loading the original video and corrected audio
    original_video = mp.VideoFileClip(original_video_path)
    corrected_audio = mp.AudioFileClip(corrected_audio_path)

    # Calculating duration difference
    original_audio_duration = original_video.audio.duration
    corrected_audio_duration = corrected_audio.duration

    # If the corrected audio is shorter than the original audio, trim the original video audio
    if corrected_audio_duration < original_audio_duration:

        start_time = (original_audio_duration - corrected_audio_duration) / 2
        corrected_audio = corrected_audio.subclip(start_time)

    elif corrected_audio_duration > original_audio_duration:
        # If the corrected audio is longer, we can either trim it or pad it.
        corrected_audio = corrected_audio.subclip(0, original_audio_duration)

    # Setting the corrected audio to the original video
    new_audio = mp.CompositeAudioClip([corrected_audio])
    original_video.audio = new_audio
    original_video.write_videofile("final_video.mp4")


    original_video.close()
    corrected_audio.close()
    



#Main method to run this Assignment
def main():
    st.title("YouTube Video Processor ")

    video_url = st.text_input("Enter YouTube video URL ")

    if st.button("Process Video"):
        if video_url:
            download_youtube_video(video_url)
            audio_file = "audio.wav"
            transcription = transcribe_audio_to_text(audio_file)
            corrected_text = correct_grammar(transcription)
            text_to_audio(corrected_text)
            merge_audio_with_video("video.mp4", "corrected_audio.mp3")
            st.success("Video processed successfully!")
        else:
            st.warning("Please enter a valid YouTube video URL.")


if __name__ == "__main__":
    main()
