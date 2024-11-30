from django.contrib import admin
from .models import Sport, Team, Player, Division , CustomUser, League
# Register your models here.
admin.site.register(Sport)
admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Division)
admin.site.register(CustomUser)
admin.site.register(League)
