import socket
import tkinter as tk
from tkinter import Label, Frame
import os
from datetime import datetime
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Global variables
window = None
response_label1 = None
response_label2 = None
right_response = None
harigami_key = ""
program_index = ""
observer = None
HOST = "197.197.197.11"  # IP address of IV3 Navigator
PORT = 8500  # Port used by IV3 Navigator

model = []
program = []

def file_reader(text_file, listy):
    with open(text_file, "r") as file:
        for line in file:
            listy.append(line.strip())

file_reader("program.txt", program)
file_reader("model.txt", model)

def check_file_modification(file_path):
    """Check for file modifications."""
    try:
        mtime = os.path.getmtime(file_path)
        modification_time = datetime.fromtimestamp(mtime)

        if not hasattr(check_file_modification, 'prev_time'):
            check_file_modification.prev_time = modification_time
            return "Unchanged (initial check)"  # Indicate initial state

        if modification_time > check_file_modification.prev_time:
            check_file_modification.prev_time = modification_time
            return "Updated"
        else:
            return "Unchanged"

    except OSError as e:
        return f"Error: {e}"

def file_check():
    """Periodically check for file modifications."""
    while True:
        modification_status = check_file_modification("BODY_INFORMATION.txt")
        if modification_status == "Updated":
            print("File modified. Sending trigger to IV3 Navigator.")
            update_file_data()  # Read and update global variables if needed
            send_trigger_to_navigator()  # Trigger the navigator check
        time.sleep(2)  # Check every 2 seconds

class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events."""
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith("BODY_INFORMATION.txt"):
            print("File modified. Sending trigger to IV3 Navigator.")
            update_file_data()
            send_trigger_to_navigator()  # Trigger the navigator check

def update_file_data():
    """Read file and update global variables."""
    global harigami_key, program_index

    with open("BODY_INFORMATION.txt", 'r') as file:
        harigami_key = file.read().strip()

    if harigami_key in model:
        model_index = model.index(harigami_key)
        program_index = program[model_index]
    else:
        program_index = ""

def front_end(message=None):
    """Initialize the Tkinter window and set up the GUI layout."""
    global window, response_label1, response_label2, right_response

    if window is None:
        window = tk.Tk()
        window.minsize(1000, 500)
        window.title("Back Door Garnish")

        label_names = ["Suffix:", "Program:"]
        heading_label = Label(window, text="TRIM LINE: BACK DOOR GARNISH", justify="center", font=("Times New Roman", 30))
        heading_label.grid(row=0, column=0, columnspan=2, padx=300, pady=150, sticky="nsew")

        container_frame = Frame(window)
        container_frame.grid(row=1, column=0, sticky="nsew")

        Label(container_frame, text=label_names[0], justify="center", font=("Times New Roman", 30)).grid(row=0, column=3, padx=100, pady=10, sticky="w")
        Label(container_frame, text=label_names[1], justify="center", font=("Times New Roman", 30)).grid(row=1, column=3, padx=100, pady=10, sticky="w")

        response_label1 = Label(container_frame, text="", justify="center", fg="BLUE", font=("Arial", 30))
        response_label1.grid(row=0, column=5, padx=0, pady=3, sticky="nsew")

        response_label2 = Label(container_frame, text="", justify="center", fg="BLUE", font=("Arial", 30))
        response_label2.grid(row=1, column=5, padx=0, pady=3, sticky="nsew")

        right_frame = Frame(window)
        right_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        Label(right_frame, text="Status:", font=("Times", 50)).grid(row=2, column=0, padx=50, pady=5, sticky="w")

        right_response = Label(right_frame, text="", bg="LIGHTgreen", relief="raised", font=("Times", 40))
        right_response.grid(row=2, column=1, padx=50, pady=50)

    if message is not None:
        update_gui(message)

    window.mainloop()

def update_gui(message):
    """Update the GUI elements based on new data."""
    global response_label1, response_label2, right_response

    if window is None:
        front_end()

    response_label1.config(text=harigami_key)
    response_label2.config(text=program_index)

    if message == "OK":
        right_response.config(text=message, bg="LIGHTgreen")
    elif message == "NG":
        right_response.config(text=message, bg="red")
    else:
        right_response.config(text=message)

    window.update()

def send_trigger_to_navigator():
    """Send a trigger to the IV3 Navigator regardless of the data content."""
    program = program_index  # Use the global program_index
    if not program:
        update_gui("No matching program found")
        return

    try:
        with open(f"suffix_programs\\{program}.txt", "rb") as file:
            for line in file:
                data = line.strip()
                COMMAND = data + b'\r'
                print(f"Sending command: {COMMAND}")
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((HOST, PORT))
                    client_socket.sendall(COMMAND)

                    received_data = client_socket.recv(1024)
                    decoded = received_data.decode().strip()
                    print(f"Received from IV3 Navigator: {decoded}")

                    # Check for empty response
                    if not decoded:
                        update_gui("No response received")
                        continue

                    # Split and handle different response scenarios
                    split_data = decoded.split(",")
                    if len(split_data) > 2:
                        actual_output = split_data[2].strip()
                        if actual_output == "OK":
                            update_gui("OK")
                        elif actual_output == "NG":
                            update_gui("NG")
                        else:
                            print(f"Unexpected token in data: {decoded}")
                            update_gui(f"Unexpected token: {actual_output}")
                    elif "PW" in decoded:
                        # Separate handling for 'PW' commands
                        print("PW command acknowledgment received.")
                        update_gui("Waiting for next command response")
                    else:
                        print(f"Unexpected data format: {decoded}")
                        update_gui(f"Unexpected Response: {decoded}")

                    client_socket.close()

                except socket.error as err:
                    print(f"Socket error: {err}")
                    update_gui(f"Error: {err}")
                    client_socket.close()

    except FileNotFoundError as e:
        print(f"File error: {e}")
        update_gui(f"File Error: {e}")

def init():
    """Initialize the observer, file check, and GUI."""
    global observer

    observer = Observer()
    event_handler = FileChangeHandler()
    observer.schedule(event_handler, ".", recursive=False)
    observer.start()

    file_thread = threading.Thread(target=file_check)
    file_thread.daemon = True
    file_thread.start()

    update_file_data()
    gui_thread = threading.Thread(target=front_end)
    gui_thread.start()

if __name__ == "__main__":
    init()
