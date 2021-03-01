import click
import todoist
from pathlib import Path
from datetime import date
from datetime import datetime
import shelve
from datetime import timezone

def sanitize_project_name(name):
	name = name.replace(':', '')
	name = name.replace('\\', '')
	name = name.replace('/', '')
	return name

@click.group()
def main():
	pass

@main.command()
def init():
	api_key = click.prompt('API Key')
	with shelve.open(str(Path.home() / '.todoist-project-folders')) as db:
		db['api_key'] = api_key
		db['baseline'] = datetime.now(tz=timezone.utc)

@main.command()
def manage():
	dropbox_home = Path.home() / 'Dropbox'
	projects = dropbox_home / 'Projects'
	archive = dropbox_home / 'Archive'
	today  = date.today()
	now = datetime.now(tz=timezone.utc)

	with shelve.open(str(Path.home() / '.todoist-project-folders')) as db:
		baseline = db.get('baseline')
		api_key = db['api_key']
		api = todoist.TodoistAPI(api_key)
		activity = api.activity.get(object_type='project', limit=100)
		for event in sorted(activity['events'], key=lambda x:x['event_date']):
			project_event = event['event_type']
			project_name = event['extra_data']['name']
			project_dir = projects / sanitize_project_name(project_name)
			event_date = datetime.strptime(event['event_date'], '%Y-%m-%dT%H:%M:%S%z')
			if baseline and event_date < baseline:
				continue
			if project_event == 'archived':
				if project_dir.is_dir():
					has_content = False
					for p in project_dir.iterdir():
						has_content = True
					if has_content:
						archive_dir = archive / '{:04d}{:02d}{:02d} {}'.format(today.year, today.month, today.day, sanitize_project_name(project_name))
						print("Moving ",project_dir,"to",archive_dir)
						project_dir.rename(archive_dir)
					else:
						print("Deleting ",project_dir)
						project_dir.rmdir()
			if project_event == 'deleted':
				if project_dir.is_dir():
					print("Deleting ",project_dir)
					project_dir.rmdir() # this may fail if not-empty
			elif project_event == 'added' or project_event == 'unarchived':
				if not project_dir.exists():
					print("Creating ",project_dir)
					project_dir.mkdir()
		db['baseline'] = now

if __name__ == '__main__':
	main()