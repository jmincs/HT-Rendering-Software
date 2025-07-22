from django.db import models

class ProcessedFile(models.Model):
    name = models.CharField(max_length=255)
    size = models.FloatField() 
    date_processed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class StagedFile(models.Model):
    tcf_file_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.staged_file_name} (TCF: {self.tcf_file_name})"