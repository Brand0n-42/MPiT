# MPiT - music Player in Terminal

import os, sys, termios, tty, time, select
from just_playback import Playback
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-d', '-dir', dest='directory', type=str, default='~/Music', help='defines directory. default is ~/Music')
parser.set_defaults(dir='~/Music')

args = parser.parse_args()

def clamp(x, minimum, maximum):
	return max(minimum, min(x, maximum))

class MusicPlayer:
	def __init__(self, music_dir):
		self.music_dir      = music_dir
		
		self.songs          = self.load_songs()
		self.song_list_len  = len(self.songs)
		self.selected_index = 0
		self.playing_index  = -1
		
		#	0:stopped
		#	1:play
		#	2:pause
		self.state          = 0
		
		self.volume_change  = False
		
		self.progress       = 0
		self.current_length = 0
		
		#init audio
		self.playback = Playback()
		
		#init treminal for tui
		print("\x1b[?1049h", end="", flush=True) #switch to alt buffer
		print("\x1b[H") #curser goes to home
	
	def load_songs(self):
		if not os.path.isdir(self.music_dir):
			self.show_error(f"Directory not found:\n{self.music_dir}")
			sys.exit(1)
		
		songs = sorted(
			f for f in os.listdir(self.music_dir)
			if f.lower().endswith(".mp3") or f.lower().endswith(".wav") or f.lower().endswith(".ogg")
		)
		
		if not songs:
			self.show_error(f"No supported files found in:\n{self.music_dir}")
			sys.exit(1)
		
		return songs
	
	def show_error(self, message):
		
		print("\033[H\033[2J", end="") #clears terminal
		
		for i, line in enumerate(message.splitlines()):
			print(line)
	
	def play_song(self, index):
		
		self.playback.stop()
		
		file_path = os.path.join(self.music_dir, self.songs[index])
		
		self.playback.load_file(file_path)
		self.playback.play()
		
		self.playing_index = index
		self.state = 1
		
		self.current_length = self.playback.duration
	
	def update_progress(self):
		
		if self.state != 1:
			return
		
		if self.current_length <= 0:
			self.progress = 0
			return
		
		self.progress = (self.playback.curr_pos / self.current_length) * 100
		
		if self.playback.curr_pos > self.current_length-1:
			next_index = (self.playing_index + 1) % self.song_list_len
			self.play_song(next_index)
	
	def toggle_play_pause(self):
		if self.state == 0:
			self.play_song(self.selected_index)
			
		elif self.state == 1:
			self.playback.pause()
			self.state = 2
			
		elif self.state == 2:
			if self.playing_index == self.selected_index:
				self.playback.resume()
				self.state = 1
			else:
				self.play_song(self.selected_index)
	
	def getch(self):
		fd = sys.stdin.fileno()
		attr = termios.tcgetattr(fd)
		try:
			tty.setraw(fd)
			
			if not select.select([fd], [], [], 0.01)[0]:
				return None
			
			ch = os.read(fd, 1)
			if ch == b'\x1b':
				while select.select([fd], [], [], 0.01)[0]:
					ch += os.read(fd, 1)
			return ch.decode(errors='ignore')
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, attr)
	
	def handle_input(self):
		
		key = self.getch()
		
		self.volume_change = False
		
		if key is None:
			return
		
		if (key == 'q'):
			sys.exit(0)
			
		elif (key == ' '):
			self.toggle_play_pause()
			
		elif (key == 'n') and (self.playing_index != -1):
			self.selected_index = (self.playing_index + 1) % self.song_list_len
			self.play_song(self.selected_index)
			
		elif (key == '\x1bOA') or (key == '\x1b[A'): #up
			self.selected_index = (self.selected_index - 1) % self.song_list_len
			
		elif (key == "\x1bOB") or (key == '\x1b[B'): #down
			self.selected_index = (self.selected_index + 1) % self.song_list_len
			
		elif (key == "\x1bOC") or (key == '\x1b[C'): #right
			self.playback.set_volume(clamp(self.playback.volume + 0.01,0,1))
			self.volume_change = True
			
		elif (key == "\x1bOD") or (key == '\x1b[D'): #left
			self.playback.set_volume(clamp(self.playback.volume - 0.01,0,1))
			self.volume_change = True
	
	def print_at(self,x, y, text):
		print(f"\033[{y};{x}H{text}", end="", flush=True)
	
	def draw_progress_bar(self, height, width):
		bar_width = max(0, width - 6)
		
		draw_height = height - 1
		
		if self.volume_change:
			filled = bar_width * self.playback.volume
			self.print_at(3,draw_height - 1, f"Volume:{int(self.playback.volume * 100)}")
			
		else:
			filled = bar_width * self.progress / 100
		
		bar = "#" * int(filled)
		
		self.print_at(2,draw_height, "[")
		self.print_at(3,draw_height, f"{bar}")
		self.print_at(width-3,draw_height, "]")
	
	def draw_song_list(self, height, width):
		
		max_visible = height - 4
		
		if self.song_list_len <= max_visible:
			offset = 0
		else:
			half = int(max_visible / 2)
			if self.selected_index < half:
				offset = 0
			elif self.selected_index >= self.song_list_len - half:
				offset = self.song_list_len - max_visible
			else:
				offset = self.selected_index - half
		
		max_id = min(offset + max_visible, self.song_list_len)
		
		for i in range(offset, max_id):
			
			if i == self.playing_index:
				if self.state == 1:
					prefix = "> "
				else:
					prefix = "= "
			else:
				prefix = "  "
			
			prefix = " " * (len(str(max_id)) - len(str(i+1))) + prefix
			
			name = self.songs[i][:-4]
			name = name[:width - 9]
			
			line = f"{i + 1}. {prefix}{name}"
			row = 2 + i - offset
			
			if i == self.selected_index:
				self.print_at(2,row,"\033[30;47m" + line + "\033[0m")
			else:
				self.print_at(2,row, line)
	
	def draw(self):
		print("\033[H\033[2J", end="") #clears screen
		
		width,height = os.get_terminal_size()
		
		while height < 8:
			self.show_error("terminal to small \nminimum size is 8 lines")
			height = os.get_terminal_size()[1]
		while width < 9:
			self.show_error("terminal to small \nminimum size is 9 columns")
			width = os.get_terminal_size()[0]
		
		#--draws a border around the edge of the terminal--
		print("+" + "-"*(width-2) + "+")
		print(("|" + " "*(width-2) + "|") * (height-2))
		print("+" + "-"*(width-2) + "+", end="", flush=True)
		
		self.draw_progress_bar(height, width)
		self.draw_song_list(height, width)
	
	def run(self):
		while True:
			self.update_progress()
			self.handle_input()
			self.draw()

if __name__ == "__main__":
	try:
		music_dir = os.path.expanduser(args.directory)
		MusicPlayer(music_dir).run()
	finally: #resets terminal if tui is closed
		print("\x1b[?1049l", end="", flush=True)
		print("\033[?25h", end="", flush=True)