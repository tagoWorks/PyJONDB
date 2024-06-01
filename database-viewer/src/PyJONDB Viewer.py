import os
import json
import sys
import pyjondb
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def decrypt_and_show():
    key = key_entry.get()
    if not key:
        messagebox.showerror("Error", "Please enter the database key.")
        return
    if not os.path.isfile(database_path):
        messagebox.showerror("Error", f"File {database_path} does not exist.")
        return
    db_name = os.path.splitext(os.path.basename(database_path))[0]
    print(db_name)
    db = pyjondb.database(db_name, key, absolute=True)
    try:
        data = db.read()
        show_data(data)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read the database: {e}")
        key_entry.delete(0, tk.END)

def show_data(data):
    text_area.configure(state='normal')
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, json.dumps(data, indent=4))
    text_area.configure(state='disabled')

def on_open():
    global database_path
    if len(sys.argv) > 1:
        database_path = sys.argv[1]
        if os.path.isfile(database_path):
            root.deiconify()
        else:
            messagebox.showerror("Error", f"File {database_path} does not exist.")
            root.quit()
    else:
        database_path = filedialog.askopenfilename(
            title="Select the database file",
            filetypes=[("NDB Files", "*.ndb")]
        )
        if database_path:
            root.deiconify()
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

root = tk.Tk()
root.withdraw()
root.title("PyJONDB Database File View Tool")
root.iconbitmap(resource_path("pyjondb.ico"))

padx = 10
pady = 10

top_frame = tk.Frame(root)
top_frame.pack(pady=pady)

tk.Label(top_frame, text="PyJONDB View Tool", font=("Helvetica", 16)).grid(row=0, column=0, columnspan=2, pady=pady)

tk.Label(top_frame, text="Enter the database passkey:").grid(row=1, column=0, padx=padx, pady=pady)
key_entry = tk.Entry(top_frame, show='*', width=50)
key_entry.grid(row=1, column=1, padx=padx, pady=pady)

tk.Button(top_frame, text="View Data in file", command=decrypt_and_show, width=20, height=2).grid(row=2, column=0, columnspan=2, padx=padx, pady=pady)

bottom_frame = tk.Frame(root)
bottom_frame.pack(pady=pady)

text_area = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, width=80, height=20)
text_area.pack(padx=padx, pady=pady)
text_area.configure(state='disabled')

root.after(0, on_open)
root.mainloop()