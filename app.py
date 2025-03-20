
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import pyttsx3
import pyautogui
import subprocess
import os
import time
import wave

# -----------------------------
#  Initialization
# -----------------------------

# Text-to-speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 150)

# Dictation mode flag
is_dictating = False

# Map commands to application paths
app_paths = {
    "files": "nautilus",
    "text editor": "gedit",
    "chrome": "google-chrome",
    "vscode": "code",
    "terminal": "gnome-terminal",
}

# Mouse and keyboard actions
actions = {
    "left click": pyautogui.click,
    "right click": pyautogui.rightClick,
    "double click": pyautogui.doubleClick,
    "scroll up": lambda: pyautogui.scroll(200),
    "scroll down": lambda: pyautogui.scroll(-200),
    "move up": lambda: pyautogui.move(0, -50),
    "move down": lambda: pyautogui.move(0, 50),
    "move left": lambda: pyautogui.move(-50, 0),
    "move right": lambda: pyautogui.move(50, 0),
    "enter": lambda: pyautogui.press("enter"),
    "backspace": lambda: pyautogui.press("backspace"),
    "space": lambda: pyautogui.press("space"),
    "tab": lambda: pyautogui.press("tab"),
    "escape": lambda: pyautogui.press("esc"),
    "close window": lambda: pyautogui.hotkey("alt", "f4"),
    "switch window": lambda: pyautogui.hotkey("alt", "tab"),
    "copy": lambda: pyautogui.hotkey("ctrl", "c"),
    "paste": lambda: pyautogui.hotkey("ctrl", "v"),
    "cut": lambda: pyautogui.hotkey("ctrl", "x"),
    "select all": lambda: pyautogui.hotkey("ctrl", "a"),
    "save": lambda: pyautogui.hotkey("ctrl", "s"),
    "undo": lambda: pyautogui.hotkey("ctrl", "z"),
    "redo": lambda: pyautogui.hotkey("ctrl", "y"),
}


# -----------------------------
#  Utility Functions
# -----------------------------

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()


def record_and_recognize():
    """Record audio and recognize speech using sounddevice."""
    fs = 16000
    duration = 5  # Max recording duration
    speak("Listening...")

    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()

        # Save recording to WAV
        with wave.open("output.wav", "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(fs)
            f.writeframes(recording.tobytes())

        # Recognize speech
        recognizer = sr.Recognizer()
        with sr.AudioFile("output.wav") as source:
            audio = recognizer.record(source)

        command = recognizer.recognize_google(audio).lower()
        print(f"Recognized: {command}")
        return command

    except Exception as e:
        print(f"Error: {e}")
        return ""


def get_app_path(app_name):
    """Get application path from dictionary or return the name."""
    return app_paths.get(app_name, app_name)


def is_app_running(app_name):
    """Check if an app is running."""
    try:
        result = subprocess.run(["pgrep", "-f", app_name], stdout=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False


def focus_existing_window(app_name):
    """Focus on an existing app window."""
    try:
        result = subprocess.run(["wmctrl", "-l"], stdout=subprocess.PIPE)
        windows = result.stdout.decode().lower()

        if app_name.lower() in windows:
            subprocess.run(["wmctrl", "-a", app_name], check=True)
            speak(f"Switched to {app_name}")
            return True
    except subprocess.CalledProcessError:
        pass
    return False


# -----------------------------
#  Application and Dictation Control
# -----------------------------

def open_application(command):
    """Open or switch to an application."""
    app_name = command.replace("open ", "").strip()
    app_path = get_app_path(app_name)

    print(f"Opening: {app_name}")  

    if is_app_running(app_name):
        print(f"{app_name} is already running.")
        if not focus_existing_window(app_name):
            speak(f"Could not focus on {app_name}, opening a new instance.")
            subprocess.Popen([app_path])
    else:
        speak(f"Opening {app_name}")
        try:
            subprocess.Popen([app_path])
            time.sleep(2)
            speak(f"{app_name} opened")
        except Exception as e:
            speak(f"Could not open {app_name}: {str(e)}")
            print(f"Error: {e}")


def handle_special_commands(text):
    """Handle special commands and punctuation during dictation."""
    replacements = {
        "comma": ",",
        "dot": ".",
        "period": ".",
        "question mark": "?",
        "exclamation mark": "!",
        "colon": ":",
        "semicolon": ";",
        "apostrophe": "'",
        "quote": "\"",
        "open bracket": "[",
        "close bracket": "]",
        "open parenthesis": "(",
        "close parenthesis": ")",
        "hashtag": "#",
        "dollar sign": "$",
        "percent": "%",
        "ampersand": "&",
        "asterisk": "*",
        "hyphen": "-",
        "dash": "-",
        "underscore": "_",
        "plus": "+",
        "equal": "=",
        "space": " ",
        "backspace": "\b",
        "tab": "\t",
        "new line": "\n",
        "enter": "\n"
    }

    words = text.split()

    for word in words:
        if word in replacements:
            symbol = replacements[word]

            if symbol == "\b":
                pyautogui.press("backspace")
            elif symbol == "\n":
                pyautogui.press("enter")
            elif symbol == "\t":
                pyautogui.press("tab")
            elif symbol == " ":
                pyautogui.press("space")
            else:
                pyautogui.typewrite(symbol)
        else:
            pyautogui.typewrite(word + " ")


def enter_text():
    """Activate dictation mode."""
    global is_dictating

    while is_dictating:
        print("Dictating...")
        text = record_and_recognize()

        if "stop dictating" in text:
            is_dictating = False
            speak("Dictation mode stopped.")
            break
        elif text:
            handle_special_commands(text)
        else:
            speak("No text recognized. Try again.")


# -----------------------------
#  Main Action Handler
# -----------------------------

def perform_action(command):
    """Execute mouse, keyboard, app, or dictation actions."""
    global is_dictating

    if command in actions:
        actions[command]()
        speak(f"{command} performed")

    elif "open" in command:
        open_application(command)

    elif "start dictating" in command:
        if not is_dictating:
            is_dictating = True
            speak("Dictation mode enabled. Start speaking.")
            enter_text()
        else:
            speak("Dictation mode is already active.")

    elif "stop dictating" in command:
        is_dictating = False
        speak("Dictation mode stopped.")
        
    elif "exit" in command:
        speak("Exiting voice control")
        exit()
    
    else:
        speak("Command not recognized")


# -----------------------------
#  Main Loop
# -----------------------------

if __name__ == "__main__":
    speak("Voice control activated. Say a command.")
    
    while True:
        command = record_and_recognize()
        if command:
            perform_action(command)
