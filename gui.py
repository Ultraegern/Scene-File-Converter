import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional
import os

from main import M32, MixerScene


class SceneConverterGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title('Scene File Converter')
        root.resizable(False, False)

        frm = tk.Frame(root, padx=10, pady=10)
        frm.pack()

        # Input file selection
        tk.Label(frm, text='Source (decoder) file:').grid(row=0, column=0, sticky='w')
        self.src_var = tk.StringVar()
        tk.Entry(frm, width=50, textvariable=self.src_var).grid(row=1, column=0, columnspan=2)
        tk.Button(frm, text='Browse...', command=self.browse_source).grid(row=1, column=2, padx=5)

        # Output file selection
        tk.Label(frm, text='Destination (encoder) file:').grid(row=2, column=0, sticky='w', pady=(8, 0))
        self.dst_var = tk.StringVar()
        tk.Entry(frm, width=50, textvariable=self.dst_var).grid(row=3, column=0, columnspan=2)
        tk.Button(frm, text='Save as...', command=self.browse_destination).grid(row=3, column=2, padx=5)

        # Encoder selection (currently only JSON)
        tk.Label(frm, text='Encoder:').grid(row=4, column=0, sticky='w', pady=(8, 0))
        self.encoder_var = tk.StringVar(value='json')
        tk.OptionMenu(frm, self.encoder_var, 'json').grid(row=5, column=0, sticky='w')

        # Convert button
        tk.Button(frm, text='Convert', command=self.convert, width=20).grid(row=6, column=0, columnspan=3, pady=(12, 0))

    def browse_source(self) -> None:
        p = filedialog.askopenfilename(title='Select source scene file', filetypes=[('Scene files', '*.scn;*.txt'), ('All files', '*.*')])
        if p:
            self.src_var.set(p)

    def browse_destination(self) -> None:
        initial = os.path.splitext(os.path.basename(self.src_var.get()))[0] if self.src_var.get() else 'scene'
        p = filedialog.asksaveasfilename(title='Save destination file', defaultextension='.json', initialfile=initial + '.json', filetypes=[('JSON', '*.json'), ('All files', '*.*')])
        if p:
            self.dst_var.set(p)

    def convert(self) -> None:
        src = self.src_var.get()
        dst = self.dst_var.get()
        enc = self.encoder_var.get().lower()
        if not src or not os.path.isfile(src):
            messagebox.showerror('Error', 'Please select a valid source file to decode.')
            return
        if not dst:
            messagebox.showerror('Error', 'Please select a destination file to save the encoded output.')
            return
        try:
            scene: MixerScene = M32.decode(src)
        except Exception as e:
            messagebox.showerror('Decode error', f'Failed to decode source file:\n{e}')
            return

        try:
            if enc == 'json':
                scene.save_json(dst)
            else:
                # future encoders could be added
                scene.save_json(dst)
        except Exception as e:
            messagebox.showerror('Save error', f'Failed to save destination file:\n{e}')
            return

        messagebox.showinfo('Success', f'Converted "{os.path.basename(src)}" -> "{os.path.basename(dst)}"')


def run_gui() -> None:
    root = tk.Tk()
    app = SceneConverterGUI(root)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
