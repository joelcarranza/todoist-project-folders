import click
import todoist
from pathlib import Path
from datetime import date

def sanitize_project_name(name):
	name = name.replace(':', '')
	name = name.replace('\\', '')
	name = name.replace('/', '')
	return name

@click.command()
@click.option('--api-key', required=True)
def main(api_key):
	dropbox_home = Path.home() / 'Dropbox'
	projects = dropbox_home / 'Projects'
	archive = dropbox_home / 'Archive'
	today  = date.today()

	api = todoist.TodoistAPI(api_key)
	activity = api.activity.get(object_type='project', limit=100)
	for event in sorted(activity['events'], key=lambda x:x['event_date']):
		# print(event)
		project_event = event['event_type']
		project_name = event['extra_data']['name']
		project_dir = projects / sanitize_project_name(project_name)

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

if __name__ == '__main__':
	main()