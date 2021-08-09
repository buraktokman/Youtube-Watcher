#!/usr/bin/env python3
# coding=utf-8
'''
#-------------------------------------------------------------------------------
Project		: YouTube Watcher
Module		: watcher
Purpose   	: Track YouTube channels and download new videos
Version		: 0.1.7 beta
Status 		: Development

Modified	:
Created   	:
Author		: Burak Tokman
Email 		: buraktokman@hotmail.com
Copyright 	: 2021, Bulrosa OU
Licence   	: EULA
			  Unauthorized copying of this file, via any medium is strictly prohibited
			  Proprietary and confidential
#-------------------------------------------------------------------------------
'''
from pathlib import Path
import subprocess
import threading
import datetime
import json
import time
# import pync
import sys
import os

CONFIG = {	'download' : True,
			'login' : False,
			'username' : '',
			'password' : '',
			'playlist-file' : str(Path(Path(__file__).parents[0] / 'playlist.txt')),
			'history-file' : str(Path(Path(__file__).parents[0] / 'history.txt')),
			'download-dir' : '/Volumes/WD/_VIDEO', # '~/Desktop/_VID'
			'update-interval' : 3, # Hour
			'thread-count' : 1}

# ------------------------------------------

def update_youtube():
	st = 'pip3 install --upgrade youtube-dl'
	with subprocess.Popen(st, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
		output, errors = p.communicate()

def timestamp():
	now = datetime.datetime.utcnow()
	output = '%.2d:%.2d:%.2d' % ((now.hour + 3) % 24, now.minute, now.second)
	return output


def parse_urls(playlist):
	st = 'youtube-dl -j --flat-playlist \'' + str(playlist) + '\''
	with subprocess.Popen(st, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
		output, errors = p.communicate()
	lines = output.decode('utf-8').splitlines()
	# print(lines)
	urls = []
	# Take first 2 videos
	i=1
	for url in lines:
		t = json.loads(url)
		# print(t['url'] + ' → ' + t['title'])
		id_temp = t['url']
		urls.append(id_temp)
		if i == 2:
			break
		i+=1
	# ERROR
	if len(urls) is 0:
		print("ERROR → No video found in playlist/channel. Update module.\npip3 install --upgrade youtube-dl")
		update_youtube()
		# exit()
	# Return
	# print( timestamp() + ' → Video count → ' + '' + str(len(urls)))
	return urls


def download_video(url):
	global CONFIG
	# Check if download dir is available
	if not os.path.isdir(CONFIG['download-dir']):
		print(' → CAUTION → ' + 'Download dir not available. ~/Desktop used as default')
		CONFIG['download-dir'] = '~/Desktop'
	# youtube-dl -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio' --merge-output-format mp4
	formats = ['22', '136', '18']
	download_status = False
	for format_temp in formats:
		if CONFIG['login'] == True: login_temp = '-u ' + str(CONFIG['username']) + ' -p ' + CONFIG['password']
		else:	login_temp = ''
		st = 'cd ' + CONFIG['download-dir'] + '&& youtube-dl ' + str(login_temp) + ' -f ' + format_temp + ' http://www.youtube.com/watch?v=' + str(url)
		lines = os.popen(st).read()
		if '100%' in lines:
			download_status = True
			break
		# elif 'ERROR' in lines:
	# Return
	return download_status


def check_new_urls(urls):
	global CONFIG
	with open(CONFIG['history-file']) as f:
		content = f.readlines()
	content = [x.strip() for x in content]
	# print(content)
	urls_new = []
	for url in urls:
		if url not in content:
			urls_new.append(url)
	return urls_new


def write_to_history(url):
	global CONFIG
	with open(CONFIG['history-file'], 'a') as f:
		f.write(url + '\n')


def load_playlists():
	global CONFIG
	with open(CONFIG['playlist-file'], encoding='utf-8') as f:
		content = f.readlines()
	temp_list = [x.strip() for x in content]
	playlist = []
	for line in temp_list:
		temp_line = line.split(',')
		temp_dict = {'name' : temp_line[0], 'url' : temp_line[1]}
		playlist.append(temp_dict)
	return playlist


def process_playlists(playlists):
	global CONFIG
	for playlist in playlists:
		time_start_temp = time.time()
		if '#' in playlist['name']:
			print( timestamp() + ' → WATCHER → ' + 'SKIPPING > ' + str(playlist['name']))
			continue
		else:
			print( timestamp() + ' → WATCHER → ' + '' + str(playlist['name']))
		# Get video URLs from playlist
		print( timestamp() + ' → ' + 'Fetching URLs ...')
		urls = parse_urls(playlist['url'])
		# Compare w/ history & Select new URLs
		# print( timestamp() + ' → Selecting new videos ...')
		urls = check_new_urls(urls)
		if len(urls) == 0:
			print( timestamp() + ' → WATCHER → ' + 'No new video (' + str(round((time.time() - time_start_temp), 2)) + 's)\n' + '• • •')
		else:
			# Process
			for url in urls:
				# Download
				print( timestamp() + ' → WATCHER → ' + 'Downloading → ' + str(url))
				if CONFIG['download'] == True:
					r = download_video(url)
				else:
					r = True
				# Get Video Title
				command = 'youtube-dl --get-title http://www.youtube.com/watch?v=' + str(url)
				try:
					if CONFIG['download'] == True:
						title = subprocess.check_output(command, shell=True).decode('utf-8')
					title = title.replace('\n', '') # Trim
				except Exception as e:
					print(timestamp() + ' → ERROR → Can\'t get video title')
					print(str(e))
					title = 'New video'

				print( timestamp() + ' → WATCHER → ' + '' + str(title))
				# Notify
				try:
					if CONFIG['download'] == True:
						title = playlist['name'] + ' → ' + title
						# pync.notify(title, appIcon=str(Path(Path(os.path.abspath(__file__)).parents[0] / 'youtube.png'))) # title='New Video' #  youtube.png
				except Exception as e:
					print(timestamp() + ' → ERROR → Notification error')
				if r == True:
					# Log
					write_to_history(url)
					print( timestamp() + ' → WATCHER → ' + 'Written to history → ' + str(url) + '\n')
				else:
					print(timestamp() + ' → ERROR → Occured. Cannot download video')
	print( timestamp() + ' → WATCHER → ' + 'Thread finished')
	# Raise exception
	exit()
	# try:
	# 	print(error)
	# except Exception as e:
	# 	raise


# ------------------------------------------


def main():
	global CONFIG
	time_start = time.time()
	# Load Playlists from file
	playlists = load_playlists()

	# Divide playlists for threads
	playlists = [playlists[i::CONFIG['thread-count']] for i in range(CONFIG['thread-count'])]

	# Define threads
	threads = []
	for x in range(0, CONFIG['thread-count']):
		print( timestamp() + ' → WATCHER → ' + 'THREAD ' + str(x) + ' → Configured')
		thread_name = 'T' + str(x) + '-youtube-watcher'
		t = threading.Thread(name=thread_name, target=process_playlists, args=(playlists[x], ))
		threads.append(t)
	# Start threads
	for x in range(0, CONFIG['thread-count']):
		print( timestamp() + ' → WATCHER → ' + 'THREAD ' + str(x) + ' → Started')
		threads[x].start()
	# Wait threads
	# for x in range(0, CONFIG['thread-count']):
	# 	print( timestamp() + ' → WATCHER → ' + 'Waiting thread ' + str(x) + ' to finish')
	# 	threads[x].join()
	# 	print( timestamp() + ' → WATCHER → ' + 'Thread ' + str(x) + ' finished')

	# print( timestamp() + ' → WATCHER → ' + 'Channels processed (' + str(i) + ' / ' + str(len(playlists)) + ') [' + str(round((time.time() - time_start) / 60, 2)) + 'm]\n' + '• • •')

if __name__ == '__main__':
	main()
	# time_left = UPDATE_INTERVAL
	# done = False
	# while True:
	# 	main()
	# 	while not done:
	# 		time_left = time_left - (10 / 60 / 60)
	# 		st = '{} Scan completed. Next loop in {:.2f} hours'.format(timestamp(), round(time_left, 3))
	# 		print(st, end='\r')
	# 		time.sleep(10)
	# 		if time_left <= 0:
	# 			print()
	# 			done = True
	# import youtube_dl
	#  download_video('8yB_UEVwuRM')
	# input_file = load_playlists()
	# for video in input_file:
	# 	print(video)
	# ydl_opts = {
	# 	'ignoreerrors': True}
	# with youtube_dl.YoutubeDL(ydl_opts) as ydl:
	#             info_dict = ydl.extract_info(video, download=False)
	#             for i in info_dict:
	#                 video_thumbnail = info_dict.get("thumbnail"),
	#                 video_id = info_dict.get("id"),
	#                 video_title = info_dict.get("title"),
	#                 video_description = info_dict.get("description"),
	#                 video_duration = info_dict.get("duration")

