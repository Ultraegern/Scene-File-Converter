import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional
import os

# Import M32 and MixerScene lazily inside methods to avoid circular imports when
# running `python main.py` which imports this gui module.


def _win_get_open_filename(title: str, filetypes: list[tuple[str, str]]) -> tuple[Optional[str], Optional[int]]:
    """Use the native Windows GetOpenFileNameW dialog to get the file path and the selected filter index.

    Returns (path, filter_index) where filter_index is 1-based index of the selected filter.
    If the platform is not Windows or the call fails, returns (None, None).
    """
    try:
        import ctypes
        from ctypes import wintypes

        comdlg32 = ctypes.windll.comdlg32

        # build filter string: 'Description\0pattern\0Description2\0pattern2\0\0'
        filt_parts = []
        for desc, pat in filetypes:
            filt_parts.append(desc)
            filt_parts.append(pat)
        filter_str = '\0'.join(filt_parts) + '\0\0'

        # buffer for filename
        buf = ctypes.create_unicode_buffer(260)

        class OPENFILENAMEW(ctypes.Structure):
            _fields_ = [
                ('lStructSize', wintypes.DWORD),
                ('hwndOwner', wintypes.HWND),
                ('hInstance', wintypes.HINSTANCE),
                ('lpstrFilter', wintypes.LPCWSTR),
                ('lpstrCustomFilter', wintypes.LPWSTR),
                ('nMaxCustFilter', wintypes.DWORD),
                ('nFilterIndex', wintypes.DWORD),
                ('lpstrFile', wintypes.LPWSTR),
                ('nMaxFile', wintypes.DWORD),
                ('lpstrFileTitle', wintypes.LPWSTR),
                ('nMaxFileTitle', wintypes.DWORD),
                ('lpstrInitialDir', wintypes.LPCWSTR),
                ('lpstrTitle', wintypes.LPCWSTR),
                ('Flags', wintypes.DWORD),
                ('nFileOffset', wintypes.WORD),
                ('nFileExtension', wintypes.WORD),
                ('lpstrDefExt', wintypes.LPCWSTR),
                ('lCustData', ctypes.c_void_p),
                ('lpfnHook', ctypes.c_void_p),
                ('lpTemplateName', wintypes.LPCWSTR),
                ('pvReserved', ctypes.c_void_p),
                ('dwReserved', wintypes.DWORD),
                ('FlagsEx', wintypes.DWORD),
            ]

        ofn = OPENFILENAMEW()
        ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
        ofn.hwndOwner = 0
        ofn.lpstrFilter = filter_str
        ofn.lpstrFile = buf
        ofn.nMaxFile = ctypes.sizeof(buf) // ctypes.sizeof(ctypes.c_wchar)
        ofn.nFilterIndex = 1
        ofn.lpstrTitle = title

        res = comdlg32.GetOpenFileNameW(ctypes.byref(ofn))
        if res:
            return buf.value, int(ofn.nFilterIndex)
        return None, None
    except Exception:
        return None, None


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

    # Note: decoder selection is done in the file browser filter (Windows):
    # the open-file dialog will allow picking M32 or JSON filter and we read that choice.

        # Output file selection
        tk.Label(frm, text='Destination (encoder) file:').grid(row=2, column=0, sticky='w', pady=(8, 0))
        self.dst_var = tk.StringVar()
        tk.Entry(frm, width=50, textvariable=self.dst_var).grid(row=3, column=0, columnspan=2)
        tk.Button(frm, text='Save as...', command=self.browse_destination).grid(row=3, column=2, padx=5)
        # Convert button
        tk.Button(frm, text='Convert', command=self.convert, width=20).grid(row=4, column=0, columnspan=3, pady=(12, 0))

    def browse_source(self) -> None:
        # Ask the native Windows dialog so we can capture the filter index (which filter the user selected).
        filetypes = [('M32/SCN', '*.scn'), ('JSON', '*.json'), ('All files', '*.*')]
        path, idx = _win_get_open_filename('Select source scene file', filetypes)
        if path is None:
            # fallback to standard filedialog; try to infer decoder from extension
            p = filedialog.askopenfilename(title='Select source scene file', filetypes=filetypes)
            if p:
                self.src_var.set(p)
                _, ext = os.path.splitext(p)
                ext = ext.lower()
                if ext == '.json':
                    self._src_decoder = 'json'
                else:
                    self._src_decoder = 'm32'
        else:
            self.src_var.set(path)
            # _win_get_open_filename returns 1-based index; map 1->M32, 2->JSON
            if idx == 2:
                self._src_decoder = 'json'
            else:
                self._src_decoder = 'm32'

    def browse_destination(self) -> None:
        initial = os.path.splitext(os.path.basename(self.src_var.get()))[0] if self.src_var.get() else 'scene'
        # allow choosing JSON or SCN via the file type selector
        p = filedialog.asksaveasfilename(
            title='Save destination file',
            defaultextension='.json',
            initialfile=initial + '.json',
            filetypes=[('JSON', '*.json'), ('M32/SCN', '*.scn'), ('All files', '*.*')]
        )
        if p:
            self.dst_var.set(p)

    def convert(self) -> None:
        src = self.src_var.get()
        dst = self.dst_var.get()
        # decide decoder from user's selection (manual choice)
        decoder = (self.decoder_var.get() if hasattr(self, 'decoder_var') else 'm32')

        # infer encoder
        _, ext = os.path.splitext(dst)
        ext = ext.lower()
        if ext == '.scn':
            enc = 'm32'
        elif ext == '.json':
            enc = 'json'
        else:
            # default to json if unknown
            enc = 'json'
        if not src or not os.path.isfile(src):
            messagebox.showerror('Error', 'Please select a valid source file to decode.')
            return
        if not dst:
            messagebox.showerror('Error', 'Please select a destination file to save the encoded output.')
            return
        try:
            # local imports to avoid circular imports when main imports this module
            from main import M32, MixerScene

            if decoder == 'm32':
                scene: MixerScene = M32.decode(src)
            else:
                scene: MixerScene = MixerScene.load_json(src)
        except Exception as e:
            messagebox.showerror('Decode error', f'Failed to decode source file:\n{e}')
            return

        try:
            if enc == 'json':
                scene.save_json(dst)
            elif enc == 'm32':
                # ensure .scn extension
                if not dst.lower().endswith('.scn'):
                    dst = dst + '.scn'
                # use M32 encoder convenience
                M32.encode(scene, dst)
            else:
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
