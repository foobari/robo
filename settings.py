import json

settings = []

def init(filename):
	global settings
	with open(filename, 'r') as f:
		settings = json.load(f)
	return settings


def get_settings():
	global settings
	return settings