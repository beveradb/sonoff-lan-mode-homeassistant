## non-hass-scripts

This subfolder contains scripts which are not intended to be executed through HomeAssistant.
They are part of this repository as they are a core part of the _purpose_ of this project, but are not technically linked to the HomeAssistant component in any away.

### Explanation

A key part of this project is researching and cataloguing differences between Sonoff device models and how they all function in LAN mode,
and the easiest way to gather information for that purpose is to ask owners of various models to run a script and upload the log file.

This subfolder is where we'll be developing those scripts.
If this project is ever significant enough to warrant cleaner separation of concerns,
this subfolder could be moved out into a separate repository as there is no technical reason to have it alongside the HomeAssistant component itself.

### Setup

To use these scripts, you'll need to run them from a terminal (command line) on your computer.

If you've never used the command line before, there are intro tutorials which can help you get started, e.g. [Windows](https://www.youtube.com/watch?v=MBBWVgE0ewk) / [macOS](https://www.youtube.com/watch?v=x3YfYVVTYvw),
and for further learning to get really familiar with it, I'd recommend [this guide](https://www.learnenough.com/command-line-tutorial/basics).

These instructions (and scripts) should work on Windows, Mac OSX and Linux, but haven't been thoroughly tested - raise an issue if you need help!

1. Install Python. There are [various guides](https://realpython.com/installing-python/) to help with this.
2. Install [Git](https://git-scm.com/download/). On Windows, you'll need to close and re-open your Command Prompt after installing so your PATH is reloaded.
3. Install the required Python libraries. There's a `requirements.txt` file in this directory, 
which can be used directly from the command line with `pip install -r .\requirements.txt`

### Usage

1. Edit the `test_sonoff.py` file and change the `SONOFF_LAN_IP` value at the top to the IP address of your Sonoff
2. Run from the command line, with `python3 test_sonoff.py`
3. Wait for a couple of seconds, then press the switch button on your Sonoff device, then again a few seconds later.
4. Stop the script (by pressing CTRL+C in the terminal)
5. Upload the log file (`test_sonoff.log`, in the same directory you ran it from) to a GitHub issue for review by me / others.
