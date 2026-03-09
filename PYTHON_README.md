# Python FT245R Controller

This repo now includes a Python entry point that talks to the FT245R through FTDI's D2XX driver.

## Files

- `controller.py`: command-line controller in Python
- `ftd2xx_wrapper.py`: minimal `ctypes` wrapper over `ftd2xx.dll`

## Requirements

- Windows
- Python 3.10+
- FTDI D2XX runtime installed so `ftd2xx.dll` is available on `PATH`, or a copy of `ftd2xx.dll` placed in this folder

## Usage

Interactive menu:

```powershell
python controller.py
```

Write one byte:

```powershell
python controller.py --write 0x01
```

Read one byte:

```powershell
python controller.py --read
```

List devices visible to the FTDI D2XX driver:

```powershell
python controller.py --list-devices
```

Send Morse code:

```powershell
python controller.py --morse "SOS"
```

If the DLL is not on `PATH`, pass it explicitly:

```powershell
python controller.py --dll "C:\path\to\ftd2xx.dll" --write 0x01
```
