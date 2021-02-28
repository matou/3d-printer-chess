# 3D Printer Chess

This code and 3D models allow you to make a chess robot out of your 3D printer. The 3D models contain files for a mechanical gripper that attaches to the print head of the printer and can move chess pieces around. A well-grippable 3d-printable chess set is also included.

The code sends commands to an Octoprint instance to move the gripper. 

I've documented this project on [YouTube](https://youtu.be/6b2As388-Ro). 

### Prerequisites for the code

The code is written in Python 3. The following packages must be installed:

* `numpy`
* `requests`
* `opencv-python`
* `sunfish` -- download the sunfish chess AI from (https://github.com/thomasahle/sunfish)[https://github.com/thomasahle/sunfish] and place `sunfish.py` in the same folder as the other source code


### How to set it up

**This is not fool-proof! The gripper might get stuck or break and fling debris through the room or even break the printer or whatever. So use it at your own risk ;)**

In the `3d-models` folder, you can find the 3d-printable gripper as well as a chess set that works well with the gripper. 

The gripper uses the extruder motor to open and close the gripper. My Ender-3 printer has a direct drive extruder, which made it easy to get the gripper to work. I have no idea how I would mount it on a stock Ender-3. 

You will probably have to adapt the 3d model for the gripper for your specific printer. 

I printed a simple chess with white PLA directly on the print bed. The files for it are also included. 

This assumes that there is an Octoprint instance controlling your 3d printer. 

In order to use the extruder motor without heating up the nozzle, you need to send the g-code `M302 P1;` to the printer through Octoprint's terminal. This enables cold extrusion. **Make sure that there is no filament in the printer, or you might damage it!**. Not all firmwares support cold extrusion; so you might have to adapt/flash new firmware on the printer. 

The computer vision module assumes that there is a camera mounted above the chess board, with the field A1 being top right and H8 being bottom left in the picture. It doesn't need to be aligned perfectly, as the tool tries to detect the board by itself. 

Once the printer is prepared, you can configure your Octoprint URL and API key in the file `main.py` and run it in order to play chess against your 3d printer. It should detect if you make a move and automatically respond with it's own move. 

### More

I might be porting this to an Octoprint plugin in the future, so it's easier to use. If you want me to get that done faster, open an issue in this repository and let me know. I am more motivated to do stuff if I know that people are interested in it. 

Any questions? Feel free to open an issue on github :)
