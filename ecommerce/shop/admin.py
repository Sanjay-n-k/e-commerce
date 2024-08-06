from django.contrib import admin
from .models import Product, Order

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'product', 'quantity', 'phone_number', 'payment_status')
    list_filter = ('payment_status',)
    search_fields = ('order_id', 'user__username', 'product__name')

admin.site.register(Product)
admin.site.register(Order, OrderAdmin)


