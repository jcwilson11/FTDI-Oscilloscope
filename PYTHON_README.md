# Python FTDI Library

This repo now includes a reusable Python package named `ioLibrary` for FTDI reads and writes through the D2XX driver.

## Files

- `ioLibrary/`: reusable FTDI IO package
- `demo_led_blink.py`: sample application that uses only `ioLibrary`
- `tests/test_iolibrary.py`: unit tests for the public library API
- `controller.py`: earlier command-line prototype retained for reference

## Requirements

- Windows
- Python 3.10+
- FTDI D2XX runtime installed so `ftd2xx.dll` is available on `PATH`, or a copy of `ftd2xx.dll` placed in this folder

## Demo Usage

Run the LED blink demonstration:

```powershell
python demo_led_blink.py
```

Pass the DLL explicitly if needed:

```powershell
python demo_led_blink.py --dll "C:\path\to\ftd2xx.dll"
```

Change the number of cycles captured in the demo video:

```powershell
python demo_led_blink.py --cycles 6
```

## Public API

```python
from ioLibrary import ioBuffer, ioRead, ioWrite

buffer = ioBuffer(2, initial_data=[0xFF, 0x00])
writer = ioWrite()
writer.setBuffer(buffer).setFrequency(1.0).setM(2)
writer.executeWrite(cycles=4, sequence_mode=True)
```

For the LED blink demo, `sequence_mode=True` writes one buffer element at a time and holds each state for part of the configured period. With `[0xFF, 0x00]`, this produces a visible ON/OFF blink at 1 Hz and 2 Hz instead of sending both bytes as one near-instant burst.

The application configures the frequency and buffer contents. All direct FTDI/D2XX interaction remains inside `ioLibrary`.
