# HT-Rendering-Software

A open-access webapp to navigate 3D Holotomography images controlled by standard mouse and keyboard inputs as well as VR through WebXR.

## Features

- __Uploading:__ Users can upload TomoCube Files (TCF) of any size.

- __Processing:__ Upon uploading, Python's h5py library extracts the data from the file's '3D' group into texture (.tga) files.

- __Staging:__ Once a file is uploaded, users can stage the file to be displayed through Unreal Engine's Pixel Streaming Plugin. Only one file can be staged at a time.


## Development

- Developed and tested on Windows 11.
- Designed from Unreal Engine 5.4.

## Dependencies

Development was done on Python 3.12. The project dependencies are shown in requirements.txt. You can download them at once in the project's root directory with shell command:
```bash
pip install -r backend/dependencies.txt
```

## Setup

The frontend component can be run as follows:
```bash
cd webapp
npm install
npm start
```

The backend server can be run as follows:
```bash
cd backend
python manage.py migrate
python manage.py runserver
```
Each server must be ran on separate terminals. This can be done with keyboard shortcut Ctrl + Shift +`.

The frontend will be accessible in a browser at http://localhost:3000 after proper setup.

## Pixel Streaming User Interface

The Pixel Streaming feature in this application offers a comprehensive set of controls to enhance the user experience:

### Features

- **Color Control:** Adjust the color settings to customize the visual appearance of the 3D model.

- **Coordinates Display:** View the current camera position coordinates for precise navigation and alignment.

- **Brightness Adjustment:** Modify the brightness level to improve visibility and detail.

- **Framerate Control:** Adjust the framerate to control the speed of the display’s movement through the time frame indexes.

### Mouse Controls

- **Right Click Hold:** Rotate the Field of View (FOV) by holding the right mouse button and moving the mouse.

- **Left Click Hold:** Move the camera on the XY plane by holding the left mouse button and dragging the mouse.

- **Scroll Wheel:** Zoom in/out of the display using the scroll wheel.

### Unreal Engine Plugins

This project utilizes specific Unreal Engine plugins to achieve shared GPU accelerated graphics:

- **UMG (Unreal Motion Graphics)**
- **Niagara Particle System**
- **Pixel Streaming Player**

## Technologies
- React
- Django
- SQLite

## Authors

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
