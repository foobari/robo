import json

settings = []

def init(filename):
	global settings
	print("open settings file", filename)
	with open(filename, 'r') as f:
		settings = json.load(f)
	return settings


def get_settings():
	global settings
	return settings