from django.contrib import admin

# Register your models here.

from .models import Question, PDFOCRData, UserProfile, V_Patient_Surgery, V_Patient_Diagnosis, ChatSessions, ChatMessages, Feedback

admin.site.register(Question)
admin.site.register(PDFOCRData)
admin.site.register(UserProfile)
admin.site.register(V_Patient_Surgery)
admin.site.register(V_Patient_Diagnosis)
admin.site.register(ChatSessions)
admin.site.register(ChatMessages)
admin.site.register(Feedback)