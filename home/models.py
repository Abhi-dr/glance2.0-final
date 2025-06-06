from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
class Company_Carousel(models.Model):
    image = models.ImageField(upload_to='corousel/')
    day = models.IntegerField(choices=[(1, 'Day 1'), (2, 'Day 2'), (3, 'Day 3')], default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Company Carousel - Day {self.day}"