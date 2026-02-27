# MPiT - music Player in Terminal

import math
import os
import sys
import time
import curses
import pygame
from enum import Enum

import mutagen



import argparse


FPS = 24


parser = argparse.ArgumentParser()
parser.add_argument('-d', '-dir', dest='directory', type=str, help='defines directory')
parser.add_argument('-m', '-min', dest='minimum_ui', action='store_true', help='if included uses minimum ui')

args = parser.parse_args()


def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))


class SongState(Enum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class MusicPlayer:

    def __init__(self, stdscr, music_dir, minimum_ui):
        self.stdscr         = stdscr
        self.music_dir      = music_dir
        self.minimum_ui     = minimum_ui

        self.songs          = self.load_songs()
        self.selected_index = 0
        self.playing_index  = -1
        self.state          = SongState.STOPPED

        self.volume_change  = False

        self.progress       = 0
        self.current_length = 0

        #init audio
        try:
            pygame.mixer.init()
        except pygame.error as e:
            self.show_error(f"Audio initialization failed:\n{e}")
        
        #init curses
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

        curses.assume_default_colors(curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)


    def load_songs(self):
        if not os.path.isdir(self.music_dir):
            self.show_error(f"Directory not found:\n{self.music_dir}")

        songs = sorted(
            f for f in os.listdir(self.music_dir)
            if f.lower().endswith(".mp3") or f.lower().endswith(".wav") or f.lower().endswith(".ogg")
        )

        if not songs:
            self.show_error(f"No supported files found in:\n{self.music_dir}")

        return songs

    def show_error(self, message):
        self.stdscr.clear()
        for i, line in enumerate(message.splitlines()):
            try:
                self.stdscr.addstr(i, 0, line)
            except curses.error:
                pass
        
        self.stdscr.refresh()

        self.stdscr.nodelay(False)
        self.stdscr.getch()

        sys.exit(1)


    def play_song(self, index):

        pygame.mixer.music.unload()

        file_path = os.path.join(self.music_dir, self.songs[index])

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        self.playing_index = index
        self.state = SongState.PLAYING

        # Cache song length once
        self.current_length = mutagen.File(file_path).info.length


    def update_progress(self):
        if self.state != SongState.PLAYING:
            return

        if self.current_length <= 0:
            self.progress = 0
            return

        pos_s = pygame.mixer.music.get_pos() / 1000.0

        self.progress = (pos_s / self.current_length) * 100

        if self.progress >= 99:
            next_index = (self.playing_index + 1) % len(self.songs)
            self.play_song(next_index)

    def toggle_play_pause(self):
        if self.state == SongState.STOPPED:
            self.play_song(self.selected_index)
            return

        if self.state == SongState.PLAYING:
            pygame.mixer.music.pause()
            self.state = SongState.PAUSED

            return

        if self.state == SongState.PAUSED:
            if self.playing_index == self.selected_index:
                pygame.mixer.music.unpause()
                self.state = SongState.PLAYING
            else:
                self.play_song(self.selected_index)

            return

    def handle_input(self):

        key = self.stdscr.getch()

        if key == ord('q'):
            sys.exit(0)
            return

        if key == ord(' '):
            self.toggle_play_pause()
            return

        if key == ord('n') and self.playing_index != -1:
            self.selected_index = (self.playing_index + 1) % len(self.songs)
            self.play_song(self.selected_index)
            return
            
        if key == curses.KEY_UP:
            self.selected_index = (self.selected_index - 1) % len(self.songs)
            return

        if key == curses.KEY_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.songs)
            return
        
        if key == curses.KEY_RIGHT:
            pygame.mixer.music.set_volume(clamp(pygame.mixer.music.get_volume() + 0.01,0,1))

            self.volume_change = True
            return

        if key == curses.KEY_LEFT:
            pygame.mixer.music.set_volume(clamp(pygame.mixer.music.get_volume() - 0.01,0,1))

            self.volume_change = True
            return


    def draw_progress_bar(self, height, width):
        bar_width = max(0, width - 6)

        if self.volume_change:
            filled = int(bar_width * pygame.mixer.music.get_volume())

            self.stdscr.addstr(height - 3, 3, f"volume:{int(pygame.mixer.music.get_volume() * 100)}")

            self.volume_change = False
        else:
            filled = int(bar_width * self.progress / 100)

        bar = "#" * filled

        try:
            self.stdscr.addch(height - 2, 2, "[")
            self.stdscr.addstr(height - 2, 3, f"{bar}")
            self.stdscr.addch(height - 2, width-3, "]")
        except curses.error:
            pass

    def draw_song_list(self, height, width):

        if self.minimum_ui == False:
            max_visible = height - 5
        else:
            max_visible = height

        if len(self.songs) <= max_visible:
            offset = 0
        else:
            half = max_visible // 2
            if self.selected_index < half:
                offset = 0
            elif self.selected_index >= len(self.songs) - half:
                offset = len(self.songs) - max_visible
            else:
                offset = self.selected_index - half

        max_id = min(offset + max_visible, len(self.songs))

        for i in range(offset, max_id):

            if self.minimum_ui == False:
                row = 2 + i - offset
            else:
                row = i - offset

            name = self.songs[i][:-4]

            if self.minimum_ui == False:
                name = name[:width - 9]
            else:
                name = name[:width - 6]

            prefix = "  "
            if i == self.playing_index:
                prefix = "> " if self.state == SongState.PLAYING else "= "

            prefix = " " * (int(math.log10(max_id)) - int(math.log10(i+1))) + prefix
            
            line = f"{i + 1}. {prefix}{name}"

            try:
                if i == self.selected_index:
                    if self.minimum_ui == False:
                        self.stdscr.addstr(row, 2, line, curses.color_pair(1))
                    else:
                        self.stdscr.addstr(row, 0, line, curses.color_pair(1))
                else:
                    if self.minimum_ui == False:
                        self.stdscr.addstr(row, 2, line)
                    else:
                        self.stdscr.addstr(row, 0, line)
            except curses.error:
                pass

    def draw(self):
        self.stdscr.clear()

        height, width = self.stdscr.getmaxyx()

        if self.minimum_ui == False:
            if height < 8:
                self.show_error("terminal to small \nminimum size is 8 lines")
        else:
            if height < 3:
                self.show_error("terminal to small \nminimum size is 3 lines in minimum mode")

        if width < 9:
            self.show_error("terminal to small \nminimum size is 9 columns")


        if self.minimum_ui == False:

            #--draws a border around the edge of the terminal--
            self.stdscr.border('|', '|', '-', '-', '+', '+', '+', '+')

            self.draw_progress_bar(height, width)
            self.draw_song_list(height, width)
        
        self.draw_song_list(height, width)

        self.stdscr.refresh()


    def run(self):
        while True:

            self.update_progress()
            self.draw()
            self.handle_input()
            
            time.sleep(1 / FPS)


def main(stdscr):

    if args.directory != None:
        music_dir = os.path.expanduser(args.directory)
    else:
        music_dir = os.path.expanduser("~/Music")

    minimum_ui = args.minimum_ui

    MusicPlayer(stdscr, music_dir, minimum_ui).run()


if __name__ == "__main__":

    curses.wrapper(main)
