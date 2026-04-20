from __future__ import annotations

import time

from ftd2xx_wrapper import FtdiError, ioFtdiDevice


MORSE_CODE = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
}


class ioLegacyFtdiCli:
    def prompt_int(self, prompt: str, minimum: int, maximum: int) -> int:
        while True:
            raw = input(prompt).strip()
            try:
                value = int(raw, 0)
            except ValueError:
                print("Enter a valid integer.")
                continue

            if minimum <= value <= maximum:
                return value

            print(f"Enter a value between {minimum} and {maximum}.")

    def write_message(self, device: ioFtdiDevice, message: str, pin_mask: int = 0x01) -> None:
        unit_seconds = 0.1
        for character in message:
            if character == " ":
                time.sleep(unit_seconds * 7)
                continue

            morse = MORSE_CODE.get(character.upper())
            if not morse:
                continue

            print(f"Morse code for '{character}': {morse}")
            for symbol in morse:
                device.write_byte(pin_mask)
                time.sleep(unit_seconds if symbol == "." else unit_seconds * 3)
                device.write_byte(0x00)
                time.sleep(unit_seconds)
            time.sleep(unit_seconds * 2)

    def control_leds(self, device: ioFtdiDevice) -> None:
        state = 0x00
        while True:
            raw = input("\nEnter pin 0-7, 'reset', or 'done': ").strip().lower()
            if raw == "done":
                break
            if raw == "reset":
                state = 0x00
                device.write_byte(state)
                print("All pins set to OFF.")
                continue

            try:
                pin = int(raw)
            except ValueError:
                print("Enter a pin number, 'reset', or 'done'.")
                continue

            if not 0 <= pin <= 7:
                print("Pin must be between 0 and 7.")
                continue

            for current_pin in range(8):
                pin_state = "ON" if state & (1 << current_pin) else "OFF"
                print(f"Pin {current_pin} = {pin_state}")

            new_value = self.prompt_int(f"Enter new state for pin {pin} (0 or 1): ", 0, 1)
            if new_value:
                state |= 1 << pin
            else:
                state &= ~(1 << pin)

            device.write_byte(state)
            print(f"Wrote 0x{state:02X}")

    def interactive_menu(self, device: ioFtdiDevice) -> None:
        while True:
            print("\nControl Menu")
            print("1. Control LEDs")
            print("2. Send Morse Code")
            print("3. Write byte to port")
            print("4. Read byte from port")
            print("5. Exit")

            choice = input("Enter your choice: ").strip()
            if choice == "1":
                self.control_leds(device)
            elif choice == "2":
                message = input("Enter your message (blank line to cancel): ")
                if message:
                    self.write_message(device, message)
            elif choice == "3":
                value = self.prompt_int("Enter byte value (0-255, hex allowed): ", 0, 255)
                device.write_byte(value)
                print(f"Wrote 0x{value:02X}")
            elif choice == "4":
                value = device.read_byte()
                print(f"Read 1 byte: 0x{value:02X}")
            elif choice == "5":
                return
            else:
                print("Invalid choice.")

    def run(self, args) -> int:
        listing_client = ioFtdiDevice(dll_path=args.dll)
        if args.list_devices:
            devices = listing_client.list_devices()
            if not devices:
                print("No FTDI devices visible through the D2XX driver.")
                return 0

            for device in devices:
                print(
                    f"index={device['index']} serial={device['serial']} "
                    f"description={device['description']} id=0x{device['id']:08X} "
                    f"location=0x{device['location_id']:08X} flags=0x{device['flags']:08X}"
                )
            return 0

        with listing_client as device:
            if args.write is not None:
                if not 0 <= args.write <= 0xFF:
                    raise FtdiError("--write value must be between 0 and 255")
                device.write_byte(args.write)
                print(f"Wrote 0x{args.write:02X}")
                return 0

            if args.read:
                value = device.read_byte()
                print(f"Read 1 byte: 0x{value:02X}")
                return 0

            if args.morse:
                self.write_message(device, args.morse)
                return 0

            self.interactive_menu(device)
            return 0
