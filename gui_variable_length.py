import itertools
import string
import time
import tkinter as tk
from tkinter import messagebox


CHARACTERS = string.digits + string.ascii_lowercase
MIN_PASSWORD_LENGTH = 1
MAX_PASSWORD_LENGTH = 8


class PasswordCrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Password Cracker Demo")
        self.root.geometry("560x520")

        self.target_password = ""
        self.password_length = 6
        self.guess_generator = None
        self.attempts = 0
        self.start_time = None
        self.paused_time = 0
        self.pause_start = None

        self.running = False
        self.paused = False

        self.title_label = tk.Label(
            root,
            text="CPU Password Cracker Demo",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=10)

        self.password_label = tk.Label(
            root,
            text="Set password (letters and/or numbers)"
        )
        self.password_label.pack()

        self.password_entry = tk.Entry(root, width=25, show="*")
        self.password_entry.pack(pady=5)

        self.length_label = tk.Label(
            root,
            text=f"Password length ({MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH})"
        )
        self.length_label.pack()

        self.length_entry = tk.Entry(root, width=10)
        self.length_entry.insert(0, "6")
        self.length_entry.pack(pady=5)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.start_button = tk.Button(
            self.button_frame,
            text="Start Cracking",
            command=self.start_cracking
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = tk.Button(
            self.button_frame,
            text="Pause",
            command=self.pause_cracking,
            state=tk.DISABLED
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.resume_button = tk.Button(
            self.button_frame,
            text="Resume",
            command=self.resume_cracking,
            state=tk.DISABLED
        )
        self.resume_button.grid(row=0, column=2, padx=5)

        self.restart_button = tk.Button(
            self.button_frame,
            text="Restart",
            command=self.restart_cracking,
            state=tk.DISABLED
        )
        self.restart_button.grid(row=0, column=3, padx=5)

        self.current_guess_label = tk.Label(
            root,
            text="Current guess: None",
            font=("Arial", 12)
        )
        self.current_guess_label.pack(pady=5)

        self.attempts_label = tk.Label(
            root,
            text="Attempts: 0",
            font=("Arial", 12)
        )
        self.attempts_label.pack(pady=5)

        self.time_label = tk.Label(
            root,
            text="Time: 0.0000 seconds",
            font=("Arial", 12)
        )
        self.time_label.pack(pady=5)

        self.max_label = tk.Label(
            root,
            text=f"Maximum possible guesses: {36 ** self.password_length:,}",
            font=("Arial", 10)
        )
        self.max_label.pack(pady=3)

        self.output_box = tk.Text(root, height=10, width=60)
        self.output_box.pack(pady=10)

    def validate_length(self):
        length_text = self.length_entry.get().strip()

        if not length_text.isdigit():
            return None, "Password length must be a whole number."

        length = int(length_text)
        if length < MIN_PASSWORD_LENGTH or length > MAX_PASSWORD_LENGTH:
            return None, (
                f"Password length must be between "
                f"{MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH}."
            )

        return length, None

    def validate_password(self, password, length):
        password = password.lower()

        if len(password) != length:
            return None, f"Password must be exactly {length} characters long."

        allowed = string.ascii_lowercase + string.digits
        if not all(ch in allowed for ch in password):
            return None, "Only letters and numbers are allowed."

        return password, None

    def start_cracking(self):
        length, error = self.validate_length()
        if error:
            messagebox.showerror("Invalid Length", error)
            return

        password = self.password_entry.get()
        password, error = self.validate_password(password, length)

        if error:
            messagebox.showerror("Invalid Password", error)
            return

        self.target_password = password
        self.password_length = length
        self.guess_generator = itertools.product(CHARACTERS, repeat=length)
        self.attempts = 0
        self.start_time = time.time()
        self.paused_time = 0
        self.pause_start = None

        self.running = True
        self.paused = False

        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, "Starting cracker...\n")
        self.output_box.insert(
            tk.END,
            f"Password length: {self.password_length}\n"
        )

        self.max_label.config(
            text=f"Maximum possible guesses: {36 ** self.password_length:,}"
        )

        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.NORMAL)
        self.password_entry.config(state=tk.DISABLED)
        self.length_entry.config(state=tk.DISABLED)

        self.crack_step()

    def pause_cracking(self):
        if self.running and not self.paused:
            self.paused = True
            self.pause_start = time.time()

            self.output_box.insert(tk.END, "\nPaused.\n")
            self.output_box.see(tk.END)

            self.pause_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.NORMAL)

    def resume_cracking(self):
        if self.running and self.paused:
            self.paused = False

            if self.pause_start is not None:
                self.paused_time += time.time() - self.pause_start
                self.pause_start = None

            self.output_box.insert(tk.END, "Resumed.\n")
            self.output_box.see(tk.END)

            self.pause_button.config(state=tk.NORMAL)
            self.resume_button.config(state=tk.DISABLED)

            self.crack_step()

    def restart_cracking(self):
        self.running = False
        self.paused = False

        self.target_password = ""
        self.guess_generator = None
        self.attempts = 0
        self.start_time = None
        self.paused_time = 0
        self.pause_start = None

        self.current_guess_label.config(text="Current guess: None")
        self.attempts_label.config(text="Attempts: 0")
        self.time_label.config(text="Time: 0.0000 seconds")
        self.max_label.config(
            text=f"Maximum possible guesses: {36 ** self.password_length:,}"
        )

        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, "Restarted.\n")
        self.output_box.insert(
            tk.END,
            "Set password and password length (letters and/or numbers)\n"
        )

        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)
        self.password_entry.config(state=tk.NORMAL)
        self.length_entry.config(state=tk.NORMAL)
        self.password_entry.delete(0, tk.END)

    def get_elapsed_time(self):
        if self.start_time is None:
            return 0

        if self.paused and self.pause_start is not None:
            return self.pause_start - self.start_time - self.paused_time

        return time.time() - self.start_time - self.paused_time

    def crack_step(self):
        if not self.running:
            return

        if self.paused:
            return

        try:
            guess_tuple = next(self.guess_generator)
        except StopIteration:
            self.running = False
            messagebox.showinfo("Done", "Password was not found.")
            self.restart_button.config(state=tk.NORMAL)
            return

        guess = ''.join(guess_tuple)
        self.attempts += 1

        elapsed_time = self.get_elapsed_time()

        self.current_guess_label.config(text=f"Current guess: {guess}")
        self.attempts_label.config(text=f"Attempts: {self.attempts}")
        self.time_label.config(text=f"Time: {elapsed_time:.4f} seconds")

        self.output_box.insert(tk.END, f"Trying: {guess}\n")
        self.output_box.see(tk.END)

        if guess == self.target_password:
            self.running = False
            self.paused = False

            messagebox.showinfo(
                "Password Cracked!",
                f"Correct password: {guess}\n"
                f"Total attempts: {self.attempts}\n"
                f"Time taken: {elapsed_time:.4f} seconds"
            )

            self.output_box.insert(tk.END, "\nPassword cracked!\n")
            self.output_box.insert(tk.END, f"Correct password: {guess}\n")
            self.output_box.insert(tk.END, f"Total attempts: {self.attempts}\n")
            self.output_box.insert(
                tk.END,
                f"Time taken: {elapsed_time:.4f} seconds\n"
            )

            self.pause_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.NORMAL)
            return

        self.root.after(1, self.crack_step)


def main():
    root = tk.Tk()
    app = PasswordCrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
