from datetime import datetime
from telegram_quote_bot.utils import get_job_dict


class JobHandler:
    def __init__(self):
        self.job_dict = get_job_dict()

    def get_due_jobs(self):
        due_jobs = []
        for row_id, job in self.job_dict.items():
            if job['interval'] == 'daily' and (
                    job['last_sent_on_date'] is None or (datetime.strptime(job['last_sent_on_date'], '%Y-%m-%d').date()
                                                         < datetime.now().date() and (job['to_send_at_time'] is None
                                                                                      or datetime.now().time()
                                                                                      > job['to_send_at_time']))):
                due_jobs.append(job)
            elif (job['interval'] == 'on fiehe pl' and job['msg_text'] is not None) or job['interval'] is None:
                due_jobs.append(job)
        return due_jobs

    def update(self):
        self.job_dict = get_job_dict()
