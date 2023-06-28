import tkinter as tk
from tkinter import ttk, Label, Scale, Entry, HORIZONTAL
from positionerComms import *

# Main Menu
class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        label = tk.Label(self, text="El-Az Postioner Motion Manager", font=("Cooper Std Black", 18, "bold"))
        label.pack(pady=10, padx=10)

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x')
        
        button = tk.Button(self, text="Manual Motor Positioning", command=lambda: self.controller.show_frame(ManualControl))
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        button = tk.Button(self, text="Autonomous Search", command=lambda: self.controller.show_frame(AutonomousControl))
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        button = tk.Button(self, text="Settings", command=lambda: self.controller.show_frame(Settings))
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x')

        label = tk.Label(self, text="Select Motor", font=("Cooper Std Black", 18, "bold"))
        label.pack(pady=10, padx=10)

        button = tk.Button(self, text="Az / El Motor", command=lambda: [switch_to_az_el, updateMotorSelection("Az / El Motor")])
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        button = tk.Button(self, text="El / Az Motor", command=lambda: [switch_to_el_az, updateMotorSelection("El / Az Motor")])
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        def updateMotorSelection(motor):
            statusMessage.config(text=f'{motor} is currently selected')
            
        statusMessage=Label(self, text="Az / El Motor is currently selected", font=("Cooper Std Black", 15))
        statusMessage.pack(pady=10)
 
# Motor Positioning
class ManualControl(tk.Frame):
    def __init__(self, parent, controller):

        def Send():
            az = slide_az.get()
            el = slide_el.get()

            set_el_az(el, az)

        def SendOriginal():
            bring_to_home()

        def restart():
            reboot()
            slide_az.set(0)
            slide_el.set(0)


        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        startup()
        
        label = tk.Label(self, text="Manual Motor Positioning", font=("Cooper Std Black", 18, "bold"))
        label.pack(pady=10, padx=10)

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x')

        label = Label(self, text='Azimuth (Rotation)', font=("Cooper Std Black", 15))
        label.pack(ipadx=10, ipady=10)

        slide_az = Scale(self, from_ = 0, to = 360, length = 600, tickinterval = 30, orient = HORIZONTAL)
        slide_az.pack(ipadx=10, ipady=10)
        slide_az.set(get_azimuth())

        label = Label(self, text='Elevation (Tilt)', font=("Cooper Std Black", 15))
        label.pack(ipadx=10, ipady=10)

        slide_el = Scale(self, from_ = -60, to = 60, length = 600, tickinterval = 30, orient = HORIZONTAL)
        slide_el.pack(ipadx=10, ipady=10)
        slide_el.set(get_elevation())

        button = tk.Button(self, text="Apply", command=Send)
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        button = tk.Button(self, text="Kill All Motion", command=halt)
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        button = tk.Button(self, text="Send to Original Position", command=SendOriginal)
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)
        
        button = tk.Button(self, text="Reboot", command=restart)
        button.pack(ipadx=10, ipady=10, padx=10, pady=10, side=tk.RIGHT)

        button = tk.Button(self, text="Back", command=lambda: self.controller.show_frame(HomePage))
        button.pack(ipadx=10, ipady=10, padx=10, pady=10, side=tk.LEFT)

# Autonomous Search Page
class AutonomousControl(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = tk.Label(self, text = "Autonomous Search Postioner", font=("Cooper Std Black", 18, "bold"))
        label.pack(pady=10, padx=10)

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x')

        button = tk.Button(self, text="Sweep", command=lambda: self.controller.show_frame(HomePage))
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        button = tk.Button(self, text="Back", command=lambda: self.controller.show_frame(HomePage))
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

class Settings(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        label = tk.Label(self, text="Settings", font=("Cooper Std Black", 18, "bold"))
        label.pack(pady=10, padx=10)

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x')

        label = Label(self, text='Acceleration (Degrees / s^2)', font=("Cooper Std Black", 15))
        label.pack(ipadx=10, ipady=10)

        acc=Entry(self, width=35)
        acc.pack()

        label = Label(self, text='Deceleration (Degrees / s^2)', font=("Cooper Std Black", 15))
        label.pack(ipadx=10, ipady=10)

        dec=Entry(self, width=35)
        dec.pack()

        label = Label(self, text='Velocity (Degrees / s)', font=("Cooper Std Black", 15))
        label.pack(ipadx=10, ipady=10)

        vel=Entry(self, width=35)
        vel.pack()

        label = Label(self, text='Stop (Degrees / s^2)', font=("Cooper Std Black", 15))
        label.pack(ipadx=10, ipady=10)

        stp=Entry(self, width=35)
        stp.pack()

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x')

        def updateMotionSettings():
            try:
                ac = int(acc.get())
                de = int(dec.get())
                st = int(stp.get())
                ve = int(vel.get())
                if ve <= 5:
                    statusMessage.config(text=f'Current Acceleration: {ac} Deceleration: {de} Stop: {st} Velocity: {ve}')
                    set_motion_parameters(ac, de, st, ve)
                else:
                    statusMessage.config(text=f'Value Error, Velocity Cannot Exceed 5 Degrees / S')
            except ValueError:
                print('Error:', str(ValueError))
                statusMessage.config(text=f'Value Error, Enter an Integer Value')

        
        ac, de, st, ve = get_motion_parameters()
        statusMessage=Label(self, text=f'Current Acceleration: {ac} Deceleration: {de} Stop: {st} Velocity: {ve}', font=("Cooper Std Black", 15, "bold"))
        statusMessage.pack(pady=10)

        button = tk.Button(self, text="Apply Changes", command=updateMotionSettings)
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

        button = tk.Button(self, text="Back", command=lambda: self.controller.show_frame(HomePage))
        button.pack(ipadx=10, ipady=10, padx=10, pady=10)

# Tkinter Interface
class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        def on_closing():
            bring_to_home()
            self.destroy()

        self.title("El-Az Postioner Motion Manager")
        self.geometry("640x575")
        self.protocol("WM_DELETE_WINDOW", on_closing)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        self.frames = {}
        
        for F in (HomePage, ManualControl, AutonomousControl, Settings):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(HomePage)
    
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

if __name__ == "__main__":  
    app = MainApplication()
    app.mainloop()