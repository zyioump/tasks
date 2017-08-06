# Open Path View Tasks

All needed tasks to stich a panorama and more. Based on the [hugin](http://hugin.sourceforge.net/) stiching chain.

## Requirements

This tasks requireded hugin's libraries and more. We have automated the deployment of these requirements in our Ansible scripts.
But you can also deploy the dependencies manually.

## Automated deployment with Ansible

Use our playbook and deployment scripts available in [OPV_Ansible](https://github.com/OpenPathView/OPV_ansible).

## Manually building the environnement

### APIs
Install and run the needed APIs :
 - [OPV_DBRest](https://github.com/Openpathview/OPV_DBrest) : you will need to kown it's endpoint. This API will be used to store all metadata.
 - [DirectoryManager](https://github.com/OpenPathView/DirectoryManager) : you will also need to know it's endpoint. This API is our storage API.

### Host configuration
We will use **opv_master**, we have DB_Rest and the DirectoryManager on this machine. You might set it in your /etc/hosts file.

### Dependencies

You will need to install :
```bash
apt-get install imagemagick hugin
```

### Hugin Script Interface (HSI) module
You also need to have the Hugin Script Interface python module. It should be install by default with hugin but migth by install for the wrong version of python.
To check it (outside your venv) :
```bash
$ python3.5
Python 3.5.2 (default, Nov 17 2016, 17:05:23)
[GCC 5.4.0 20160609] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import hsi
```

If you don't have it ... dam you are about to recompile hugin ! To wrap your HSI in the good python version, follow the instructions [here](doc/compile_hugin_hsi.md).

If you have it installed on your system, you need to add it to your python virtual env, the easiest way to do so his to make a symbolic link from your system dist-packages/hsi.py module to venv dist-packages.
Follow this :
```bash
(global) $ python3.5 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))"  # get you global dist-package path
/usr/lib/python3/dist-packages
(venv) $ python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))"  # get you venv dist-package path
/home/benjamin/Documents/OpenPathView/code/OPV_Tasks/.venv/OPV_Tasks/lib/python3.5/site-packages
(vent) $ ln -s /usr/lib/python3/dist-packages/hsi.py /home/benjamin/Documents/OpenPathView/code/OPV_Tasks/.venv/OPV_Tasks/lib/python3.5/site-packages/ # make symbolic link
(vent) $ ln -s /usr/lib/python3/dist-packages/_hsi.so /home/benjamin/Documents/OpenPathView/code/OPV_Tasks/.venv/OPV_Tasks/lib/python3.5/site-packages/ # make symbolic link
```

### Install
```bash
cd OPV_Tasks
python setup.py install
```

## Using opv-task

You migth need some data to play with it, use [OPV_importdata](https://github.com/OpenPathView/OPV_importdata#importing-test-dataset) to import our test set.

```bash
# Get the help
opv-task -h
# Stitch a panorama lot 130 / id malette 15
opv-task makeall '{"id_lot": 130, "id_malette": 15 }' --db-rest=http://opv_master:5000 --dir-manager=http://opv_master:5005
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
