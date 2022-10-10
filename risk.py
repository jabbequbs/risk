#! python3

"""
Adapted from https://gist.github.com/davepape/7324958
Textures from https://www.solarsystemscope.com/textures/
Ideas from https://www.youtube.com/watch?v=sLqXFF8mlEU&t=972s
"""

from pyglet.gl import *
from math import *


def floatrange(start, stop, step):
    result = start
    while result < stop:
        yield result
        result += step

def clamp(x, minVal, maxVal):
    if x < minVal:
        return minVal
    elif x > maxVal:
        return maxVal
    else:
        return x

def wrap(x, minVal, maxVal):
    if x < minVal:
        x += maxVal - minVal
    elif x > maxVal:
        x -= maxVal - minVal
    return x

def normalized(vertices):
    if len(vertices) % 3 != 0:
        raise ArgumentError("len(vertices) must be a multiple of three (3)")
    result = []
    for i in range(0, len(vertices), 3):
        vlen = hypot(*vertices[i:i+3])
        result.extend((vertices[i]/vlen, vertices[i+1]/vlen, vertices[i+2]/vlen))
    return result

def texcoords(vertices):
    if len(vertices) % 3 != 0:
        raise ArgumentError("len(vertices) must be a multiple of three (3)")
    result = []
    for i in range(0, len(vertices), 3):
        x, y, z = vertices[i:i+3]
        s = wrap((atan2(x, z) + pi)/(2*pi), 0, 1)
        t = wrap((asin(y) + pi/2)/pi, 0, 1)
        result.extend((s, t))
    return result

def get_vertices(radius):
    faces = {name:[] for name in ("left", "right", "top", "bottom", "front", "back")}
    step = radius/8
    for b in floatrange(-radius, radius, step):
        for face in faces:
            faces[face].append([])
        for c in floatrange(-radius, radius, step):
            faces["left"][-1].extend((-radius, b, c, -radius, b+step, c))
            faces["right"][-1].extend((radius, b, c, radius, b+step, c))
            faces["bottom"][-1].extend((b, -radius, c, b+step, -radius, c))
            faces["top"][-1].extend((b, radius, c, b+step, radius, c))
            faces["front"][-1].extend((b, c, -radius, b+step, c, -radius))
            faces["back"][-1].extend((b, c, radius, b+step, c, radius))
        faces["left"][-1].extend((-radius, b, radius, -radius, b+step, radius))
        faces["right"][-1].extend((radius, b, radius, radius, b+step, radius))
        faces["bottom"][-1].extend((b, -radius, radius, b+step, -radius, radius))
        faces["top"][-1].extend((b, radius, radius, b+step, radius, radius))
        faces["front"][-1].extend((b, radius, -radius, b+step, radius, -radius))
        faces["back"][-1].extend((b, radius, radius, b+step, radius, radius))

    result = []
    colors = ((255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255),
        (255, 255, 0, 255), (255, 0, 255, 255), (0, 255, 255, 255))
    for face, color in zip(faces, colors):
        for strip in faces[face]:
            strip = normalized(strip)
            colors = []
            for i in range(0, len(strip), 3):
                s, t = texcoords(strip[i:i+3])
                colors.extend((255, int(255*s), int(255*s), 255))
            result.append(pyglet.graphics.vertex_list(
                len(strip)//3,
                ("v3f", strip),
                # ("c4B", color*(len(strip)//3))
                # ("c4B", colors)
                ("t2f", texcoords(strip))
                ))
            # TODO: fix the texture coords around the international date line
    return result

