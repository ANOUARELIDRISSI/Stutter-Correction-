import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog, ttk
import sounddevice as sd
import scipy.io.wavfile as wav
import os
from gtts import gTTS
import whisper
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("api_key"))

# Correct stutter using Groq API
def correct_stutter(text):
    try:
        # Define the prompt for stutter correction
        prompt = (
            f"Correct the following stuttered text to make it fluent and natural. "
            f"Remove any repetitions of  words, but keep the meaning intact. "
            f"Here is the text: {text}") 
        # Call the Groq API
        response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",  # Use the appropriate model name
            max_tokens=512,
        )

        # Extract the corrected text
        corrected_text = response.choices[0].message.content
        return corrected_text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to correct stutter: {str(e)}")
        return text  # Return the original text if correction fails

# Record audio
def record_audio(duration=5, sample_rate=16000, filename="recorded_audio.wav"):
    print("Recording...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    wav.write(filename, sample_rate, audio)  # Save as WAV file
    print(f"Recording saved as {filename}")

# Transcribe audio using Whisper
def transcribe_audio(filename="recorded_audio.wav", language="en"):
    model = whisper.load_model("base")  # Use "base" for faster performance
    result = model.transcribe(filename, language=language)
    return result["text"]

# Generate corrected audio
def text_to_speech(text, filename="corrected_audio.mp3"):
    tts = gTTS(text=text, lang="en")
    tts.save(filename)
    print(f"Corrected audio saved as {filename}")
    return filename

# Play audio
def play_audio(filename):
    os.system(f"start {filename}" if os.name == "nt" else f"afplay {filename}")

# GUI Application
class StutterCorrectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stutter Corrector")
        self.root.geometry("600x400")
        self.output_directory = os.getcwd()  # Default output directory

        # Record Button
        self.record_button = tk.Button(root, text="Record Audio", command=self.record_and_process)
        self.record_button.pack(pady=10)

        # Play Recorded Audio Button
        self.play_recorded_button = tk.Button(root, text="Play Recorded Audio", command=self.play_recorded_audio)
        self.play_recorded_button.pack(pady=10)

        # Language Selection
        self.language_var = tk.StringVar(value="en")
        self.language_label = tk.Label(root, text="Select Language:")
        self.language_label.pack()
        self.language_menu = tk.OptionMenu(root, self.language_var, "en", "es", "fr", "de", "hi")  # Add more languages as needed
        self.language_menu.pack(pady=10)

        # Recorded Text Section
        self.input_label = tk.Label(root, text="Recorded Text:")
        self.input_label.pack()
        self.input_textbox = scrolledtext.ScrolledText(root, width=70, height=5)
        self.input_textbox.pack()

        # Corrected Text Section
        self.corrected_label = tk.Label(root, text="Corrected Text:")
        self.corrected_label.pack()
        self.corrected_textbox = scrolledtext.ScrolledText(root, width=70, height=5)
        self.corrected_textbox.pack()

        # Play and Save Audio Button
        self.play_button = tk.Button(root, text="Play Corrected Audio", command=self.play_corrected_audio)
        self.play_button.pack(pady=10)

        # Save Corrected Text Button
        self.save_text_button = tk.Button(root, text="Save Corrected Text", command=self.save_corrected_text)
        self.save_text_button.pack(pady=10)

        # Save Corrected Audio Button
        self.save_audio_button = tk.Button(root, text="Save Corrected Audio", command=self.save_corrected_audio)
        self.save_audio_button.pack(pady=10)

        # Clear Text Button
        self.clear_button = tk.Button(root, text="Clear Text", command=self.clear_text)
        self.clear_button.pack(pady=10)

        # Batch Process Button
        self.batch_process_button = tk.Button(root, text="Batch Process", command=self.batch_process)
        self.batch_process_button.pack(pady=10)

        # Set Output Directory Button
        self.output_directory_button = tk.Button(root, text="Set Output Directory", command=self.set_output_directory)
        self.output_directory_button.pack(pady=10)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="indeterminate")
        self.progress_bar.pack(pady=10)

        # Status Label
        self.status_label = tk.Label(root, text="Ready", fg="blue")
        self.status_label.pack(pady=10)

    def record_and_process(self):
        try:
            # Update status
            self.status_label.config(text="Recording...")
            self.progress_bar.start()

            # Ask user for recording duration
            duration = simpledialog.askinteger("Recording Duration", "Enter recording duration (seconds):", minvalue=1, maxvalue=60)
            if duration is None:  # User canceled the dialog
                self.status_label.config(text="Ready")
                self.progress_bar.stop()
                return

            # Record audio
            record_audio(duration=duration, filename="recorded_audio.wav")
            self.status_label.config(text="Transcribing...")

            # Transcribe audio
            language = self.language_var.get()
            transcribed_text = transcribe_audio("recorded_audio.wav", language=language)
            self.input_textbox.delete("1.0", tk.END)
            self.input_textbox.insert(tk.END, transcribed_text)
            self.status_label.config(text="Correcting stutter...")

            # Correct stutter
            # Correct stutter
            corrected_text = correct_stutter(transcribed_text)
            # Extract text after the colon
            if ":" in transcribed_text:
                corrected_text = transcribed_text.split(":", 1)[1].strip()  # Split at the first colon and take the part after it
            else:
                corrected_text = transcribed_text  # If there's no colon, use the full text

            # Update the corrected_textbox with the extracted text
            self.corrected_textbox.delete("1.0", tk.END)
            self.corrected_textbox.insert(tk.END, corrected_text)

            self.status_label.config(text="Generating corrected audio...")

            # Generate corrected audio
            text_to_speech(corrected_text, filename="corrected_audio.mp3")
            self.status_label.config(text="Ready")
            self.progress_bar.stop()

            messagebox.showinfo("Success", "Audio processed and corrected successfully!")
        except Exception as e:
            self.status_label.config(text="Ready")
            self.progress_bar.stop()
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def play_recorded_audio(self):
        try:
            if not os.path.exists("recorded_audio.wav"):
                messagebox.showwarning("File Missing", "No recorded audio found. Please record audio first.")
                return
            play_audio("recorded_audio.wav")
        except Exception as e:
            messagebox.showerror("Error", f"Could not play audio: {str(e)}")

    def play_corrected_audio(self):
        try:
            if not os.path.exists("corrected_audio.mp3"):
                messagebox.showwarning("File Missing", "Corrected audio file not found. Please process audio first.")
                return
            play_audio("corrected_audio.mp3")
        except Exception as e:
            messagebox.showerror("Error", f"Could not play audio: {str(e)}")

    def save_corrected_text(self):
        corrected_text = self.corrected_textbox.get("1.0", tk.END).strip()
        if not corrected_text:
            messagebox.showwarning("No Text", "No corrected text to save.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")], initialdir=self.output_directory)
        if file_path:
            with open(file_path, "w") as file:
                file.write(corrected_text)
            messagebox.showinfo("Saved", f"Corrected text saved to {file_path}")

    def save_corrected_audio(self):
        if not os.path.exists("corrected_audio.mp3"):
            messagebox.showwarning("File Missing", "Corrected audio file not found. Please process audio first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 Files", "*.mp3")], initialdir=self.output_directory)
        if file_path:
            os.replace("corrected_audio.mp3", file_path)
            messagebox.showinfo("Saved", f"Corrected audio saved to {file_path}")

    def clear_text(self):
        self.input_textbox.delete("1.0", tk.END)
        self.corrected_textbox.delete("1.0", tk.END)

    def batch_process(self):
        try:
            # Ask user to select multiple audio files
            file_paths = filedialog.askopenfilenames(filetypes=[("WAV Files", "*.wav")])
            if not file_paths:
                return

            # Process each file
            for file_path in file_paths:
                # Transcribe audio
                transcribed_text = transcribe_audio(file_path, language=self.language_var.get())
                corrected_text = correct_stutter(transcribed_text)

                # Save corrected text
                output_file = os.path.splitext(file_path)[0] + "_corrected.txt"
                with open(output_file, "w") as file:
                    file.write(corrected_text)

                # Generate corrected audio
                output_audio_file = os.path.splitext(file_path)[0] + "_corrected.mp3"
                text_to_speech(corrected_text, filename=output_audio_file)

            messagebox.showinfo("Success", f"Processed {len(file_paths)} files successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def set_output_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_directory = directory
            messagebox.showinfo("Output Directory", f"Output directory set to {directory}")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = StutterCorrectorApp(root)
    root.mainloop()