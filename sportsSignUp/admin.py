from django.contrib import admin
from .models import Sport, Team, Player, Division , CustomUser, League, StripeProduct, StripePrice, TeamCaptain, Registration, DynamicForm, FormField, FormResponse
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .services import sync_stripe_products

admin.site.register(Sport)
admin.site.register(Player)
admin.site.register(Division)
admin.site.register(CustomUser)
admin.site.register(League)
admin.site.register(Registration)

@admin.register(TeamCaptain)
class TeamCaptainAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number')
    search_fields = ('first_name', 'last_name', 'email')

class PlayerInline(admin.TabularInline):  # You could also use admin.StackedInline for a different layout
    model = Player
    extra = 0  # Number of empty forms to display
    fields = ('first_name', 'last_name', 'email', 'phone_number', 'is_active')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'league', 'division', 'captain', 'needs_real_captain')
    list_filter = ('league', 'division')
    search_fields = ('name', 'captain__first_name', 'captain__last_name')
    inlines = [PlayerInline]

    def needs_real_captain(self, obj):
        return obj.captain.is_system_captain
    needs_real_captain.boolean = True
    needs_real_captain.short_description = 'Needs Captain'
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'team', 'membership_number', 'is_member')
    list_filter = ('is_member', 'is_active', 'team')
    search_fields = ('first_name', 'last_name', 'email', 'membership_number', 'parent_name')
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth', 'parent_name')
        }),
        ('Membership Details', {
            'fields': ('membership_number', 'is_member')
        }),
        ('Team Information', {
            'fields': ('team', 'jersey_number', 'position', 'is_active')
        }),
        ('User Account', {
            'fields': ('user',),
            'classes': ('collapse',)  # Makes this section collapsible in admin
        })
    )
# stripe section 
class StripePriceInline(admin.TabularInline):
    model = StripePrice
    readonly_fields = ('stripe_id', 'currency', 'unit_amount', 'recurring', 
                      'recurring_interval', 'recurring_interval_count', 'active')
    extra = 0
    can_delete = False
    max_num = 0

@admin.register(StripeProduct)
class StripeProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'stripe_id', 'active', 'created_at')
    readonly_fields = ('stripe_id', 'metadata', 'created_at', 'updated_at')
    inlines = [StripePriceInline]
    change_list_template = "admin/sportsSignUp/stripeproduct/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sync-products/', self.sync_products, name='sportsSignUp_stripeproduct_sync'),  # Changed name
        ]
        return custom_urls + urls

    def sync_products(self, request):
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to do this.")
            return redirect('admin:sportsSignUp_stripeproduct_changelist')

        try:
            products_synced, prices_synced = sync_stripe_products()
            messages.success(
                request, 
                f'Successfully synced {products_synced} new products and {prices_synced} new prices from Stripe.'
            )
        except Exception as e:
            messages.error(request, f'Error syncing from Stripe: {str(e)}')

        return redirect('admin:sportsSignUp_stripeproduct_changelist')

@admin.register(StripePrice)
class StripePriceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'stripe_id', 'product', 'active')
    readonly_fields = ('stripe_id', 'product', 'currency', 'unit_amount', 
                      'recurring', 'recurring_interval', 'recurring_interval_count',
                      'metadata', 'created_at', 'updated_at')
    list_filter = ('active', 'recurring', 'recurring_interval')
    search_fields = ('stripe_id', 'product__name')

class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    ordering = ['order']

@admin.register(DynamicForm)
class DynamicFormAdmin(admin.ModelAdmin):
    list_display = ('title', 'league', 'is_active', 'created_at')
    list_filter = ('is_active', 'league')
    search_fields = ('title', 'league__name')
    inlines = [FormFieldInline]

@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'get_league_name', 'created_at')
    list_filter = ('form__league', 'created_at')
    search_fields = ('user__email', 'user__username', 'form__league__name')
    readonly_fields = ('form', 'user', 'registration', 'responses', 'created_at')

    def get_user_name(self, obj):
        return f"{obj.user.get_full_name()} ({obj.user.email})"
    get_user_name.short_description = 'User'

    def get_league_name(self, obj):
        return obj.form.league.name
    get_league_name.short_description = 'League'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def response_details(self, obj):
        """Custom method to display response details in a readable format"""
        html = ['<table style="width:100%">']
        for field in obj.form.fields.all():
            value = obj.responses.get(f'field_{field.id}', 'No response')
            html.append(f'<tr><th style="text-align:left;padding:8px;background:#f5f5f5;">{field.label}</th>')
            html.append(f'<td style="padding:8px;">{value}</td></tr>')
        html.append('</table>')
        return ''.join(html)
    response_details.allow_tags = True

    readonly_fields = ('response_details',)