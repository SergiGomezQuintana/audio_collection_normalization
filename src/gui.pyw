import threading
import traceback
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, scrolledtext

from BS1770_normalize import normalize_folder


class NormalizeGUI:

    def __init__(self, root):

        self.root = root
        self.root.title("BS1770 MP3 Normalizer")
        self.root.geometry("700x420")

        # --------------------------
        # Input folder
        # --------------------------

        tk.Label(root, text="Input Folder").grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.in_var = tk.StringVar()

        tk.Entry(root, textvariable=self.in_var, width=60).grid(row=0, column=1)

        tk.Button(root, text="Browse...",
                  command=self.select_input).grid(row=0, column=2, padx=5)

        # --------------------------
        # Output folder
        # --------------------------

        tk.Label(root, text="Output Folder").grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.out_var = tk.StringVar()

        tk.Entry(root, textvariable=self.out_var, width=60).grid(row=1, column=1)

        tk.Button(root, text="Browse...",
                  command=self.select_output).grid(row=1, column=2, padx=5)

        # --------------------------
        # Target LUFS
        # --------------------------

        tk.Label(root, text="Target LUFS").grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.lufs_var = tk.StringVar(value="auto")

        tk.Entry(root, textvariable=self.lufs_var, width=15).grid(row=2, column=1, sticky="w")

        # --------------------------
        # True Peak
        # --------------------------

        tk.Label(root, text="True Peak Limit (dBTP)").grid(row=3, column=0, sticky="w", padx=10, pady=5)

        self.tp_var = tk.DoubleVar(value=-1.0)

        tk.Entry(root, textvariable=self.tp_var, width=15).grid(row=3, column=1, sticky="w")

        # --------------------------
        # Run button
        # --------------------------

        self.run_button = ttk.Button(root,
                                    text="Normalize",
                                    command=self.run)

        self.run_button.grid(row=4, column=1, pady=10)

        # --------------------------
        # Progress bar
        # --------------------------

        self.progress_label = tk.Label(
            root,
            text="Idle"
        )

        self.progress_label.grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="w",
            padx=10,
        )

        self.progress = ttk.Progressbar(
            root,
            orient="horizontal",
            mode="determinate",
        )

        self.progress.grid(
            row=6,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=10,
            pady=5,
        )

        # --------------------------
        # Log
        # --------------------------

        self.log = scrolledtext.ScrolledText(root, height=14)
        self.log.grid(
            row=7, 
            column=0,
            columnspan=3,
            sticky="nsew",
            padx=10,
            pady=10,
        )

        root.grid_rowconfigure(7, weight=1)
        root.grid_columnconfigure(1, weight=1)

    def select_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.in_var.set(folder)

    def select_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.out_var.set(folder)

    def write_log(self, text):

        self.root.after(0, self._write_log, text)


    def _write_log(self, text):

        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    def update_progress(self, current, total, phase):

        self.root.after(
            0,
            self._update_progress,
            current,
            total,
            phase,
        )


    def _update_progress(self, current, total, phase):

        self.progress["maximum"] = total
        self.progress["value"] = current

        self.progress_label.config(
            text=f"{phase}: {current}/{total}"
        )

    def run(self):

        thread = threading.Thread(target=self.normalize)
        thread.start()

    def normalize(self):

        self.run_button.config(state="disabled")

        try:

            target = self.lufs_var.get().strip()

            if target.lower() != "auto":
                target = float(target)

            self.write_log("Starting normalization...")

            normalize_folder(
                in_folder=self.in_var.get(),
                out_folder=self.out_var.get(),
                target_lufs=target,
                true_peak_limit=self.tp_var.get(),
                log_callback=self.write_log,
                progress_callback=self.update_progress,
            )

            self.write_log("Done!")

            messagebox.showinfo("Finished", "Normalization complete.")

        except Exception as e:

            self.write_log(str(e))

            messagebox.showerror("Error", str(e))

        finally:

            self.run_button.config(state="normal")


if __name__ == "__main__":

    try:
        root = tk.Tk()
        NormalizeGUI(root)
        root.mainloop()

    except Exception:
        messagebox.showerror(
            "Error",
            traceback.format_exc()
        )