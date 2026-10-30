from django.contrib import admin

from .models import TitikCOD, TransaksiCOD, Ulasan
#from .models import Module 3 list
#admin.site.register(Module 3 list)
admin.site.register(TitikCOD)
admin.site.register(TransaksiCOD)
admin.site.register(Ulasan)