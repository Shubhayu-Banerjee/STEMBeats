import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import math
import pygame
import time
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import os
import re
import numpy as np
import sounddevice as sd
from sympy import false

# Set customtkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SoundLoop:
    """Class to handle continuous sound playback"""

    def __init__(self, app, sound_file):
        self.app = app
        self.sound_file = sound_file
        self.playing = False
        self.after_id = None

    def start(self):
        """Start playing the sound in a loop"""
        self.playing = True
        self.play_once()

    def play_once(self):
        """Play the sound once and schedule the next playback"""
        if not self.playing:
            return

            # Play the sound
        if self.sound_file in self.app.sounds and self.app.sounds[self.sound_file]:
            self.app.sounds[self.sound_file].play()

            # 🔥 Calculate delay based on tempo slider
        try:
            bpm = int(self.app.tempo_slider.get()) + 50  # Matches your `adjust_tempo()` logic
            delay = int(60000 / bpm)  # Convert BPM to ms delay
        except:
            delay = 1000  # Fallback to 1 second

            # Schedule the next loop
        self.after_id = self.app.root.after(delay, self.play_once)

    def stop(self):
        """Stop the sound loop"""
        self.playing = False
        if self.after_id:
            self.app.root.after_cancel(self.after_id)
            self.after_id = None


class PhysicsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("StemBeats")
        self.root.geometry("1200x700")

        # Configure dark blue-purple gradient background
        self.root.configure(fg_color=("#1a1a2e", "#4a148c"))

        self._current_stream = None
        self._current_phase = 0

        # Initialize pygame for sound
        pygame.mixer.init()

        # Try to load sounds
        self.sounds = {}
        self.load_sounds()

        # Define the formulas and their descriptions
        self.formulas = {
            "T = 2π√(L/g)": {
                "name": "Pendulum Period",
                "description": "Period of a simple pendulum",
                "visual": "pendulum",
                "sound": "piano.mp3",
                "aliases": ["T = 2pi√(L/g)", "T = 2*pi*√(L/g)", "T = 2*π*√(L/g)"]
            },
            "t = √(2h/g)": {
                "name": "Free Fall Time",
                "description": "Time for an object to fall from height h",
                "visual": "freefall",
                "sound": "drum.mp3",
                "aliases": ["t = sqrt(2h/g)", "t = √(2*h/g)"]
            },
            "F = ma": {
                "name": "Newton's Second Law",
                "description": "Force equals mass times acceleration",
                "visual": "force",
                "sound": None,
                "aliases": []
            },
            "F = mv²/r": {
                "name": "Centripetal Force",
                "description": "Force needed for circular motion",
                "visual": "orbit",
                "sound": "snare.mp3",
                "aliases": ["F = mv^2/r", "F = m*v²/r", "F = m*v^2/r"]
            },
            "V = IR": {
                "name": "Ohm's Law",
                "description": "Relationship between voltage, current and resistance",
                "visual": "circuit",
                "sound": None,
                "aliases": ["V = I*R"]
            },
            "y = A sin(ωt + φ)": {
                "name": "Simple Harmonic Motion",
                "description": "Wave equation for simple harmonic motion",
                "visual": "wave",
                "sound": "synth.mp3",
                "aliases": ["y = A*sin(ωt + φ)", "y = A sin(wt + φ)", "y = A*sin(wt + φ)"]
            }
        }

        # Keep track of entered formulas
        self.entered_formulas = []

        # Current animation
        self.current_animation = None
        self.animation_running = False
        self.animation_after_id = None

        # Sound playing states
        self.sound_states = {}  # Formula -> playing state
        self.sound_loops = {}  # Formula -> sound loop reference

        # Create UI components
        self.create_ui()

        # Start with no animation
        self.draw_placeholder()

    def load_sounds(self):
        """Load all sound files"""
        sound_files = ["correct.mp3", "drum.mp3","piano_low.mp3", "piano_mid.mp3","piano_high.mp3", "snare.mp3", "synth.mp3"]
        for sound_file in sound_files:
            try:
                self.sounds[sound_file] = pygame.mixer.Sound(sound_file)
            except:
                print(f"Warning: Could not load {sound_file} sound file")
                self.sounds[sound_file] = None

    def create_ui(self):
        # Create main frames with gradient styling
        self.main_frame = ctk.CTkFrame(self.root, fg_color=("gray85", "#1a1a2e"), border_width=2, border_color="#4a148c")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left frame for visualizations
        self.visual_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray90", "#16213e"))
        self.visual_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Canvas for animations with dark background
        self.canvas = tk.Canvas(self.visual_frame, bg="#0f0c29", width=600, height=600)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # Right frame for formula entry and list with gradient styling
        self.formula_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray90", "#1a1a2e"))
        self.formula_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Label for formula entry with modern font
        self.entry_label = ctk.CTkLabel(
            self.formula_frame,
            text="Enter Physics Formula:",
            font=("Roboto", 14, "bold"),
            text_color=("black", "#e2e2e2")
        )
        self.entry_label.pack(pady=(10, 5))

        # Entry for formula with modern styling
        self.formula_entry = ctk.CTkEntry(
            self.formula_frame,
            width=300,
            font=("Roboto", 14),
            fg_color=("white", "#2a2a4a"),
            border_color="#4a148c",
            placeholder_text="Type a formula and press Enter..."
        )
        self.formula_entry.pack(pady=5)
        self.formula_entry.bind("<Return>", self.check_formula)

        # Submit button with gradient styling
        self.submit_button = ctk.CTkButton(
            self.formula_frame,
            text="Submit",
            command=self.check_formula,
            fg_color=("#4a148c", "#6a3093"),
            hover_color=("#6a3093", "#8e44ad"),
            font=("Roboto", 12, "bold")
        )
        self.submit_button.pack(pady=5)

        # Label for formula list
        self.list_label = ctk.CTkLabel(
            self.formula_frame,
            text="Discovered Formulas:",
            font=("Roboto", 14, "bold"),
            text_color=("black", "#e2e2e2")
        )
        self.list_label.pack(pady=(20, 5))

        # Frame for formula list with scrollable content
        self.list_frame = ctk.CTkScrollableFrame(
            self.formula_frame,
            width=350,
            height=400,
            fg_color=("gray90", "#16213e")
        )
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Help button with modern styling
        self.help_button = ctk.CTkButton(
            self.formula_frame,
            text="Help",
            command=self.show_help,
            fg_color=("#4a148c", "#6a3093"),
            hover_color=("#6a3093", "#8e44ad"),
            font=("Roboto", 12, "bold")
        )
        self.help_button.pack(pady=10)

        # Master volume control frame
        self.volume_frame = ctk.CTkFrame(self.formula_frame, fg_color="transparent")
        self.volume_frame.pack(side="left", padx=10, pady=5, fill="x", expand=True)

        self.volume_label = ctk.CTkLabel(
            self.volume_frame,
            text="Volume:",
            font=("Roboto", 12),
            text_color=("black", "#e2e2e2")
        )
        self.volume_label.pack(side="left", padx=5)

        self.volume_slider = ctk.CTkSlider(
            self.volume_frame,
            from_=0,
            to=100,
            width=120,
            progress_color=("#4a148c", "#6a3093"),
            button_color=("#6a3093", "#8e44ad"),
            button_hover_color=("#8e44ad", "#9b59b6")
        )
        self.volume_slider.pack(side="left", padx=10)
        self.volume_slider.set(50)  # Default to 50% volume
        self.volume_slider.configure(command=self.adjust_volume)

        self.volume_value = ctk.CTkLabel(
            self.volume_frame,
            text="50%",
            font=("Roboto", 12),
            text_color=("black", "#e2e2e2")
        )
        self.volume_value.pack(side="left", padx=5)

        # Master Tempo control frame
        self.tempo_frame = ctk.CTkFrame(self.formula_frame, fg_color="transparent")
        self.tempo_frame.pack(side="left", padx=10, pady=5, fill="x", expand=True)

        self.tempo_label = ctk.CTkLabel(
            self.tempo_frame,
            text="Tempo:",
            font=("Roboto", 12),
            text_color=("black", "#e2e2e2")
        )
        self.tempo_label.pack(side="left", padx=20)

        self.tempo_slider = ctk.CTkSlider(
            self.tempo_frame,
            from_=0,
            to=100,
            width=120,
            progress_color=("#4a148c", "#6a3093"),
            button_color=("#6a3093", "#8e44ad"),
            button_hover_color=("#8e44ad", "#9b59b6")
        )
        self.tempo_slider.pack(side="left", padx=10)
        self.tempo_slider.set(50)  # Default to 50% tempo
        self.tempo_slider.configure(command=self.adjust_tempo)

        self.tempo_value = ctk.CTkLabel(
            self.tempo_frame,
            text="100bpm",
            font=("Roboto", 12),
            text_color=("black", "#e2e2e2")
        )
        self.tempo_value.pack(side="right", padx=5)

    def adjust_volume(self, value):
        """Adjust the volume of all sounds"""
        volume = int(value)
        self.volume_value.configure(text=f"{volume}%")

        # Set volume for all sounds (0.0 to 1.0)
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(volume / 100)

    def adjust_tempo(self, value):
        """Adjust the volume of all sounds"""
        tempo = int(value) + 50
        self.tempo_value.configure(text=f"{tempo}bpm")
        return tempo

    def play_sound(self, sound_file):
        """Play a sound once"""
        if sound_file in self.sounds and self.sounds[sound_file]:
            self.sounds[sound_file].play()

    def toggle_sound_loop(self, formula):
        """Toggle continuous sound loop for a formula"""
        # Check if sound is enabled for this formula
        if formula not in self.sound_states:
            self.sound_states[formula] = False

        # Get the sound file for this formula
        sound_file = self.formulas[formula].get("sound")
        if not sound_file or sound_file not in self.sounds or not self.sounds[sound_file]:
            return

        # Toggle the state
        self.sound_states[formula] = not self.sound_states[formula]

        # If sound should play, start a loop
        if self.sound_states[formula]:
            # Store sound loop reference
            if formula not in self.sound_loops:
                self.sound_loops[formula] = SoundLoop(self, sound_file)
            self.sound_loops[formula].start()
        else:
            # Stop the sound loop
            if formula in self.sound_loops:
                self.sound_loops[formula].stop()

    def show_help(self):
        help_text = "Enter physics formulas to see them visualized with sound.\n\n"
        help_text += "Try to discover these important physics formulas:\n"
        help_text += "- Pendulum period (T = 2π√(L/g))\n"
        help_text += "- Free fall time (t = √(2h/g))\n"
        help_text += "- Newton's Second Law (F = ma)\n"
        help_text += "- Centripetal Force (F = mv²/r)\n"
        help_text += "- Ohm's Law (V = IR)\n"
        help_text += "- Simple Harmonic Motion (y = A sin(ωt + φ))\n\n"
        help_text += "Each formula has unique visualizations and sounds!\n"
        help_text += "Click on visualizations to change parameters.\n\n"
        help_text += "Sound Effects:\n"
        help_text += "- Pendulum: Piano sounds at swing extremes\n"
        help_text += "- Free Fall: Drum sound when object hits ground\n"
        help_text += "- Centripetal Force: Snare beat on each 1/8th of a orbit completion\n"
        help_text += "- Simple Harmonic Motion: Synth tones matching wave frequency"

        messagebox.showinfo("Help", help_text)

    def check_formula(self, event=None):
        formula = self.formula_entry.get().strip()

        if not formula:
            return

        # Check if formula matches any correct formula or its aliases
        found_match = False
        matched_formula = None

        for correct_formula, info in self.formulas.items():
            # Remove spaces and standardize for comparison
            clean_input = re.sub(r'\s+', '', formula.lower())
            clean_correct = re.sub(r'\s+', '', correct_formula.lower())

            # Check direct match
            if clean_input == clean_correct:
                found_match = True
                matched_formula = correct_formula
                break

            # Check aliases
            for alias in info["aliases"]:
                clean_alias = re.sub(r'\s+', '', alias.lower())
                if clean_input == clean_alias:
                    found_match = True
                    matched_formula = correct_formula
                    break

            if found_match:
                break

        # If a match was found and not already entered
        if found_match and matched_formula not in self.entered_formulas:
            self.entered_formulas.append(matched_formula)
            self.add_formula_to_list(matched_formula)

            # Play correct sound
            if "correct.mp3" in self.sounds and self.sounds["correct.mp3"]:
                self.sounds["correct.mp3"].play()

            # Start the corresponding visualization
            self.start_visualization(matched_formula)

            # Clear the entry
            self.formula_entry.delete(0, tk.END)
            return
        elif found_match and matched_formula in self.entered_formulas:
            messagebox.showinfo("Already Discovered", "You've already discovered this formula!")
        else:
            messagebox.showinfo("Incorrect Formula",
                                "That's not a recognized physics formula, or it's not in the correct format.")

        # Clear the entry
        self.formula_entry.delete(0, tk.END)

    def add_formula_to_list(self, formula):
        # Create frame for formula item with gradient styling
        item_frame = ctk.CTkFrame(
            self.list_frame,
            fg_color=("gray90", "#1a1a2e"),
            border_color="#4a148c",
            border_width=1
        )
        item_frame.pack(fill="x", pady=5)

        # Get formula info
        formula_info = self.formulas[formula]

        # Display formula with its name
        formula_label = ctk.CTkLabel(
            item_frame,
            text=f"{formula_info['name']}: {formula}",
            font=("Roboto", 14, "bold"),
            text_color=("black", "#e2e2e2")
        )
        formula_label.pack(anchor="w", padx=5, pady=2)

        # Display description
        desc_label = ctk.CTkLabel(
            item_frame,
            text=formula_info['description'],
            font=("Roboto", 12),
            text_color=("black", "#b8b8b8")
        )
        desc_label.pack(anchor="w", padx=5, pady=2)

        # Button frame
        button_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        button_frame.pack(anchor="w", padx=5, pady=5, fill="x")

        # Button to show this visualization again
        show_button = ctk.CTkButton(
            button_frame,
            text="Visualize",
            width=80,
            command=lambda f=formula: self.start_visualization(f),
            fg_color=("#4a148c", "#6a3093"),
            hover_color=("#6a3093", "#8e44ad"),
            font=("Roboto", 12)
        )
        show_button.pack(side="left", padx=(0, 10))

        # Sound toggle button if formula has sound
        if formula_info.get("sound"):
            # Initialize the state
            if formula not in self.sound_states:
                self.sound_states[formula] = False

            sound_button = ctk.CTkButton(
                button_frame,
                text="Play Sound",
                width=100,
                command=lambda f=formula: self.toggle_sound_button(f, sound_button),
                fg_color=("#4a148c", "#6a3093"),
                hover_color=("#6a3093", "#8e44ad"),
                font=("Roboto", 12)
            )
            sound_button.pack(side="left")

            # Store button reference for updating text
            sound_button.formula = formula
            sound_button.is_playing = False

    def toggle_sound_button(self, formula, button):
        """Toggle sound and update button text"""
        # Toggle sound
        self.toggle_sound_loop(formula)

        # Update button text
        if self.sound_states.get(formula, False):
            button.configure(text="Stop Sound")
        else:
            button.configure(text="Play Sound")

    def start_visualization(self, formula):
        # Stop any current animation
        if self.animation_after_id:
            self.root.after_cancel(self.animation_after_id)
            self.animation_after_id = None

        # Stop any sine wave playing
        self.stop_sine()

        # Set the current animation
        visual_type = self.formulas[formula]["visual"]
        self.current_animation = visual_type
        self.animation_running = True

        # Start the animation
        if visual_type == "pendulum":
            self.animate_pendulum()
        elif visual_type == "freefall":
            self.animate_freefall()
        elif visual_type == "force":
            self.animate_force()
        elif visual_type == "orbit":
            self.animate_orbit()
        elif visual_type == "circuit":
            self.animate_circuit()
        elif visual_type == "wave":
            self.animate_wave()

    def draw_placeholder(self):
        # Clear canvas
        self.canvas.delete("all")

        # Draw a placeholder with gradient text
        self.canvas.create_text(
            300, 250,
            text="Enter a physics formula to see visualization",
            fill="#e2e2e2",
            font=("Roboto", 16)
        )

        self.canvas.create_text(
            300, 300,
            text="Check the Help button for formula hints",
            fill="#9b59b6",
            font=("Roboto", 14)
        )

    def animate_pendulum(self, angle=30, length=200, time_passed=0, last_extreme=False):
        if not self.animation_running or self.current_animation != "pendulum":
            return

        # Clear canvas
        self.canvas.delete("all")

        # Draw title
        self.canvas.create_text(
            300, 30,
            text="Pendulum Period: T = 2π√(L/g)",
            fill="#e2e2e2",
            font=("Roboto", 16, "bold")
        )

        # Constants
        g = 9.8  # gravity

        # Calculate period
        period = 2 * math.pi * math.sqrt(length / 100 / g)

        # Calculate current angle
        amplitude = math.radians(angle)
        omega = 2 * math.pi / period
        current_angle = amplitude * math.sin(omega * time_passed)

        # Calculate pendulum position
        origin_x, origin_y = 300, 100
        bob_x = origin_x + length * math.sin(current_angle)
        bob_y = origin_y + length * math.cos(current_angle)

        # Draw pendulum
        self.canvas.create_line(origin_x, origin_y, bob_x, bob_y, fill="#9b59b6", width=3)
        self.canvas.create_oval(bob_x - 15, bob_y - 15, bob_x + 15, bob_y + 15, fill="#e74c3c")

        # Draw mount
        self.canvas.create_rectangle(origin_x - 20, origin_y - 5, origin_x + 20, origin_y + 5, fill="#3498db")

        # Draw time info
        self.canvas.create_text(
            300, 450,
            text=f"Period: {period:.2f} seconds | Time: {time_passed:.2f} seconds",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        # Draw length info
        self.canvas.create_text(
            300, 470,
            text=f"Length: {length / 100:.2f} meters",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        # Draw audio info
        self.canvas.create_text(
            300, 490,
            text="Sound: Piano at extremes, background tone based on period",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Controls
        self.canvas.create_text(
            300, 520,
            text="Click to change pendulum length",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Add click handler for changing length
        self.canvas.bind("<Button-1>", lambda e: self.change_pendulum_length())

        # Play sounds at extremes of swing
        # Check if pendulum is at an extreme (left or right)
        at_extreme = False
        if abs(abs(current_angle) - amplitude) < 0.05:  # Close to amplitude
            at_extreme = True

        # Play piano sound at extremes
        if at_extreme and not last_extreme:
            length_meters = length / 100  # convert cm to meters

            # Choose the appropriate sample
            if length_meters < 1.6:
                sample_name = "piano_high.mp3"
            elif length_meters < 2.3:
                sample_name = "piano_mid.mp3"
            else:
                sample_name = "piano_low.mp3"

            # Play the sample if it's loaded
            if sample_name in self.sounds:
                self.sounds[sample_name].play()

        # Update time and continue animation
        self.animation_after_id = self.root.after(50, lambda: self.animate_pendulum(angle, length, time_passed + 0.05,
                                                                                    at_extreme))

    def change_pendulum_length(self):
        if self.current_animation == "pendulum":
            # Generate random length between 100 and 300
            new_length = np.random.randint(100, 300)

            # Restart animation with new length
            if self.animation_after_id:
                self.root.after_cancel(self.animation_after_id)

            self.animate_pendulum(angle=30, length=new_length, time_passed=0)

    def animate_freefall(self, height=400, time_passed=0, was_at_bottom=False):
        if not self.animation_running or self.current_animation != "freefall":
            return

        # Clear canvas
        self.canvas.delete("all")

        # Draw title
        self.canvas.create_text(
            300, 30,
            text="Free Fall Time: t = √(2h/g)",
            fill="#e2e2e2",
            font=("Roboto", 16, "bold")
        )

        # Constants
        g = 9.8  # gravity

        # Calculate total fall time
        total_time = math.sqrt(2 * (height / 100) / g)

        # Calculate cycle time (drop + reset)
        cycle_time = total_time + 0.5  # Add 0.5s for reset animation

        # Calculate current time in the cycle
        cycle_position = time_passed % cycle_time

        # Determine if in falling phase or reset phase
        in_falling_phase = cycle_position <= total_time

        # Calculate current position
        initial_y = 80
        max_y = initial_y + height

        at_bottom = False
        if in_falling_phase:
            # Normal falling physics: y = y₀ + 0.5gt²
            at_bottom = false
            was_at_bottom = false
            current_y = initial_y + 0.5 * g * (cycle_position ** 2) * 100
            if current_y > max_y:
                current_y = max_y
        else:
            current_y = initial_y
            at_bottom = True

        # Draw building/reference
        self.canvas.create_rectangle(160, initial_y, 440, max_y, outline="#3498db")

        # Draw ground
        self.canvas.create_line(100, max_y, 500, max_y, fill="#2ecc71", width=3)

        # Draw ball
        self.canvas.create_oval(290 - 10, current_y - 10, 290 + 10, current_y + 10, fill="#e74c3c")

        # Draw time info
        self.canvas.create_text(
            300, 500,
            text=f"Fall time: {total_time:.2f} seconds | Current cycle: {cycle_position:.2f}/{cycle_time:.2f} seconds",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        # Draw height info
        self.canvas.create_text(
            300, 520,
            text=f"Height: {height / 100:.2f} meters",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        # Draw audio info
        self.canvas.create_text(
            300, 540,
            text="Sound: Drum when object hits ground",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Controls
        self.canvas.create_text(
            300, 570,
            text="Click to change drop height",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Add click handler for changing height
        self.canvas.bind("<Button-1>", lambda e: self.change_freefall_height())

        # Check if ball just hit ground
        just_hit = at_bottom and not was_at_bottom


        # Play drum sound when ball hits ground
        if just_hit and "drum.mp3" in self.sounds and self.sounds["drum.mp3"]:
            self.sounds["drum.mp3"].play()
            was_at_bottom = True

        # Update time and continue animation
        self.animation_after_id = self.root.after(50,lambda: self.animate_freefall(height, time_passed + 0.05, at_bottom))

    def change_freefall_height(self):
        if self.current_animation == "freefall":
            # Generate random height between 200 and 400
            new_height = np.random.randint(200, 400)

            # Restart animation with new height
            if self.animation_after_id:
                self.root.after_cancel(self.animation_after_id)

            self.animate_freefall(height=new_height, time_passed=0)

    def animate_force(self, mass=2.0, force=10.0, time_passed=0):
        if not self.animation_running or self.current_animation != "force":
            return

        # Clear canvas
        self.canvas.delete("all")

        # Draw title
        self.canvas.create_text(
            300, 30,
            text="Newton's Second Law: F = ma",
            fill="#e2e2e2",
            font=("Roboto", 16, "bold")
        )

        # Calculate acceleration (a = F/m)
        acceleration = force / mass

        # Calculate cycle time - time until reset
        cycle_time = 6.0  # seconds
        cycle_position = time_passed % cycle_time

        # Check if we're in reset phase
        reset_phase = cycle_position > 5.0

        # Calculate position
        if not reset_phase:
            # Normal motion: x = x₀ + 0.5at²
            distance = 0.5 * acceleration * (cycle_position ** 2)
            pos_x = 100 + min(distance * 10, 400)  # Scale and limit to canvas
        else:
            # Reset animation
            reset_progress = (cycle_position - 5.0)
            pos_x = max(100, 500 - reset_progress * 800)

        # Draw ground
        self.canvas.create_line(100, 350, 500, 350, fill="#2ecc71", width=3)

        # Draw object
        size = 30 + mass * 10  # Size based on mass
        self.canvas.create_rectangle(
            pos_x - size / 2, 350 - size,
            pos_x + size / 2, 350,
            fill="#3498db"
        )

        # Draw force arrow
        arrow_length = force * 5
        self.canvas.create_line(
            pos_x, 350 - size / 2,
                   pos_x + arrow_length, 350 - size / 2,
            fill="#e74c3c", width=3, arrow=tk.LAST
        )

        # Draw physics info
        self.canvas.create_text(
            300, 400,
            text=f"Mass: {mass} kg | Force: {force} N | Acceleration: {acceleration:.2f} m/s²",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        # Draw time and distance
        if not reset_phase:
            self.canvas.create_text(
                300, 430,
                text=f"Time: {cycle_position:.2f} s | Distance: {distance:.2f} m",
                fill="#e2e2e2",
                font=("Roboto", 12)
            )
        else:
            self.canvas.create_text(
                300, 430,
                text="Resetting position...",
                fill="#e2e2e2",
                font=("Roboto", 12)
            )

        # Controls
        self.canvas.create_text(
            300, 470,
            text="Click to change force and mass",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Add click handler for changing force and mass
        self.canvas.bind("<Button-1>", lambda e: self.change_force_mass())

        # Update time and continue animation
        self.animation_after_id = self.root.after(50, lambda: self.animate_force(mass, force, time_passed + 0.05))

    def change_force_mass(self):
        if self.current_animation == "force":
            # Generate random mass and force
            new_mass = round(np.random.uniform(1.0, 5.0), 1)
            new_force = round(np.random.uniform(5.0, 20.0), 1)

            # Restart animation with new parameters
            if self.animation_after_id:
                self.root.after_cancel(self.animation_after_id)

            self.animate_force(mass=new_mass, force=new_force, time_passed=0)

    def animate_orbit(self, radius=150, speed=1.0, time_passed=0, last_eigth=-1):
        if not self.animation_running or self.current_animation != "orbit":
            return

        # Clear canvas
        self.canvas.delete("all")

        # Draw title
        self.canvas.create_text(
            300, 30,
            text="Centripetal Force: F = mv²/r",
            fill="#e2e2e2",
            font=("Roboto", 16, "bold")
        )

        # Constants
        center_x, center_y = 300, 250
        mass = 1.0  # kg

        # Calculate period of orbit (T = 2πr/v)
        velocity = 50 * speed  # pixels per second
        period = 2 * math.pi * radius / velocity

        # Calculate current angle
        angle = (time_passed % period) / period * 2 * math.pi

        # Check if we just completed a cycle
        eigth_index = int((time_passed % period) / (period / 8))
        new_eigth = eigth_index != last_eigth

        # Calculate object position
        obj_x = center_x + radius * math.cos(angle)
        obj_y = center_y + radius * math.sin(angle)

        # Draw central object (sun/planet)
        self.canvas.create_oval(center_x - 20, center_y - 20, center_x + 20, center_y + 20, fill="#f1c40f")

        # Draw orbit path
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="#3498db", dash=(2, 4)
        )

        # Draw orbiting object
        self.canvas.create_oval(obj_x - 10, obj_y - 10, obj_x + 10, obj_y + 10, fill="#3498db")

        # Calculate centripetal force (F = mv²/r)
        force = mass * (velocity ** 2) / radius

        # Draw force vector (pointing to center)
        vector_length = min(30, force)
        vector_angle = math.atan2(center_y - obj_y, center_x - obj_x)
        vector_end_x = obj_x + vector_length * math.cos(vector_angle)
        vector_end_y = obj_y + vector_length * math.sin(vector_angle)

        self.canvas.create_line(
            obj_x, obj_y, vector_end_x, vector_end_y,
            fill="#e74c3c", width=2, arrow=tk.LAST
        )

        # Draw physics info
        self.canvas.create_text(
            300, 420,
            text=f"Mass: {mass} kg | Velocity: {velocity:.1f} m/s | Radius: {radius / 100:.1f} m",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        self.canvas.create_text(
            300, 450,
            text=f"Centripetal Force: {force:.2f} N | Period: {period:.2f} seconds",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        # Draw audio info
        self.canvas.create_text(
            300, 480,
            text="Sound: Snare beat on each orbit completion",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Controls
        self.canvas.create_text(
            300, 510,
            text="Click to change orbit radius and speed",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Add click handler for changing orbit parameters
        self.canvas.bind("<Button-1>", lambda e: self.change_orbit_parameters())

        # Play snare sound when completing a cycle
        if new_eigth and "snare.mp3" in self.sounds and self.sounds["snare.mp3"]:
            self.sounds["snare.mp3"].play()

        # Update time and continue animation
        self.animation_after_id = self.root.after(
            50, lambda: self.animate_orbit(radius, speed, time_passed + 0.05, eigth_index)
        )

    def change_orbit_parameters(self):
        if self.current_animation == "orbit":
            # Generate random radius and speed
            new_radius = np.random.randint(80, 200)
            new_speed = round(np.random.uniform(0.5, 2.0), 1)

            # Restart animation with new parameters
            if self.animation_after_id:
                self.root.after_cancel(self.animation_after_id)

            self.animate_orbit(radius=new_radius, speed=new_speed, time_passed=0)

    def animate_circuit(self, voltage=10.0, resistance=5.0, time_passed=0):
        if not self.animation_running or self.current_animation != "circuit":
            return

        # Clear canvas
        self.canvas.delete("all")

        # Draw title
        self.canvas.create_text(
            300, 30,
            text="Ohm's Law: V = IR",
            fill="#e2e2e2",
            font=("Roboto", 16, "bold")
        )

        # Calculate current (I = V/R)
        current = voltage / resistance

        # Draw battery
        battery_x, battery_y = 150, 250
        battery_width, battery_height = 40, 80

        # Battery body
        self.canvas.create_rectangle(
            battery_x - battery_width / 2, battery_y - battery_height / 2,
            battery_x + battery_width / 2, battery_y + battery_height / 2,
            fill="#3498db"
        )

        # Battery terminals
        self.canvas.create_line(
            battery_x, battery_y - battery_height / 2 - 10,
            battery_x, battery_y - battery_height / 2,
            fill="white", width=3
        )
        self.canvas.create_line(
            battery_x - 10, battery_y + battery_height / 2,
            battery_x + 10, battery_y + battery_height / 2,
            fill="white", width=3
        )

        # Battery voltage label
        self.canvas.create_text(
            battery_x, battery_y,
            text=f"{voltage}V",
            fill="white",
            font=("Roboto", 12, "bold")
        )

        # Draw resistor
        resistor_x, resistor_y = 300, 150
        resistor_width, resistor_height = 60, 30

        self.canvas.create_rectangle(
            resistor_x - resistor_width / 2, resistor_y - resistor_height / 2,
            resistor_x + resistor_width / 2, resistor_y + resistor_height / 2,
            fill="#9b59b6"
        )

        # Resistor value label
        self.canvas.create_text(
            resistor_x, resistor_y,
            text=f"{resistance}Ω",
            fill="white",
            font=("Roboto", 12, "bold")
        )

        # Draw bulb/lamp
        lamp_x, lamp_y = 450, 250
        lamp_radius = 30

        # Bulb brightness based on current (higher current = brighter)
        brightness = min(255, int(current * 25))
        lamp_color = f"#{brightness:02x}{brightness:02x}{brightness:02x}"

        # Bulb body
        self.canvas.create_oval(
            lamp_x - lamp_radius, lamp_y - lamp_radius,
            lamp_x + lamp_radius, lamp_y + lamp_radius,
            fill=lamp_color, outline="white"
        )

        # Bulb filament
        self.canvas.create_line(
            lamp_x - lamp_radius / 2, lamp_y,
            lamp_x + lamp_radius / 2, lamp_y,
            fill="yellow" if brightness > 100 else "gray",
            width=2
        )

        # Draw wires
        # Top wire
        self.canvas.create_line(
            battery_x, battery_y - battery_height / 2,
            battery_x, resistor_y,
                       resistor_x - resistor_width / 2, resistor_y,
            fill="#e2e2e2", width=2
        )

        # Middle wire
        self.canvas.create_line(
            resistor_x + resistor_width / 2, resistor_y,
            lamp_x, resistor_y,
            lamp_x, lamp_y - lamp_radius,
            fill="#e2e2e2", width=2
        )

        # Bottom wire
        self.canvas.create_line(
            lamp_x, lamp_y + lamp_radius,
            lamp_x, lamp_y + lamp_radius + 20,
            battery_x, lamp_y + lamp_radius + 20,
            battery_x, battery_y + battery_height / 2,
            fill="#e2e2e2", width=2
        )

        # Draw current flow indicators (animated dots)
        num_dots = 12
        for i in range(num_dots):
            # Calculate position in the circuit cycle
            circuit_position = (time_passed + i / num_dots) % 1.0

            # Determine dot position based on circuit position
            dot_x, dot_y = 0, 0

            if circuit_position < 0.25:  # Top wire
                progress = circuit_position * 4
                dot_x = battery_x + progress * (resistor_x - resistor_width / 2 - battery_x)
                dot_y = resistor_y
            elif circuit_position < 0.5:  # Middle wire
                progress = (circuit_position - 0.25) * 4
                dot_x = resistor_x + resistor_width / 2 + progress * (lamp_x - (resistor_x + resistor_width / 2))
                dot_y = resistor_y
            elif circuit_position < 0.75:  # Bottom wire (vertical part near lamp)
                progress = (circuit_position - 0.5) * 4
                dot_x = lamp_x
                dot_y = lamp_y + lamp_radius + progress * 20
            else:  # Bottom wire (horizontal and back to battery)
                progress = (circuit_position - 0.75) * 4
                dot_x = lamp_x - progress * (lamp_x - battery_x)
                dot_y = lamp_y + lamp_radius + 20

            # Draw dot with brightness proportional to current
            dot_size = 3 + current / 3
            dot_color = f"#{min(255, int(current * 25)):02x}ff{min(255, int(current * 25)):02x}"

            self.canvas.create_oval(
                dot_x - dot_size, dot_y - dot_size,
                dot_x + dot_size, dot_y + dot_size,
                fill=dot_color, outline=""
            )

        # Draw physics info
        self.canvas.create_text(
            300, 420,
            text=f"Voltage: {voltage:.1f} V | Resistance: {resistance:.1f} Ω | Current: {current:.2f} A",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        # Draw audio info
        self.canvas.create_text(
            300, 450,
            text="No sound for this visualization",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Controls
        self.canvas.create_text(
            300, 480,
            text="Click to change voltage and resistance",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Add click handler for changing circuit parameters
        self.canvas.bind("<Button-1>", lambda e: self.change_circuit_parameters())

        # Update time and continue animation
        self.animation_after_id = self.root.after(
            50, lambda: self.animate_circuit(voltage, resistance, time_passed + 0.02)
        )

    def change_circuit_parameters(self):
        if self.current_animation == "circuit":
            # Generate random voltage and resistance
            new_voltage = round(np.random.uniform(5.0, 15.0), 1)
            new_resistance = round(np.random.uniform(1.0, 10.0), 1)

            # Restart animation with new parameters
            if self.animation_after_id:
                self.root.after_cancel(self.animation_after_id)

            self.animate_circuit(voltage=new_voltage, resistance=new_resistance, time_passed=0)

    def stop_sine(self):
        if self._current_stream:
            try:
                self._current_stream.stop()
                self._current_stream.close()
            except:
                pass
            self._current_stream = None

    def play_sine(self, frequency=440, volume=0.5, samplerate=44100):
        self.stop_sine()

        dt = 1 / samplerate
        omega = 2 * np.pi * frequency

        def callback(outdata, frames, time, status):
            t_values = self._t + dt * np.arange(frames)
            samples = np.sin(omega * t_values) * volume
            outdata[:] = samples.reshape(-1, 1).astype(np.float32)
            self._t = t_values[-1]

        self._t = 0  # Reset time on new tone
        stream = sd.OutputStream(
            samplerate=samplerate,
            channels=1,
            callback=callback
        )
        stream.start()
        self._current_stream = stream

    def animate_wave(self, amplitude=50, frequency=1.0, time_passed=0):
        if not self.animation_running or self.current_animation != "wave":
            return

        # Clear canvas
        self.canvas.delete("all")

        # Draw title
        self.canvas.create_text(
            300, 30,
            text="Simple Harmonic Motion: y = A sin(ωt + φ)",
            fill="#e2e2e2",
            font=("Roboto", 16, "bold")
        )

        # Parameters
        angular_frequency = frequency * 2 * math.pi  # ω = 2πf
        phase = 0  # φ

        # Draw axes
        axis_y = 250
        self.canvas.create_line(50, axis_y, 550, axis_y, fill="#3498db", width=1)  # x-axis
        self.canvas.create_line(100, 100, 100, 400, fill="#3498db", width=1)  # y-axis

        # Draw wave
        points = []
        for x in range(500):
            x_pos = x + 100
            t = time_passed + x / 100
            y = axis_y - amplitude * math.sin(angular_frequency * t + phase)
            points.append(x_pos)
            points.append(y)

        # Draw sine wave
        if len(points) >= 4:  # Need at least 2 points (4 values) to draw a line
            self.canvas.create_line(points, fill="#9b59b6", width=2, smooth=True)

        # Create gradient for the wave
        num_segments = 20
        segment_width = 500 / num_segments
        for i in range(num_segments):
            segment_points = []
            for j in range(int(segment_width) + 1):
                x_pos = 100 + i * segment_width + j
                x_val = i * segment_width + j
                t = time_passed + x_val / 100
                y1 = axis_y - amplitude * math.sin(angular_frequency * t + phase)
                y2 = axis_y
                segment_points.extend([x_pos, y1, x_pos, y2])

            # Calculate color based on position (blue to purple gradient)
            r = int(100 + (i / num_segments) * 155)
            g = int(100 - (i / num_segments) * 100)
            b = 255
            color = f"#{r:02x}{g:02x}{b:02x}"

            if len(segment_points) >= 4:
                self.canvas.create_polygon(segment_points, fill=color, outline="", stipple="gray12")

        # Draw a moving point on the wave
        point_x = 100  # At the origin of the wave
        point_y = axis_y - amplitude * math.sin(angular_frequency * time_passed + phase)
        self.canvas.create_oval(
            point_x - 8, point_y - 8,
            point_x + 8, point_y + 8,
            fill="#e74c3c", outline="white"
        )

        # Draw vertical line to show oscillation
        self.canvas.create_line(
            point_x, axis_y,
            point_x, point_y,
            fill="white", dash=(2, 2)
        )

        # Draw parameters
        self.canvas.create_text(
            300, 420,
            text=f"Amplitude (A): {amplitude} pixels | Frequency (f): {frequency:.2f} Hz | Angular Frequency (ω): {angular_frequency:.2f} rad/s",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        self.canvas.create_text(
            300, 450,
            text=f"Period (T): {1 / frequency:.2f} seconds | Time: {time_passed:.2f} seconds",
            fill="#e2e2e2",
            font=("Roboto", 12)
        )

        # Draw audio info
        self.canvas.create_text(
            300, 480,
            text="Sound: Synth tones matching wave frequency (freq increased 300x)",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Controls
        self.canvas.create_text(
            300, 510,
            text="Click to change amplitude and frequency",
            fill="#9b59b6",
            font=("Roboto", 12)
        )

        # Add click handler for changing wave parameters
        self.canvas.bind("<Button-1>", lambda e: self.change_wave_parameters())

        # Update time and continue animation
        self.animation_after_id = self.root.after(
            50, lambda: self.animate_wave(amplitude, frequency, time_passed + 0.05)
        )

    def change_wave_parameters(self):
        if self.current_animation == "wave":
            # Generate random amplitude and frequency
            new_amplitude = np.random.randint(30, 70)
            new_frequency = round(np.random.uniform(0.5, 2.0), 2)

            # Restart animation with new parameters
            if self.animation_after_id:
                self.root.after_cancel(self.animation_after_id)
                # Play sine wave at higher frequency (300x for audible range)
                play_freq = int(new_frequency * 300)
                self.play_sine(play_freq)

            self.animate_wave(amplitude=new_amplitude, frequency=new_frequency, time_passed=0)


# Run the application
if __name__ == "__main__":
    root = ctk.CTk()
    app = PhysicsApp(root)
    root.mainloop()
