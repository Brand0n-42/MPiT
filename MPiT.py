# MPiT - music Player in Terminal

import os
import sys
import time
import curses
import pygame
import mutagen
import argparse

FPS = 30

parser = argparse.ArgumentParser()
parser.add_argument('-d', '-dir', dest='directory', type=str, default='~/Music', help='defines directory. default directory is ~/Music')

parser.set_defaults(dir='~/Music')

args = parser.parse_args()

def clamp(x, minimum, maximum):
	return max(minimum, min(x, maximum))

class MusicPlayer:
	def __init__(self, stdscr, music_dir):
		self.stdscr         = stdscr
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
		try:
			pygame.mixer.init()
		except pygame.error as e:
			self.show_error(f"Audio initialization failed:\n{e}")
			sys.exit(1)
		
		#init curses
		curses.curs_set(0)
		self.stdscr.nodelay(True)
		self.stdscr.keypad(True)
		
		curses.assume_default_colors(curses.COLOR_WHITE, curses.COLOR_BLACK)
		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
	
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
		
		self.stdscr.clear()
		
		for i, line in enumerate(message.splitlines()):
			self.stdscr.addstr(i, 0, line)
		
		self.stdscr.refresh()
		self.stdscr.nodelay(False)
		self.stdscr.getch()
		self.stdscr.nodelay(True)
	
	def play_song(self, index):
		
		pygame.mixer.music.unload()
		
		file_path = os.path.join(self.music_dir, self.songs[index])
		
		pygame.mixer.music.load(file_path)
		pygame.mixer.music.play()
		
		self.playing_index = index
		self.state = 1
		
		self.current_length = mutagen.File(file_path).info.length
	
	def update_progress(self):
		
		if self.state != 1:
			return
		
		if self.current_length <= 0:
			self.progress = 0
			return
		
		pos_s = pygame.mixer.music.get_pos() / 1000.0
		
		self.progress = (pos_s / self.current_length) * 100
		
		if self.progress >= 99:
			next_index = (self.playing_index + 1) % self.song_list_len
			self.play_song(next_index)
	
	def toggle_play_pause(self):
		if self.state == 0:
			self.play_song(self.selected_index)
			
		elif self.state == 1:
			pygame.mixer.music.pause()
			self.state = 2
			
		elif self.state == 2:
			if self.playing_index == self.selected_index:
				pygame.mixer.music.unpause()
				self.state = 1
			else:
				self.play_song(self.selected_index)
	
	def handle_input(self):
		
		key = self.stdscr.getch()
		
		self.volume_change = False
		
		if key == ord('q'):
			sys.exit(0)
			
		elif key == ord(' '):
			self.toggle_play_pause()
			
		elif key == ord('n') and self.playing_index != -1:
			self.selected_index = (self.playing_index + 1) % self.song_list_len
			self.play_song(self.selected_index)
			
		elif key == curses.KEY_UP:
			self.selected_index = (self.selected_index - 1) % self.song_list_len
			
		elif key == curses.KEY_DOWN:
			self.selected_index = (self.selected_index + 1) % self.song_list_len
			
		elif key == curses.KEY_RIGHT:
			pygame.mixer.music.set_volume(clamp(pygame.mixer.music.get_volume() + 0.01,0,1))
			self.volume_change = True
			
		elif key == curses.KEY_LEFT:
			pygame.mixer.music.set_volume(clamp(pygame.mixer.music.get_volume() - 0.01,0,1))
			self.volume_change = True
	
	def draw_progress_bar(self, height, width):
		bar_width = max(0, width - 6)
		
		draw_height = height - 2
		
		if self.volume_change:
			filled = bar_width * pygame.mixer.music.get_volume()
			
			self.stdscr.addstr(draw_height - 1, 3, f"volume:{int(pygame.mixer.music.get_volume() * 100)}")
			
		else:
			filled = bar_width * self.progress / 100
		
		bar = "#" * int(filled)
		
		self.stdscr.addch(draw_height, 2, "[")
		self.stdscr.addstr(draw_height, 3, f"{bar}")
		self.stdscr.addch(draw_height, width-3, "]")
	
	def draw_song_list(self, height, width):
		
		max_visible = height - 5
		
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
				self.stdscr.addstr(row, 2, line, curses.color_pair(1))
			else:
				self.stdscr.addstr(row, 2, line)
	
	def draw(self):
		self.stdscr.clear()
		
		height, width = self.stdscr.getmaxyx()
		
		while height < 8:
			self.show_error("terminal to small \nminimum size is 8 lines")
			height = self.stdscr.getmaxyx()[0]
		while width < 9:
			self.show_error("terminal to small \nminimum size is 9 columns")
			width = self.stdscr.getmaxyx()[1]
		
		#--draws a border around the edge of the terminal--
		self.stdscr.border('|', '|', '-', '-', '+', '+', '+', '+')
		
		self.draw_progress_bar(height, width)
		self.draw_song_list(height, width)
		
		self.stdscr.refresh()
	
	def run(self):
		while True:
			self.update_progress()
			self.handle_input()
			self.draw()
			
			time.sleep(1 / FPS)

def main(stdscr):
	music_dir = os.path.expanduser(args.directory)
	MusicPlayer(stdscr, music_dir).run()

if __name__ == "__main__":
	curses.wrapper(main)

