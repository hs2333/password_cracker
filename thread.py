import itertools
import string
import time
import threading
import queue
import tkinter as tk
from tkinter import messagebox


CHARACTERS = string.digits + string.ascii_lowercase
UPDATE_EVERY = 1000

class PasswordCrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Password Cracker Demo (one-thread)")
        self.root.geometry("560x470")

        self.target_password = ""
        self.attempts = 0
        self.start_time = None
        self.paused_time = 0
        self.pause_start = None

        self.running = False
        self.paused = False

        # Threading tools
        self.worker_thread = None
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        self.title_label = tk.Label(
            root,
            text="CPU Password Cracker Demo",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=10)

        self.password_label = tk.Label(
            root,
            text="Set 6-character password (letters and/or numbers)"
        )
        self.password_label.pack()

        self.password_entry = tk.Entry(root, width=25, show="*")
        self.password_entry.pack(pady=5)

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

        self.output_box = tk.Text(root, height=10, width=60)
        self.output_box.pack(pady=10)

        # Keep checking messages from the worker thread
        self.check_queue()

    def validate_password(self, password):
        password = password.lower()

        if len(password) != 6:
            return None, "Password must be exactly 6 characters long."

        allowed = string.ascii_lowercase + string.digits
        if not all(ch in allowed for ch in password):
            return None, "Only letters and numbers are allowed."

        return password, None

    def start_cracking(self):
        password = self.password_entry.get()
        password, error = self.validate_password(password)

        if error:
            messagebox.showerror("Invalid Password", error)
            return

        self.target_password = password
        self.attempts = 0
        self.start_time = time.time()
        self.paused_time = 0
        self.pause_start = None

        self.running = True
        self.paused = False

        self.stop_event.clear()
        self.pause_event.clear()

        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, "Starting cracker in worker thread...\n")

        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.NORMAL)
        self.password_entry.config(state=tk.DISABLED)

        self.worker_thread = threading.Thread(
            target=self.crack_worker,
            daemon=True
        )
        self.worker_thread.start()

    def crack_worker(self):
        # run in the background worker thread
        # NO directly update Tkinter widgets here

        guess_generator = itertools.product(CHARACTERS, repeat=6)

        for guess_tuple in guess_generator:
            if self.stop_event.is_set():
                return

            while self.pause_event.is_set():
                if self.stop_event.is_set():
                    return
                time.sleep(0.05)

            guess = ''.join(guess_tuple)
            self.attempts += 1

            elapsed_time = self.get_elapsed_time()

            # Only send update every UPDATE_EVERY guesses.
            # This prevents the GUI queue from being flooded.
            if self.attempts % UPDATE_EVERY == 0:
                self.message_queue.put({
                    "type": "update",
                    "guess": guess,
                    "attempts": self.attempts,
                    "time": elapsed_time
                })

            if guess == self.target_password:
                self.message_queue.put({
                    "type": "found",
                    "guess": guess,
                    "attempts": self.attempts,
                    "time": elapsed_time
                })
                return

        self.message_queue.put({
            "type": "not_found"
        })

    def check_queue(self):
        # run in the Tkinter main thread.
        # update the GUI using messages from the worker thread.
        max_messages_per_check = 20
        messages_processed = 0

        try:
            while messages_processed < max_messages_per_check:
                message = self.message_queue.get_nowait()
                messages_processed += 1

                if message["type"] == "update":
                    guess = message["guess"]
                    attempts = message["attempts"]
                    elapsed_time = message["time"]

                    self.current_guess_label.config(text=f"Current guess: {guess}")
                    self.attempts_label.config(text=f"Attempts: {attempts}")
                    self.time_label.config(text=f"Time: {elapsed_time:.4f} seconds")

                    # # Do not print every guess. This text box is slow.
                    # self.output_box.insert(
                    #     tk.END,
                    #     f"Trying: {guess}\n"
                    # )
                    # self.output_box.see(tk.END)
                    # # self.output_box.insert(
                    # #     tk.END,
                    # #     f"Trying: {guess}    Attempts: {attempts}\n"
                    # # )
                    # # self.output_box.see(tk.END)

                elif message["type"] == "found":
                    self.running = False
                    self.paused = False

                    guess = message["guess"]
                    attempts = message["attempts"]
                    elapsed_time = message["time"]

                    self.current_guess_label.config(text=f"Current guess: {guess}")
                    self.attempts_label.config(text=f"Attempts: {attempts}")
                    self.time_label.config(text=f"Time: {elapsed_time:.4f} seconds")

                    self.output_box.insert(tk.END, "\nPassword cracked!\n")
                    self.output_box.insert(tk.END, f"Correct password: {guess}\n")
                    self.output_box.insert(tk.END, f"Total attempts: {attempts}\n")
                    self.output_box.insert(tk.END, f"Time taken: {elapsed_time:.4f} seconds\n")

                    self.pause_button.config(state=tk.DISABLED)
                    self.resume_button.config(state=tk.DISABLED)
                    self.restart_button.config(state=tk.NORMAL)

                    messagebox.showinfo(
                        "Password Cracked!",
                        f"Correct password: {guess}\n"
                        f"Total attempts: {attempts}\n"
                        f"Time taken: {elapsed_time:.4f} seconds"
                    )

                elif message["type"] == "not_found":
                    self.running = False
                    messagebox.showinfo("Done", "Password was not found.")

                    self.pause_button.config(state=tk.DISABLED)
                    self.resume_button.config(state=tk.DISABLED)
                    self.restart_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass

        # check the queue again after 50 ms
        self.root.after(50, self.check_queue)

    def pause_cracking(self):
        if self.running and not self.paused:
            self.paused = True
            self.pause_start = time.time()
            self.pause_event.set()

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

            self.pause_event.clear()

            self.output_box.insert(tk.END, "Resumed.\n")
            self.output_box.see(tk.END)

            self.pause_button.config(state=tk.NORMAL)
            self.resume_button.config(state=tk.DISABLED)

    def restart_cracking(self):
        self.stop_event.set()
        self.pause_event.clear()

        self.running = False
        self.paused = False

        self.target_password = ""
        self.attempts = 0
        self.start_time = None
        self.paused_time = 0
        self.pause_start = None

        # Clear old messages still waiting in the queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except queue.Empty:
                break

        self.current_guess_label.config(text="Current guess: None")
        self.attempts_label.config(text="Attempts: 0")
        self.time_label.config(text="Time: 0.0000 seconds")

        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, "Restarted.\n")
        self.output_box.insert(tk.END, "Set 6-character password (letters and/or numbers)\n")

        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)
        self.password_entry.config(state=tk.NORMAL)
        self.password_entry.delete(0, tk.END)

    def get_elapsed_time(self):
        if self.start_time is None:
            return 0

        if self.paused and self.pause_start is not None:
            return self.pause_start - self.start_time - self.paused_time

        return time.time() - self.start_time - self.paused_time


def main():
    root = tk.Tk()
    app = PasswordCrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()