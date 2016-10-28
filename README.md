#Anki layout switcher

##Linux (X11) and Windows only 

Autoswitch the keyboard layout when changing between question and answer field

Layouts can be set in the deck option ("general" tab)

Rudimentary Windows (10 - didn't test it on anything else) support has been added:

**Be aware, this might mess up your layout on Windows (I didn't really test it)**

**Requirements:** 

* a version of Anki compiled against PyQt5 (currently only the alpha builds come with PyQt5 on Windows)
* python3
* pywin32 (https://sourceforge.net/projects/pywin32/)

**For Windows user:**
If you switch to another non-anki window (e.g. Browser, Thunderbird...) while the "Add Cards/Editor"  window is still open (=> while adding/editing cards) the layout of the "Front" or "Back" field might be carried to that window (and will be difficult to reset without reboot). To prevent this, make a left click somewhere in the "Add Cards/Editor" window (or close the Editor / Add Card Window). This will reset the layout back to the default value until you click back into the "Front" or "Back" field.  
