Welcome to my repository!
The main script is LoadedStave.py. This script can register a new STAVE (initiate) and assemble MODULEs (update).
========================================================================================================================

If you want to try to register a new STAVE and load a MODULE using this script, you need to prepare the following:

a)  Unzip  'Calibrations.zip'

b)	Register a short slim module through User Interface, give it a local name

c)	Put this local name into the modulesID.csv in 'Calibrations' (say you put it next to position 9).
    This csv is needed for supplying the unique ID (in this case, it’s the local name) to find the MODULE in PD.

d)	Now run in terminal:
```
        >python2.7 LoadedStave.py initiate --directory ./Calibrations/ --positions 9
```
    follow the directions from prompt lines; it will first register a STAVE and then assemble the MODULE at position 9.

================================================================================================

If you want to assemble more MODULEs to the same STAVE:

a) repeat step b) above

b) save local name in modulesID.csv (say position 10)

c) run:
```
        >python2.7 LoadedStave.py update --directory ./Calibrations/ --positions 10
```
    prompt lines will ask for the local name of the STAVE and assemble MODULE at position 10.
