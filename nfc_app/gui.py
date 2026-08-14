import threading
import tkinter as tk
from tkinter import messagebox
from .nfc import list_readers, read_uid
from smartcard.util import toHexString


class NFCGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NFC-Tester")
        self.geometry("480x320")

        self.reader_listbox = tk.Listbox(self, height=6)
        self.reader_listbox.pack(fill=tk.X, padx=12, pady=(12, 4))

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=12)

        self.refresh_btn = tk.Button(btn_frame, text="Refresh Readers", command=self.refresh_readers)
        self.refresh_btn.pack(side=tk.LEFT)

        self.read_btn = tk.Button(btn_frame, text="Read UID", command=self.read_uid)
        self.read_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.diag_btn = tk.Button(btn_frame, text="Diagnose", command=self.diagnose)
        self.diag_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.ndef_read_btn = tk.Button(btn_frame, text="NDEF Read", command=self.ndef_read)
        self.ndef_read_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.uid_var = tk.StringVar(value="UID: ")
        self.uid_label = tk.Label(self, textvariable=self.uid_var, anchor="w")
        self.uid_label.pack(fill=tk.X, padx=12, pady=(8, 0))

        write_frame = tk.Frame(self)
        write_frame.pack(fill=tk.X, padx=12)
        tk.Label(write_frame, text="NDEF Text:").pack(side=tk.LEFT)
        self.ndef_entry = tk.Entry(write_frame)
        self.ndef_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))
        self.ndef_write_btn = tk.Button(write_frame, text="Write NDEF", command=self.ndef_write)
        self.ndef_write_btn.pack(side=tk.LEFT)

        self.log_text = tk.Text(self, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.refresh_readers()

        # Raw APDU frame
        raw_frame = tk.LabelFrame(self, text="Raw APDU")
        raw_frame.pack(fill=tk.X, padx=12, pady=(0,8))
        self.apdu_entry = tk.Entry(raw_frame)
        self.apdu_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, pady=6)
        self.apdu_send_btn = tk.Button(raw_frame, text="Send APDU", command=self.send_raw_apdu)
        self.apdu_send_btn.pack(side=tk.LEFT, padx=6)

        # MIFARE helper frame
        mifare_frame = tk.LabelFrame(self, text="MIFARE Classic Helpers")
        mifare_frame.pack(fill=tk.X, padx=12, pady=(0,8))
        tk.Label(mifare_frame, text="Block:").pack(side=tk.LEFT)
        self.block_entry = tk.Entry(mifare_frame, width=6)
        self.block_entry.pack(side=tk.LEFT, padx=(4,8))
        tk.Label(mifare_frame, text="Key (hex 12 chars):").pack(side=tk.LEFT)
        self.key_entry = tk.Entry(mifare_frame, width=16)
        self.key_entry.insert(0, "FFFFFFFFFFFF")
        self.key_entry.pack(side=tk.LEFT, padx=(4,8))
        self.load_key_btn = tk.Button(mifare_frame, text="Load Key", command=self.mifare_load_key)
        self.load_key_btn.pack(side=tk.LEFT, padx=4)
        self.auth_btn = tk.Button(mifare_frame, text="Auth", command=self.mifare_auth)
        self.auth_btn.pack(side=tk.LEFT, padx=4)
        self.read_block_btn = tk.Button(mifare_frame, text="Read Block", command=self.mifare_read_block)
        self.read_block_btn.pack(side=tk.LEFT, padx=4)
        self.write_block_btn = tk.Button(mifare_frame, text="Write Block", command=self.mifare_write_block)
        self.write_block_btn.pack(side=tk.LEFT, padx=4)

        # Type-2 passthrough frame
        t2_frame = tk.LabelFrame(self, text="Type-2 / NTAG Passthrough")
        t2_frame.pack(fill=tk.X, padx=12, pady=(0,8))
        tk.Label(t2_frame, text="Page:").pack(side=tk.LEFT)
        self.page_entry = tk.Entry(t2_frame, width=6)
        self.page_entry.pack(side=tk.LEFT, padx=(4,8))
        self.t2_read_btn = tk.Button(t2_frame, text="Native READ (0x30)", command=self.type2_native_read)
        self.t2_read_btn.pack(side=tk.LEFT, padx=4)
        # Raw APDU frame
        raw_frame = tk.LabelFrame(self, text="Raw APDU")
        raw_frame.pack(fill=tk.X, padx=12, pady=(0,8))
        self.apdu_entry = tk.Entry(raw_frame)
        self.apdu_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, pady=6)
        self.apdu_send_btn = tk.Button(raw_frame, text="Send APDU", command=self.send_raw_apdu)
        self.apdu_send_btn.pack(side=tk.LEFT, padx=6)

        # MIFARE helper frame
        mifare_frame = tk.LabelFrame(self, text="MIFARE Classic Helpers")
        mifare_frame.pack(fill=tk.X, padx=12, pady=(0,8))
        tk.Label(mifare_frame, text="Block:").pack(side=tk.LEFT)
        self.block_entry = tk.Entry(mifare_frame, width=6)
        self.block_entry.pack(side=tk.LEFT, padx=(4,8))
        tk.Label(mifare_frame, text="Key (hex 12 chars):").pack(side=tk.LEFT)
        self.key_entry = tk.Entry(mifare_frame, width=16)
        self.key_entry.insert(0, "FFFFFFFFFFFF")
        self.key_entry.pack(side=tk.LEFT, padx=(4,8))
        self.load_key_btn = tk.Button(mifare_frame, text="Load Key", command=self.mifare_load_key)
        self.load_key_btn.pack(side=tk.LEFT, padx=4)
        self.auth_btn = tk.Button(mifare_frame, text="Auth", command=self.mifare_auth)
        self.auth_btn.pack(side=tk.LEFT, padx=4)
        self.read_block_btn = tk.Button(mifare_frame, text="Read Block", command=self.mifare_read_block)
        self.read_block_btn.pack(side=tk.LEFT, padx=4)
        self.write_block_btn = tk.Button(mifare_frame, text="Write Block", command=self.mifare_write_block)
        self.write_block_btn.pack(side=tk.LEFT, padx=4)

        # Type-2 passthrough frame
        t2_frame = tk.LabelFrame(self, text="Type-2 / NTAG Passthrough")
        t2_frame.pack(fill=tk.X, padx=12, pady=(0,8))
        tk.Label(t2_frame, text="Page:").pack(side=tk.LEFT)
        self.page_entry = tk.Entry(t2_frame, width=6)
        self.page_entry.pack(side=tk.LEFT, padx=(4,8))
        self.t2_read_btn = tk.Button(t2_frame, text="Native READ (0x30)", command=self.type2_native_read)
        self.t2_read_btn.pack(side=tk.LEFT, padx=4)

    def log(self, *parts):
        self.log_text.insert(tk.END, " ".join(str(p) for p in parts) + "\n")
        self.log_text.see(tk.END)

    def refresh_readers(self):
        try:
            readers = list_readers()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enumerate readers: {e}")
            return
        self.reader_listbox.delete(0, tk.END)
        for r in readers:
            self.reader_listbox.insert(tk.END, r)
        self.log("Readers refreshed:", len(readers))

    def read_uid(self):
        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                uid = read_uid(reader_name=reader)
                self.uid_var.set(f"UID: {uid}")
                self.log("UID read:", uid)
            except Exception as e:
                self.log("Error reading UID:", e)
                messagebox.showerror("Read error", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def diagnose(self):
        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                from .nfc import diagnose
                res = diagnose(reader_name=reader)
                # pretty print result
                import json
                self.log(json.dumps(res, indent=2))
            except Exception as e:
                self.log("Diagnose error:", e)

        threading.Thread(target=worker, daemon=True).start()

    def send_raw_apdu(self):
        txt = self.apdu_entry.get().strip()
        if not txt:
            messagebox.showinfo("APDU", "Enter hex bytes for APDU, e.g. 00A4040007D2760000850101")
            return
        try:
            apdu = bytes.fromhex(txt)
        except Exception as e:
            messagebox.showerror("APDU", f"Invalid hex: {e}")
            return

        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                from .nfc import _connect_reader
                conn = _connect_reader(reader)
                data, sw1, sw2 = conn.transmit(list(apdu))
                self.log(f"APDU -> SW1=0x{sw1:02X} SW2=0x{sw2:02X} DATA={toHexString(data)}")
            except Exception as e:
                self.log("APDU error:", e)

        threading.Thread(target=worker, daemon=True).start()

    def mifare_load_key(self):
        blk = self.block_entry.get()
        key_hex = self.key_entry.get().strip()
        try:
            block = int(blk)
            key = bytes.fromhex(key_hex)
            if len(key) != 6:
                raise ValueError('Key must be 6 bytes')
        except Exception as e:
            messagebox.showerror("Input", f"Invalid input: {e}")
            return

        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                from .nfc import _connect_reader
                conn = _connect_reader(reader)
                apdu = [0xFF,0x82,0x00,0x00,0x06] + list(key)
                data, sw1, sw2 = conn.transmit(apdu)
                self.log(f"LoadKey SW1=0x{sw1:02X} SW2=0x{sw2:02X}")
            except Exception as e:
                self.log("LoadKey error:", e)

        threading.Thread(target=worker, daemon=True).start()

    def mifare_auth(self):
        blk = self.block_entry.get()
        try:
            block = int(blk)
        except Exception as e:
            messagebox.showerror("Input", f"Invalid block: {e}")
            return
        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                from .nfc import _connect_reader
                conn = _connect_reader(reader)
                # key number 0, Key A (0x60)
                apdu = [0xFF,0x86,0x00,0x00,0x05, 0x01,0x00, block, 0x60, 0x00]
                data, sw1, sw2 = conn.transmit(apdu)
                self.log(f"Auth SW1=0x{sw1:02X} SW2=0x{sw2:02X}")
            except Exception as e:
                self.log("Auth error:", e)

        threading.Thread(target=worker, daemon=True).start()

    def mifare_read_block(self):
        blk = self.block_entry.get()
        try:
            block = int(blk)
        except Exception as e:
            messagebox.showerror("Input", f"Invalid block: {e}")
            return
        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                from .nfc import _connect_reader
                conn = _connect_reader(reader)
                apdu = [0xFF,0xB0,0x00,block,0x10]
                data, sw1, sw2 = conn.transmit(apdu)
                self.log(f"Read block {block} SW1=0x{sw1:02X} SW2=0x{sw2:02X} DATA={toHexString(data)}")
            except Exception as e:
                self.log("Read error:", e)

        threading.Thread(target=worker, daemon=True).start()

    def mifare_write_block(self):
        blk = self.block_entry.get()
        try:
            block = int(blk)
        except Exception as e:
            messagebox.showerror("Input", f"Invalid block: {e}")
            return
        # Ask user for 16 bytes hex
        val = tk.simpledialog.askstring("Write Block", "Enter 16 bytes hex data (32 hex chars):")
        if not val:
            return
        try:
            data_bytes = bytes.fromhex(val)
            if len(data_bytes) != 16:
                raise ValueError('Must be 16 bytes')
        except Exception as e:
            messagebox.showerror("Input", f"Invalid data: {e}")
            return
        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                from .nfc import _connect_reader
                conn = _connect_reader(reader)
                apdu = [0xFF,0xD6,0x00,block,0x10] + list(data_bytes)
                _, sw1, sw2 = conn.transmit(apdu)
                self.log(f"Write block {block} SW1=0x{sw1:02X} SW2=0x{sw2:02X}")
            except Exception as e:
                self.log("Write error:", e)

        threading.Thread(target=worker, daemon=True).start()

    def type2_native_read(self):
        page_txt = self.page_entry.get()
        try:
            page = int(page_txt)
        except Exception as e:
            messagebox.showerror("Input", f"Invalid page: {e}")
            return
        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                from .nfc import _connect_reader
                conn = _connect_reader(reader)
                # try common passthrough wrappers
                native = [0x30, page]
                wrappers = [
                    lambda b: [0xFF,0x00,0x00,0x00,len(b)] + b,
                    lambda b: [0xFF,0x00,0x40,0x00,len(b)] + b,
                ]
                for w in wrappers:
                    apdu = w(native)
                    try:
                        data, sw1, sw2 = conn.transmit(apdu)
                        if sw1 == 0x90 or ((sw1<<8)|sw2) == 0x9000:
                            self.log(f"Native read OK via wrapper {apdu}: {toHexString(data)}")
                            return
                        else:
                            self.log(f"Wrapper returned SW1=0x{sw1:02X} SW2=0x{sw2:02X}")
                    except Exception as e:
                        self.log("Wrapper error:", e)
                self.log("All wrappers tried, no success")
            except Exception as e:
                self.log("Type-2 read error:", e)

        threading.Thread(target=worker, daemon=True).start()

    def ndef_read(self):
        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                from .nfc import ndef_read
                import json
                res = ndef_read(reader_name=reader)
                self.log(json.dumps(res, indent=2))
            except Exception as e:
                self.log("NDEF read error:", e)

        threading.Thread(target=worker, daemon=True).start()

    def ndef_write(self):
        text = self.ndef_entry.get()
        if not text:
            messagebox.showinfo("Input", "Enter text to write as NDEF")
            return
        sel = self.reader_listbox.curselection()
        reader = None
        if sel:
            reader = self.reader_listbox.get(sel[0])

        def worker():
            try:
                import ndef as ndeflib
                msg_bytes = b"".join(ndeflib.message_encoder([ndeflib.TextRecord(text)]))
                from .nfc import ndef_write
                res = ndef_write(reader_name=reader, ndef_message_bytes=msg_bytes)
                self.log("NDEF write result:", res)
            except Exception as e:
                self.log("NDEF write error:", e)

        threading.Thread(target=worker, daemon=True).start()


def main():
    app = NFCGui()
    app.mainloop()


if __name__ == "__main__":
    main()