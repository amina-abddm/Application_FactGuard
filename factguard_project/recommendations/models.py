from django.db import models

# Create your models here.

class Article(models.Model):
    THEMES = [
        ('politique', 'Politique'),
        ('finance', 'Finance'),
        ('sport', 'Sport'),
        ('technologie', 'Technologie'),
        ('science', 'Science'),
        ('culture', 'Culture'),
        ('international', 'International'),
        ('sante', 'Santé'),
    ]
    
    title = models.CharField(max_length=200)
    summary = models.TextField()
    theme = models.CharField(max_length=20, choices=THEMES)
    read_time = models.CharField(max_length=10, default="5 min")
    url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Theme(models.Model):
    THEME_CHOICES = [
        ('politique', 'Politique'),
        ('finance', 'Finance'),
        ('sport', 'Sport'),
        ('technologie', 'Technologie'),
        ('science', 'Science'),
        ('culture', 'Culture'),
        ('international', 'International'),
        ('sante', 'Santé'),
    ]
    
    GRADIENTS = [
        ('from-blue-500 to-indigo-600', 'Bleu-Indigo'),
        ('from-green-500 to-emerald-600', 'Vert-Emeraude'),
        ('from-orange-500 to-red-600', 'Orange-Rouge'),
        ('from-purple-500 to-violet-600', 'Violet-Pourpre'),
        ('from-cyan-500 to-blue-600', 'Cyan-Bleu'),
        ('from-pink-500 to-rose-600', 'Rose-Pink'),
        ('from-teal-500 to-cyan-600', 'Teal-Cyan'),
        ('from-red-500 to-pink-600', 'Rouge-Rose'),
    ]
    
    name = models.CharField(max_length=20, choices=THEME_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    emoji = models.CharField(max_length=10)
    gradient = models.CharField(max_length=50, choices=GRADIENTS)
    bg_color = models.CharField(max_length=20, default="bg-primary-50")
    text_color = models.CharField(max_length=20, default="text-primary-700")
    icon_name = models.CharField(max_length=30, default="Building2")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.display_name
