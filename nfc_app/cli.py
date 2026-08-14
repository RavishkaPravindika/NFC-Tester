import argparse
from .nfc import list_readers, read_uid
from . import gui


def main():
    parser = argparse.ArgumentParser(description="NFC-Tester CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="List PC/SC readers")
    sub.add_parser("gui", help="Launch the Tkinter GUI")
    sub.add_parser("diag", help="Run reader/tag diagnostic and print results")
    ndef_read_p = sub.add_parser("ndef-read", help="Read NDEF from a Type 4 tag and print records")
    ndef_read_p.add_argument("-r", "--reader", help="Reader name (optional)")
    ndef_write_p = sub.add_parser("ndef-write", help="Write NDEF to a Type 4 tag (simple text)")
    ndef_write_p.add_argument("text", help="Text to write as a single NDEF TextRecord")
    ndef_write_p.add_argument("-r", "--reader", help="Reader name (optional)")

    uid_parser = sub.add_parser("uid", help="Read UID from tag")
    uid_parser.add_argument("-r", "--reader", help="Reader name (optional)")

    args = parser.parse_args()
    if args.cmd == "list":
        for r in list_readers():
            print(r)
    elif args.cmd == "uid":
        try:
            uid = read_uid(reader_name=args.reader)
            print(uid)
        except Exception as e:
            print("Error:", e)
    elif args.cmd == "gui":
        gui.main()
    elif args.cmd == "diag":
        try:
            from .nfc import diagnose
            result = diagnose(reader_name=args.reader if hasattr(args, 'reader') else None)
            import json
            print(json.dumps(result, indent=2))
        except Exception as e:
            print("Error:", e)
    elif args.cmd == "ndef-read":
        try:
            from .nfc import ndef_read
            import json
            res = ndef_read(reader_name=args.reader)
            print(json.dumps(res, indent=2))
        except Exception as e:
            print("Error:", e)
    elif args.cmd == "ndef-write":
        try:
            from .nfc import ndef_write
            import ndef as ndeflib
            # build a single TextRecord message
            msg_bytes = b"".join(ndeflib.message_encoder([ndeflib.TextRecord(args.text)]))
            res = ndef_write(reader_name=args.reader, ndef_message_bytes=msg_bytes)
            print(res)
        except Exception as e:
            print("Error:", e)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()