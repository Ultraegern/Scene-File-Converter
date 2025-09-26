import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Tuple, List
import os


def _win_get_open_filename(title: str, filetypes: List[Tuple[str, str]]) -> Tuple[Optional[str], Optional[int]]:
    """Use the native Windows GetOpenFileNameW dialog to get the file path and the selected filter index.

    Returns (path, filter_index) where filter_index is 1-based index of the selected filter.
    If the platform is not Windows or the call fails, returns (None, None).
    """
    try:
        import ctypes
        from ctypes import wintypes

        comdlg32 = ctypes.windll.comdlg32

        # build filter string: 'Description\0pattern\0Description2\0pattern2\0\0'
        filt_parts: List[str] = []
        for desc, pat in filetypes:
            filt_parts.append(desc)
            filt_parts.append(pat)
        filter_str = "\0".join(filt_parts) + "\0\0"

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
    src_var: tk.StringVar
    dst_var: tk.StringVar
    src_decoder_var: tk.StringVar
    _src_decoder: str

    def __init__(self, root: tk.Tk) -> None:
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

        # Decoder status label
        self._src_decoder = 'm32'
        self.src_decoder_var = tk.StringVar(value='Decoder: m32')
        tk.Label(frm, textvariable=self.src_decoder_var).grid(row=1, column=3, sticky='w', padx=(10, 0))

        # Output file selection
        tk.Label(frm, text='Destination (encoder) file:').grid(row=2, column=0, sticky='w', pady=(8, 0))
        self.dst_var = tk.StringVar()
        tk.Entry(frm, width=50, textvariable=self.dst_var).grid(row=3, column=0, columnspan=2)
        tk.Button(frm, text='Save as...', command=self.browse_destination).grid(row=3, column=2, padx=5)

        # Convert button
        tk.Button(frm, text='Convert', command=self.convert, width=20).grid(row=4, column=0, columnspan=3, pady=(12, 0))

    def browse_source(self) -> None:
        # Try native Windows dialog first to capture the selected file-type filter index.
        filetypes: List[Tuple[str, str]] = [('M32/SCN', '*.scn'), ('JSON', '*.json'), ('All files', '*.*')]
        path, idx = _win_get_open_filename('Select source scene file', filetypes)
        if path is None:
            p: Optional[str] = filedialog.askopenfilename(title='Select source scene file', filetypes=filetypes)
            if not p:
                return
            self.src_var.set(p)
            _, ext = os.path.splitext(p)
            ext = ext.lower()
            if ext == '.json':
                self._src_decoder = 'json'
                self.src_decoder_var.set('Decoder: json')
            else:
                self._src_decoder = 'm32'
                self.src_decoder_var.set('Decoder: m32')
        else:
            self.src_var.set(path)
            # idx is 1-based: map 1->M32, 2->JSON
            if idx == 2:
                self._src_decoder = 'json'
                self.src_decoder_var.set('Decoder: json')
            else:
                self._src_decoder = 'm32'
                self.src_decoder_var.set('Decoder: m32')

    def browse_destination(self) -> None:
        initial = os.path.splitext(os.path.basename(self.src_var.get()))[0] if self.src_var.get() else 'scene'
        p = filedialog.asksaveasfilename(
            title='Save destination file',
            defaultextension='.json',
            initialfile=initial + '.json',
            filetypes=[('JSON', '*.json'), ('M32/SCN', '*.scn'), ('All files', '*.*')],
        )
        if p:
            self.dst_var.set(p)

    def convert(self) -> None:
        src: str = self.src_var.get()
        dst: str = self.dst_var.get()
        decoder: str = getattr(self, '_src_decoder', 'm32')

        # infer encoder from destination extension
        _, ext = os.path.splitext(dst)
        ext = ext.lower()
        if ext == '.scn':
            enc = 'm32'
        elif ext == '.json':
            enc = 'json'
        else:
            enc = 'json'

        if not src or not os.path.isfile(src):
            messagebox.showerror('Error', 'Please select a valid source file to decode.')
            return
        if not dst:
            messagebox.showerror('Error', 'Please select a destination file to save the encoded output.')
            return

        try:
            # local imports to avoid circular import when main imports this module
            from main import M32, MixerScene  # type: ignore

            if decoder == 'm32':
                scene = M32.decode(src)
            else:
                scene = MixerScene.load_json(src)
        except Exception as e:
            messagebox.showerror('Decode error', f'Failed to decode source file:\n{e}')
            return

        try:
            if enc == 'json':
                scene.save_json(dst)
            elif enc == 'm32':
                if not dst.lower().endswith('.scn'):
                    dst = dst + '.scn'
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
