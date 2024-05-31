import os
import json
import pyjondb
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def decrypt_and_show():
    database_path = filedialog.askopenfilename(
        title="Select the NDB file",
        filetypes=[("NDB Files", "*.ndb")]
    )
    if not database_path:
        return
    
    if not os.path.isfile(database_path):
        messagebox.showerror("Error", f"File {database_path} does not exist.")
        return

    key = key_entry.get()
    db_name = os.path.splitext(os.path.basename(database_path))[0]
    db = pyjondb.database(db_name, key)
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

root = tk.Tk()
root.title("NDB Decrypter")

# Padding configuration
padx = 10
pady = 10

# Top frame for file selection and key entry
top_frame = tk.Frame(root)
top_frame.pack(pady=pady)

tk.Label(top_frame, text="NDB Decryption Tool", font=("Helvetica", 16)).grid(row=0, column=0, columnspan=2, pady=pady)

tk.Button(top_frame, text="Open NDB File", command=decrypt_and_show, width=20, height=2).grid(row=1, column=0, padx=padx, pady=pady)

tk.Label(top_frame, text="Enter the database key:").grid(row=2, column=0, padx=padx, pady=pady)
key_entry = tk.Entry(top_frame, show='*', width=50)
key_entry.grid(row=2, column=1, padx=padx, pady=pady)

# Bottom frame for displaying data
bottom_frame = tk.Frame(root)
bottom_frame.pack(pady=pady)

text_area = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD, width=80, height=20)
text_area.pack(padx=padx, pady=pady)
text_area.configure(state='disabled')

root.mainloop()
