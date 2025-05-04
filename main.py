import os
import remi.gui as gui
from remi import start, App
import random
import threading
import time

class Display(App):
    def __init__(self, *args):
        super(Display, self).__init__(*args)

    def main(self):
        container = gui.Widget(style={'width':'600px', 'height': '600px', 'position': 'relative', 'background-color': 'white'})

        self.dot = gui.Widget(style={'width':'20px', 'height': '20px', 'background-color': 'red', 'border-radius': '50%', 'position': 'absolute', 'left': '0px', 'top': '0px'})

        container.append(self.dot)
        threading.Thread(target=self.move_loop, daemon=True).start()
        
        return container

    def move_loop(self):
        while True:
            x = random.randint(0,580)
            y = random.randint(0,580)
            self.dot.style['left'] = f'{x}px'
            self.dot.style['top'] = f'{x}px'
            time.sleep(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    start(Display, address='0.0.0.0', port=port)
