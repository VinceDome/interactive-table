# About the project
This is the full source code for my yearly project at my high school, AKG.
## Method
A projector and a camera are suspended above a table, using a piece of wood and 3d printed attachment parts. The camera processes the objects it sees on the table (using [OpenCV](https://opencv.org/)), and with precise alignment, the projector can correctly project the outlines of small, 3d printed markers. This creates a system, where the apps can be operated by the markers.

### Currently there are two demo apps:
  - A game where the players guess the location of major cities in Hungary on a blank map.
  - A game where the players place the hands of an analog clock to match the time displayed digitally.
## About the developement
- The project was created by Bartha Vince Döme, a student of the Budapest-based high school AKG.
- The code uses various image recognition techniques to minimize the margin of error of the shape detection, and make it functional in various lighting conditions.
- The structure that holds up the projector and the webcam 1.5 meters above the table is made up of a wooden plank, two 3d printed parts, a few screws, and is attached to the table using two clamps.
- This project got second place on the competition [MiniMaker](https://fb.me/e/4cgvXt9h6) (hosted by [Fablab](https://www.fablabbudapest.com/)).
