import main
import os,shutil

from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

print(os.environ["GDRIVE_BACKUP_FOLDER"])

def clean_up_tiles():
    size = get_size("tiles")/1000000.0
    if(size > 50):
        for the_file in os.listdir("tiles"):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)
    
def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

main.main()

@sched.scheduled_job('interval', minutes=20)
def timed_job():
    main.main()
    clean_up_tiles()
    print("uploaded")

@sched.scheduled_job('cron', day_of_week='mon-fri', hour=17)
def scheduled_job():
    print('This job is run every weekday at 5pm.')

sched.start()

