# FTDI-Oscilloscope

## Overview
This repository contains the initial development work for a PC-based oscilloscope application that interfaces with FTDI hardware. The goal of this project is to design and implement a digital oscilloscope capable of real-time visualization and analysis of electrical signals.

As part of the system architecture process, an initial **user interface prototype** was created using Figma. This prototype represents the planned layout and functionality of the oscilloscope control software.


## Figma User Interface Design

The oscilloscope interface was designed using **Figma** to prototype the layout before implementing the software.

The Figma design includes:

- Waveform selection (Sine, Square, Triangle, Sawtooth)
- Frequency control
- Amplitude adjustment
- Signal offset adjustment
- Time/div control
- Trigger level adjustment
- Run and Reset control buttons

This layout describes the planned structure of the oscilloscope control software.

### Figma Design Link

View the full design here:

https://www.figma.com/design/X6zNvyLg22J7tkcQIDl1BI/Oscilloscope-Wireframe?node-id=0-1&t=w9TdjTskqkcVeDE0-1

The Figma file contains the wireframes and UI layout used for the initial system architecture design.



## User Interface Description

The oscilloscope interface is divided into functional sections:

### Channel Configuration Panels
Each channel panel allows the user to configure the waveform signal for that channel.

Each channel is color coded for clarity when visualized in the oscilloscope display.

### Oscilloscope Controls
The oscilloscope control section provides controls for the signal visualization.

Controls include:
- Time per division (Time/Div)
- Trigger level adjustment
- Run button to start signal generation
- Reset button to restore default settings

### Oscilloscope Display
The oscilloscope display area shows the generated waveforms for both channels. The interface supports simultaneous visualization of multiple signals to allow comparison and signal analysis.



## Purpose of the UI Prototype

The Figma prototype was created to:

- Plan the oscilloscope software layout
- Define user interaction workflows
- Establish the control structure for signal generation
- Provide a reference for future implementation

This design helps guide the development of the oscilloscope software interface before integrating the hardware signal acquisition system.

## Figma UI Screenshots

Below are screenshots of the oscilloscope interface prototype created in Figma.

### Oscilloscope Display

<img width="1440" height="1024" alt="Oscilloscope UI" src="https://github.com/user-attachments/assets/9e7c3617-96f3-4c28-9215-d1b90fb50d4c" />

### Channel Control Panels

<img width="954" height="682" alt="Control Panel UI" src="https://github.com/user-attachments/assets/5c2257b0-85ef-4250-b00b-607308eb2b04" />

## Future Development

Future updates to this project will include:

- Implementation of the oscilloscope interface in software
- Integration with FTDI hardware
- Real-time signal acquisition and visualization

