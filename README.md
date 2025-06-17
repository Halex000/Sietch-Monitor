Thanks for checking out my little python app. :D

The purpose of this program is to take the wonderful information available on https://dunestatus.com/?type=public and provide live updates on a specific world and sietch from it so you can see when the hagga basin you want to join unlocks.

When launching the program it will ask you which region, world, and sietch you wish to monitor, while it isn't case sensitive, make sure you type these in correctly. After clicking OK a line graph will show up which is monitoring the capacity of the sietch, this fluxuates depending on the player activity on that specific sietch and will slowly go down if the sietch has light activity for a while. If it drops below 100% then the sietch will unlock allowing a new player to create a character on it.

The graph updates every 3 minutes so it should allow you to quickly know when the sietch you want is open. Good luck sleepers!

![Capture](https://github.com/user-attachments/assets/4964e34e-3626-4dbc-89ed-a77ff5ecab46)

**How to create an executable file for this program**

For those of you who want to use this yourselves and want to make it into an exe file. Good news! It is possible, bad news is that it is 500MB so I can't upload an exe directly to github. Unfortunately this means you need to generate it yourself. Don't worry, it is easy and I provided everything you need.

Step 1: Install python at https://www.python.org/downloads/ if you do not already have it.
Step 2: Open terminal/cmd and type the following commands: "pip install pyinstaller", "pip install tkinter", "pip install playwright", "install playwright"
Step 3: Download the DA_Monitor.spec and DA_Sietch_Lock_Monitor.py files from this reposotory and put them in the same file directory on your computer.
Step 4: In your terminal/cmd navigate to that directory and once there run "pyinstaller DA_Monitor.spec" This should generate a folder called dist and inside it will be the exe file. Feel free to delete everything else afterwards.
