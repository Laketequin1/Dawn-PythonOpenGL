import pygame as pg
import OpenGL.GL as gl
import numpy as np
import ctypes
import OpenGL.GL.shaders as gls
import pyrr

"""
    Todo:
    
    choose palette
    draw mountain
    draw floor grid
    
    draw player
    player controls: movement and shooting
    update player
    animate sentient component drop
    
    draw bullets
    update bullets
    
    spawn and draw enemies
    update enemies
    
    collision checks
    
    draw powerups
    update powerups
    collision checks
"""

class App:
    
    def __init__(self, screen_size):
        
        self.screen_width, self.screen_height = screen_size
        
        self.renderer = GraphicsEngine()
        
        self.scene = Scene()
        
        self.last_time = pg.time.get_ticks()
        self.current_time = 0
        self.num_frames = 0
        self.frame_time = 0
        self.light_count = 0
        
        # Start main
        self.main_loop()
        
    def main_loop(self):
        
        running = True
        while running:
            # Check events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False
            
            self.handle_keys()
            
            self.scene.update(self.frame_time * 0.05)
            
            self.renderer.render(self.scene)
            
            # Timing
            self.calculate_framerate()
            
        self.quit()
    
    def handle_keys(self):
        
        keys = pg.key.get_pressed()
    
    def calculate_framerate(self):
        
        self.current_time = pg.time.get_ticks()
        delta = self.current_time - self.last_time
        
        if (delta >= 1000):
            framerate = max(1,int(1000.0 * self.num_frames/delta))
            pg.display.set_caption(f"Running at {framerate} fps.")
            self.last_time = self.currentTime
            self.num_frames = -1
            self.frame_time = float(1000.0 / max(1,framerate))
            
        self.num_frames += 1
    
    def quit(self):
        
        # Remove allocated memory
        self.renderer.destroy()


class SimpleComponent:
    
    def __init__(self, position, velocity):
        
        self.position = np.array(position, dtype=np.float32)
        self.velocity = np.array(velocity, dtype=np.float32)


class SentientComponent:
    
    def __init__(self, position, eulers, health):
        
        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
        self.velocity = np.array([0, 0, 0], dtype=np.float32)
        
        self.state = "stable"
        self.health = health
        self.can_shoot = True
        self.reloading = False
        self.reload_time = 0


class Scene:
    
    def __init__(self):
        
        self.enemy_spawn_rate = 0.1
        self.powerup_spawn_rate = 0.05
        self.enemy_shoot_rate = 0.1
        
        self.player = SentientComponent(
            position = [0, 0, 0],
            eulers = [0, 90, 0],
            health = 36
        )
        
        self.enemys = []
        self.bullets = []
        self.powerups = []
        
    def update(self, rate):
        
        pass
    
    def move_player(self, d_pos):
            
            pass


class GraphicsEngine:
    
    def __init__(self):
        
        # Initilize pygame
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode((640,480), pg.OPENGL|pg.DOUBLEBUF)
        
        # Initilize OpenGL
        gl.glClearColor(0.0, 0.0, 0.0, 1)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Create renderpasses and resources
        shader = self.create_shader("shaders/vertex.txt", "shaders/fragment.txt")
        self.renderPass = RenderPass(shader)
        
    def create_shader(self, vertexFilepath, fragmentFilepath):
        
        with open(vertexFilepath, 'r') as f:
            vertex_src = f.readlines()
        
        with open(fragmentFilepath, 'r') as f:
            fragment_src = f.readlines()
        
        shader = gls.compileProgram(
            gls.compileShader(vertex_src, gl.GL_VERTEX_SHADER),
            gls.compileShader(fragment_src, gl.GL_FRAGMENT_SHADER)
        )
        
        return shader
        
    def render(self, scene):
            
        # Refresh screen
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Draw
        self.renderPass.render(scene, self)
        
        pg.display.flip()
    
    def quit(self):
        
        pg.quit()


class RenderPass:
    
    def __init__(self, shader):
        
        # Initilize OpenGL
        self.shader = shader
        gl.glUseProgram(self.shader)
        
        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = 800/600,
            near = 0.1, far = 50, dtype = np.float32
        )
        gl.glUniformMatrix4fv(
            gl.glGetUniformLocation(self.shader, "projection"),
            1, gl.GL_FALSE, projection_transform
        )
        self.modelMatrixLocation = gl.glGetUniformLocation(self.shader, "model")
        self.viewMatrixLocation = gl.glGetUniformLocation(self.shader, "view")
        self.colorLoc = gl.glGetUniformLocation(self.shader, "object_color")
    
    def render(self, scene, engine):
        
        gl.glUseProgram(self.shader)
        
        view_transform = pyrr.matrix44.create_look_at(
            eye = scene.player.position,
            target = scene.player.position + scene.player.forwards,
            up = scene.player.up,
            dtype = np.float32
        )
        
        gl.glUniformMatrix4fv(self.viewMatrixLocation, 1, gl.GL_FALSE, view_transform)
    
    def destroy(self):
        
        gl.glDeleteProgram(self.shader)


class Mesh:
    
    def __init__(self, filepath):
        
        # x, y, z, s, t, nx, ny, nz
        self.vertices = self.load_mesh(filepath)
        
        # // is integer division
        self.vertex_count = len(self.vertices) // 3
        self.vertices = np.array(self.vertices, dtype=np.float32)
        
        # Create a vertex array where attributes for buffer are going to be stored, bind to make active, needs done before buffer
        self.vao = gl.glGenVertexArrays(1) 
        gl.glBindVertexArray(self.vao)
        
        # Create a vertex buffer where the raw data is stored, bind to make active, then store the raw data at the location
        self.vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, gl.GL_STATIC_DRAW)
        
        # Enable attributes for buffer. Add attribute pointer for buffer so gpu knows what data is which. Vertex shader.
        # Location 1 - Postion
        gl.glEnableVertexAttribArray(0)
        # Location, number of floats, format (float), gl.GL_FALSE, stride (total length of vertex, 4 bytes times number of floats), ctypes of starting position in bytes (void pointer expected)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 12, ctypes.c_void_p(0))
    
    @staticmethod
    def load_mesh(filepath):
    
        vertices = []
        
        flags = {"v": [], "vt": [], "vn": []}
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
            for line in lines:
                line.replace("\n", "")
                
                first_space = line.find(" ")
                flag = line[0:first_space]
                
                if flag in flags.keys():
                    line = line.replace(flag + " ", "")
                    line = line.split(" ")
                    flags[flag].append([float(x) for x in line])
                elif flag == "f":
                    line = line.replace(flag + " ", "")
                    line = line.split(" ")
                    
                    face_vertices = []
                    face_textures = []
                    face_normals = []
                    for vertex in line:
                        l = vertex.split("/")
                        face_vertices.append(flags["v"][int(l[0]) - 1])
                        face_textures.append(flags["vt"][int(l[1]) - 1])
                        face_normals.append(flags["vn"][int(l[2]) - 1])
                    triangles_in_face = len(line) - 2
                    vertex_order = []
                    for x in range(triangles_in_face):
                        vertex_order.extend((0, x + 1, x + 2))
                    for x in vertex_order:
                        vertices.extend((*face_vertices[x], *face_textures[x], *face_normals[x]))
        
        return vertices
    
    def destroy(self):
        
        # Remove allocated memory
        gl.glDeleteVertexArrays(1, (self.vao, ))
        gl.glDeleteBuffers(1, (self.vbo, ))
        

if __name__ == "__main__":
    myApp = App((800, 600))