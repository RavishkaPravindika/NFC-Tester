from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException
import ndef


def list_readers():
    """Return a list of available PC/SC reader names."""
    return [str(r) for r in readers()]


def read_uid(reader_name=None, timeout=3):
    """Connect to the first (or named) reader and return the tag UID as hex string.

    Uses the common PC/SC GET DATA command: FF CA 00 00 00
    """
    rlist = readers()
    if not rlist:
        raise RuntimeError("No PC/SC readers found")

    conn = None
    if reader_name:
        match = [r for r in rlist if str(r) == reader_name]
        if not match:
            raise RuntimeError(f"Reader not found: {reader_name}")
        conn = match[0].createConnection()
    else:
        conn = rlist[0].createConnection()

    conn.connect()

    GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]
    data, sw1, sw2 = conn.transmit(GET_UID_APDU)
    sw = (sw1 << 8) | sw2
    if sw1 == 0x90 or sw == 0x9000:
        return toHexString(data).replace(' ', '')
    raise RuntimeError(f"Failed to read UID: SW1=0x{sw1:02X} SW2=0x{sw2:02X}")


def diagnose(reader_name=None):
    """Diagnose a reader/tag: returns dict with ATR, UID (if readable), and NDEF select/read attempts."""
    rlist = readers()
    if not rlist:
        return {"error": "No PC/SC readers found"}

    conn = None
    reader_obj = None
    if reader_name:
        match = [r for r in rlist if str(r) == reader_name]
        if not match:
            return {"error": f"Reader not found: {reader_name}"}
        reader_obj = match[0]
    else:
        reader_obj = rlist[0]

    conn = reader_obj.createConnection()
    try:
        conn.connect()
    except NoCardException:
        return {"reader": str(reader_obj), "error": "No card present"}

    out = {"reader": str(reader_obj)}
    try:
        atr = conn.getATR()
        out["atr"] = toHexString(atr).replace(' ', '')
    except Exception as e:
        out["atr_error"] = str(e)

    # Try to read UID via common APDU
    try:
        GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        data, sw1, sw2 = conn.transmit(GET_UID_APDU)
        sw = (sw1 << 8) | sw2
        if sw1 == 0x90 or sw == 0x9000:
            out["uid"] = toHexString(data).replace(' ', '')
        else:
            out["uid_error"] = f"SW1=0x{sw1:02X} SW2=0x{sw2:02X}"
    except Exception as e:
        out["uid_error"] = str(e)

    # Try to SELECT NDEF Tag Application AID (Type 4)
    try:
        aid = [0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
        sel, sw1, sw2 = conn.transmit([0x00, 0xA4, 0x04, 0x00, len(aid)] + aid)
        out["select_ndef_sw"] = f"SW1=0x{sw1:02X} SW2=0x{sw2:02X}"
        if sw1 == 0x90 or ((sw1 << 8) | sw2) == 0x9000:
            out["select_ndef"] = True
            # attempt to select a common NDEF file id 0xE1 0x04
            try:
                sel2, sw1b, sw2b = conn.transmit([0x00, 0xA4, 0x00, 0x0C, 0x02, 0xE1, 0x04])
                out["select_file_sw"] = f"SW1=0x{sw1b:02X} SW2=0x{sw2b:02X}"
                if sw1b == 0x90 or ((sw1b << 8) | sw2b) == 0x9000:
                    # read first 32 bytes
                    data, r1, r2 = conn.transmit([0x00, 0xB0, 0x00, 0x00, 0x20])
                    out["file_read_sw"] = f"SW1=0x{r1:02X} SW2=0x{r2:02X}"
                    out["file_data"] = toHexString(data)
            except Exception as e:
                out["file_select_error"] = str(e)
        else:
            out["select_ndef"] = False
    except Exception as e:
        out["select_ndef_error"] = str(e)

    return out


def _connect_reader(reader_name=None):
    rlist = readers()
    if not rlist:
        raise RuntimeError("No PC/SC readers found")
    if reader_name:
        match = [r for r in rlist if str(r) == reader_name]
        if not match:
            raise RuntimeError(f"Reader not found: {reader_name}")
        reader_obj = match[0]
    else:
        reader_obj = rlist[0]
    conn = reader_obj.createConnection()
    conn.connect()
    return conn


def ndef_read(reader_name=None):
    """Attempt to read NDEF from a Type 4 tag by selecting NDEF AID and common file IDs.

    Returns dict with keys: file_id, nlen, raw, records (list of tuples)
    """
    conn = _connect_reader(reader_name)
    aid = [0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
    sel, sw1, sw2 = conn.transmit([0x00, 0xA4, 0x04, 0x00, len(aid)] + aid)
    if not (sw1 == 0x90 or ((sw1 << 8) | sw2) == 0x9000):
        raise RuntimeError(f"SELECT NDEF AID failed: SW1=0x{sw1:02X} SW2=0x{sw2:02X}")

    # try common file IDs
    candidates = [(0xE1, 0x04), (0x00, 0x01), (0xE1, 0x03), (0xE1, 0x02)]
    for fid in candidates:
        try:
            sel2, s1, s2 = conn.transmit([0x00, 0xA4, 0x00, 0x0C, 0x02, fid[0], fid[1]])
            if not (s1 == 0x90 or ((s1 << 8) | s2) == 0x9000):
                continue
            # read NLEN (first 2 bytes)
            header, h1, h2 = conn.transmit([0x00, 0xB0, 0x00, 0x00, 0x02])
            if not (h1 == 0x90 or ((h1 << 8) | h2) == 0x9000):
                continue
            if len(header) < 2:
                raise RuntimeError("Failed to read NLEN")
            nlen = (header[0] << 8) | header[1]
            # read remaining bytes
            file_bytes = header[:]
            offset = 2
            while offset < nlen + 2:
                le = min(0xFF, nlen + 2 - offset)
                off_hi = (offset >> 8) & 0xFF
                off_lo = offset & 0xFF
                chunk, c1, c2 = conn.transmit([0x00, 0xB0, off_hi, off_lo, le])
                if not (c1 == 0x90 or ((c1 << 8) | c2) == 0x9000):
                    raise RuntimeError(f"READ BINARY failed at offset {offset}: SW1=0x{c1:02X} SW2=0x{c2:02X}")
                file_bytes += chunk
                offset += len(chunk)
            raw = bytes(file_bytes)
            ndef_payload = raw[2:2 + nlen]
            records = []
            for rec in ndef.message_decoder(ndef_payload):
                records.append(rec)
            return {"file_id": f"{fid[0]:02X}{fid[1]:02X}", "nlen": nlen, "raw": raw.hex(), "records": [str(r) for r in records]}
        except Exception:
            continue
    raise RuntimeError("No NDEF file found using common file IDs")


def ndef_write(reader_name=None, ndef_message_bytes=b""):
    """Attempt to write NDEF (Type 4) by selecting NDEF AID and writing to common file IDs.

    ndef_message_bytes should be the raw NDEF message bytes (no NLEN)
    """
    conn = _connect_reader(reader_name)
    aid = [0xD2, 0x76, 0x00, 0x00, 0x85, 0x01, 0x01]
    sel, sw1, sw2 = conn.transmit([0x00, 0xA4, 0x04, 0x00, len(aid)] + aid)
    if not (sw1 == 0x90 or ((sw1 << 8) | sw2) == 0x9000):
        raise RuntimeError(f"SELECT NDEF AID failed: SW1=0x{sw1:02X} SW2=0x{sw2:02X}")

    nlen = len(ndef_message_bytes)
    payload = bytes([(nlen >> 8) & 0xFF, nlen & 0xFF]) + ndef_message_bytes

    candidates = [(0xE1, 0x04), (0x00, 0x01), (0xE1, 0x03), (0xE1, 0x02)]
    for fid in candidates:
        try:
            sel2, s1, s2 = conn.transmit([0x00, 0xA4, 0x00, 0x0C, 0x02, fid[0], fid[1]])
            if not (s1 == 0x90 or ((s1 << 8) | s2) == 0x9000):
                continue
            # write in chunks using UPDATE BINARY (0xD6)
            offset = 0
            total = len(payload)
            while offset < total:
                chunk = payload[offset:offset + 0xF0]
                off_hi = (offset >> 8) & 0xFF
                off_lo = offset & 0xFF
                apdu = [0x00, 0xD6, off_hi, off_lo, len(chunk)] + list(chunk)
                _, w1, w2 = conn.transmit(apdu)
                if not (w1 == 0x90 or ((w1 << 8) | w2) == 0x9000):
                    raise RuntimeError(f"UPDATE BINARY failed at offset {offset}: SW1=0x{w1:02X} SW2=0x{w2:02X}")
                offset += len(chunk)
            return {"file_id": f"{fid[0]:02X}{fid[1]:02X}", "written": total}
        except Exception as e:
            last_exc = e
            continue
    raise RuntimeError(f"Failed to write NDEF to any common file IDs: {last_exc}")


if __name__ == "__main__":
    print(list_readers())