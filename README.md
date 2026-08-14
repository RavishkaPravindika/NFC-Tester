# NFC-Tester

Minimal Python CLI to interact with NFC readers (ACR1252U) using PC/SC.

Requirements
- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

Usage

List readers:

```bash
python main.py list
```

Read UID from a reader (first available):

```bash
python main.py uid
```

Notes
- This scaffold implements reader enumeration and UID read via PC/SC APDU `FF CA 00 00 00`.
- NDEF read/write implementations depend on tag type (Type 2/Type 4/MIFARE). I'll add examples next if you want.# NFC-Tester
 - NDEF read/write implementations depend on tag type (Type 2/Type 4/MIFARE). I'll add examples next if you want.

GUI

Launch the simple Tkinter GUI:

```bash
python main.py gui
```

NDEF Read / Write

- CLI read (Type 4):

```bash
python main.py ndef-read
```

- CLI write a simple text record (Type 4):

```bash
python main.py ndef-write "Hello NFC"
```

- GUI: use the `NDEF Read` and `Write NDEF` controls after selecting your reader.

Notes on tag types
- This implementation attempts Type 4 (ISO-DEP/APDU) NDEF read/write using common file IDs. Type 2 tags (NTAG/Ultralight) use native commands and may need vendor escape APDUs; if you primarily use Type 2 tags I can add native command support.

Testing with your ACR1252U
- With a tag present, run `python main.py diag` to get ATR, UID, and NDEF selection results. Paste that JSON if anything fails and I'll adapt the read/write flow.
