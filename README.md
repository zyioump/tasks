# Open Path View Tasks

## Todo

Write this software

## Requirements

You will need to install :
```bash
apt-get install imagemagick
```
You also need to have a [https://github.com/OpenPathView/DirectoryManager](DirectoryManager server) and an [https://github.com/OpenPathView/OPV_DBRest](OPV_DBRest server) running.
These server handle campaings, lot ... data storing.

## Install
```bash
pip install -r requirements.txt
python setup.py install
```

## Rotate Task
Will rotate a lot (it's 6 pictures) in portrait mode.
```bash
bin/opv-task-rotate 53 --debug
```

## License

Copyright (C) 2017 Open Path View, Maison Du Libre <br />
This program is free software; you can redistribute it and/or modify  <br />
it under the terms of the GNU General Public License as published by  <br />
the Free Software Foundation; either version 3 of the License, or  <br />
(at your option) any later version.  <br />
This program is distributed in the hope that it will be useful,  <br />
but WITHOUT ANY WARRANTY; without even the implied warranty of  <br />
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the  <br />
GNU General Public License for more details.  <br />
You should have received a copy of the GNU General Public License along  <br />
with this program. If not, see <http://www.gnu.org/licenses/>.  <br />
