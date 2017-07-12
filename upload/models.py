from django.db import models

class BigFile(models.Model):
    name = models.CharField(max_length=100)
    ready = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now=True)
    stop_time = models.DateTimeField(null=True, default=None)
    #status = models.CharField(choices=[('upnow', 'Is updated now'),
    #                                   ('waitparse', 'Wait parse'),
    #                                   ('parsenow', 'Is parsed now'),
    #                                   ('finish', 'Finished'),
    #                                  ])
    #progress = models.IntegerField()
    result = models.IntegerField(default=0)