def get_vertices_old(radius):
    step = 10
    vlists = []
    sphere_height = 2 # [sin(90), sin(270)]
    for lat in range(-90,90,step):
        verts = []
        texc = []
        for lon in range(-180,181,step):
            x = -cos(radians(lat)) * cos(radians(lon))
            y = sin(radians(lat))
            z = cos(radians(lat)) * sin(radians(lon))
            s = (lon+180) / 360.0
            t = (lat+90) / 180.0
            verts += [x,y,z]
            texc += [s,t]
            x = -cos(radians((lat+step))) * cos(radians(lon))
            y = sin(radians((lat+step)))
            z = cos(radians((lat+step))) * sin(radians(lon))
            s = (lon+180) / 360.0
            t = ((lat+step)+90) / 180.0
            verts += [x,y,z]
            texc += [s,t]
        vlist = pyglet.graphics.vertex_list(len(verts)//3, ('v3f', verts), ('t2f', texc))
        vlists.append(vlist)
    return vlists

def from_hex(color):
    if color[0] == "#":
        color = color[1:]
    if len(color) != 6:
        raise ArgumentError("hex color must be 6 characters long")
    return tuple(int(color[i:i+2], base=16) for i in range(0, len(color), 2))

class Menu:
    def __init__(self):
        self.batches = {}
        self.batches["main"] = self.get_main_batch()
        self.state = "main"

    def draw(self):
        self.batches[self.state].draw()

    def click(self, x, y):
        pass

    def get_main_batch(self):
        width, height = 400, 400
        result = pyglet.graphics.Batch()
        result.add(4, GL_TRIANGLE_STRIP, pyglet.graphics.Group(),
            ("v2i", (0, 0, 0, -height, width, 0, width, -height)),
            ("c4B", (255, 0, 0, 128)*4))
        return result


class RiskWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__(1280, 720, caption="Risk", resizable=True)
        self.ui_batch = pyglet.graphics.Batch()
        self.player_colors = [
            ["ff0000", "00ff00", "0000ff", "4b0082", "00ffff", "ff00ff", "ffff00", "808080", "ffffff",],
            ["dc143c", "228b22", "1e90ff", "ff69b4", "ff8c00", "ffff00", "4b0082", "808080", "f8f8ff",],
            ["8b008b", "2f4f4f", "ff00ff",],
            ["00008b", "00bfff", "008b8b",],
            ]
        button_width = 30
        button_height = 20
        button_spacing = 10
        for rowIdx, row in enumerate(self.player_colors):
            for idx, color in enumerate(row):
                vertices = ("v2i", (
                    (idx*button_width)+(idx*button_spacing), -rowIdx*(button_height+button_spacing),
                    (idx*button_width)+(idx*button_spacing), -rowIdx*(button_height+button_spacing)-button_height,
                    (idx*button_width)+(idx*button_spacing)+button_width, -rowIdx*(button_height+button_spacing),
                    (idx*button_width)+(idx*button_spacing)+button_width, -rowIdx*(button_height+button_spacing)-button_height,))
                colors = ("c3B", from_hex(color)*4)
                self.ui_batch.add(4, GL_TRIANGLE_STRIP, pyglet.graphics.Group(), vertices, colors)
        self.label = pyglet.text.Label("Hello, world", font_name="Times New Roman", font_size=36, x=0, y=0, color=(255, 255, 255, 255))
        self.fpsDisplay = pyglet.window.FPSDisplay(self)
        self.texture = pyglet.image.load('2k_earth_daymap.jpg').get_texture()
        self.sphere_height = 2
        self.vertices = get_vertices_old(self.sphere_height/2)
        self.tilt = 20
        self.rotation = 0
        self.screen_height = 3
        self.rotation_factor = self.sphere_height / self.screen_height * self.height / 180
        self.menu = Menu()
        # self.maximize()
        self.set_icon(pyglet.image.load("icon_16.png"), pyglet.image.load("icon_32.png"))
        glPointSize(2)
        glColor3f(1, 1, 1)

    def on_draw(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glEnable(GL_BLEND)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        ratio = self.width / self.height * self.screen_height / 2.0
        glOrtho(-ratio, ratio, -self.screen_height/2, self.screen_height/2, -2, 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(self.tilt, 1, 0, 0)
        glRotatef(self.rotation, 0, 1, 0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        for v in self.vertices:
            v.draw(GL_TRIANGLE_STRIP)

        # Draw UI stuff (overtop of the globe)
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glPushMatrix()
        glTranslatef(0, self.height, 0)
        self.ui_batch.draw()
        self.fpsDisplay.draw()
        # self.label.draw()
        glPopMatrix()
        glTranslatef(self.width/2, self.height/2, 0)
        self.menu.draw()

    def update(self, dt):
        self.rotation += dt / 24 * 360

    def on_resize(self, width, height):
        self.rotation_factor = self.sphere_height / self.screen_height * self.height / 180

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.rotation = wrap(self.rotation + dx/self.rotation_factor, 0, 360)
        self.tilt = clamp(self.tilt - dy/self.rotation_factor, -80, 80)

    def on_mouse_scroll(self, x, y, dx, dy):
        self.screen_height = clamp(self.screen_height * pow(2, -dy), 3*pow(2, -4), 3)
        self.rotation_factor = self.sphere_height / self.screen_height * self.height / 180


if __name__ == '__main__':
    window = RiskWindow()
    pyglet.clock.schedule_interval(window.update, 1/30.0)
    pyglet.app.run()
