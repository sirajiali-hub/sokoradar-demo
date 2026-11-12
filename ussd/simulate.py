"""Try the USSD menu in the terminal, like a phone, without Africa's Talking.

    python simulate.py
Type the number of your choice and press Enter. Type q to quit.
"""
import menu

PHONE = "+254700000000"      # a test number

while True:
    text = ""
    reply = menu.handle(text, PHONE)
    while True:
        print("\n" + reply[4:] + f"\n[{len(reply) - 4} chars]")
        if reply.startswith("END"):
            break
        key = input("> ").strip()
        if key.lower() == "q":
            raise SystemExit
        text = key if not text else f"{text}*{key}"
        reply = menu.handle(text, PHONE)
    if input("\nDial again? (y/n) ").strip().lower() != "y":
        break
