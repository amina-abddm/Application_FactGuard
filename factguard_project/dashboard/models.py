# dashboard/models.py
from django.db import models
from django.contrib.auth.models import User

class Analysis(models.Model):
    TYPE_CHOICES = [
        ('text', 'Texte'),
        ('link', 'Lien'),
        ('image', 'Image'),
    ]
    
    text = models.TextField(verbose_name="Texte analysé")
    result = models.TextField(verbose_name="Résultat de l'analyse")
    confidence_score = models.FloatField(default=0.0, verbose_name="Score de confiance")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    content_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text', verbose_name="Type de contenu")  # ✅ NOUVEAU CHAMP
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Analyse"
        verbose_name_plural = "Analyses"
    
    def __str__(self):
        return f"Analyse de {self.user.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def reliability_level(self):
        """Retourne le niveau de fiabilité en texte"""
        if self.confidence_score >= 0.8:
            return "Très fiable"
        elif self.confidence_score >= 0.6:
            return "Fiable"
        elif self.confidence_score >= 0.4:
            return "Peu fiable"
        else:
            return "Non fiable"
    
    @property
    def type_display(self):
        """Retourne le type lisible"""
        return dict(self.TYPE_CHOICES).get(self.content_type, self.content_type)
    
    @property
    def type_icon(self):
        """Retourne l'icône correspondant au type"""
        icons = {
            'text': 'fas fa-file-alt',
            'link': 'fas fa-link', 
            'image': 'fas fa-image'
        }
        return icons.get(self.content_type, 'fas fa-file')
