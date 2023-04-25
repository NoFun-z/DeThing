import openai
import asyncio
import re
import whisper
import speech_recognition as sr
import pyttsx3  # Import pytsx3 library for speech synthesis
from EdgeGPT import Chatbot, ConversationStyle
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
# import eventlet
# eventlet.monkey_patch()

# Initialize the OpenAI API
openai.api_key = "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"

# Create a recognizer object and wake word variables
app = Flask(__name__, template_folder='.')
socketio = SocketIO(app, async_mode='eventlet')  # Use eventlet as the async mode
recognizer = sr.Recognizer()
engine = pyttsx3.init()

GPT_WAKE_WORD = "go"

def get_wake_word(phrase):
    if GPT_WAKE_WORD in phrase.lower():
        return GPT_WAKE_WORD
    else:
        return None

def speak_text(text):
    engine.say(text)
    engine.runAndWait()

def get_openai_response(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content":
            "You are a helpful assistant."},
            {"role": "user", "content": user_input},
        ],
        temperature=0.5,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        n=1,
        stop=["\nUser:"],
    )
    bot_response = response["choices"][0]["message"]["content"]
    return bot_response

async def main():
    while True:

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print(f"Say 'Go' to wake me up")
            speak_text("Say go to wake me up")
            while True:
                audio = recognizer.listen(source)
                try:
                    with open("audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    # Use the preloaded tiny_model
                    model = whisper.load_model("base")
                    result = model.transcribe("audio.wav")
                    phrase = result["text"]
                    print(f"You said: {phrase}")

                    wake_word = get_wake_word(phrase)
                    if wake_word is not None:
                        break
                    else:
                        print("Not a wake word. Try again.")
                except Exception as e:
                    print("Error transcribing audio: {0}".format(e))
                    continue

            print("Speak a prompt...")
            print("What can I help you with?")
            speak_text("What can I help you with?")
            audio = recognizer.listen(source)

            try:
                with open("audio_prompt.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                model = whisper.load_model("base")
                result = model.transcribe("audio_prompt.wav")
                user_input = result["text"]
                print(f"You said: {user_input}")
            except Exception as e:
                print("Error transcribing audio: {0}".format(e))
                continue

            if wake_word == GPT_WAKE_WORD:
                # Send prompt to GPT-3.5-turbo API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content":
                        "You are a helpful assistant."},
                        {"role": "user", "content": user_input},
                    ],
                    temperature=0.5,
                    max_tokens=150,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    n=1,
                    stop=["\nUser:"],
                )

                bot_response = response["choices"][0]["message"]["content"]

            print(f"Bot: {bot_response}")
            print(type(bot_response))
            speak_text(bot_response)

async def main2():
        global User_input
        User_input = None
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print(f"Say 'Go' to wake me up")
            socketio.emit('Q_Text', {'text': 'Say "Go" to wake me up.'}, namespace='/home')
            speak_text("Say go to wake me up")
            while True:
                audio = recognizer.listen(source)
                try:
                    with open("audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    # Use the preloaded tiny_model
                    model = whisper.load_model("base")
                    result = model.transcribe("audio.wav")
                    phrase = result["text"]
                    print(f"You said: {phrase}")

                    wake_word = get_wake_word(phrase)
                    if wake_word is not None:
                        break
                    else:
                        socketio.emit('Q_Text', {'text': 'Not a wake word. Try again.'}, namespace='/home')
                        print("Not a wake word. Try again.")
                        speak_text("Not a wake word, Try again")
                except Exception as e:
                    print("Error transcribing audio: {0}".format(e))
                    continue
            
            print("Speak a prompt...")
            socketio.emit('Q_Text', {'text': 'What can I help you with?'}, namespace='/home')
            print("What can I help you with?")
            speak_text("What can I help you with?")
            audio = recognizer.listen(source)

            try:
                with open("audio_prompt.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                model = whisper.load_model("base")
                result = model.transcribe("audio_prompt.wav")
                user_input = result["text"]
                print(f"You said: {user_input}")
                socketio.emit('My_text', {'text': user_input}, namespace='/home')
            except Exception as e:
                print("Error transcribing audio: {0}".format(e))

            if wake_word == GPT_WAKE_WORD:
                # Send prompt to GPT-3.5-turbo API
                User_input = user_input
                socketio.emit('Q_Text', {'text': 'Generating response...'}, namespace='/home')
                socketio.emit('VerifyR', {'result': True}, namespace='/home')
                print("Generating response...")
                speak_text("Generating response...")
                rep = get_openai_response(user_input)
                print(rep)
                speak_text(rep)


@socketio.on('Q_Text', namespace='/home')
async def handle_QText(data):
    voice_text = data['text']

@socketio.on('AcButton', namespace='/home')
async def handle_AcBtn(data):
    voice_text = data['result']

@socketio.on('VerifyR', namespace='/home')
async def handle_R(data):
    result = data['result']

@socketio.on('My_text', namespace='/home')
async def handle_My_event(data):
    voice_text = data['text']

if __name__ == "__main__":
    asyncio.run(main2())