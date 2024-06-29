from django import forms
from .models import InternalUser, PromoHeaders, PromoItemBasketHeaders
from django.db import connection


class UserForm(forms.ModelForm):
    class Meta:
        model = InternalUser
        fields = [
            'UserName',
            'PhoneNumber',
            'Grouping',
            'IsBlocked',
            'LoginName',
            'AreaCode',
            'CityID',
            'RouteCode',
            'ParentCode'
        ]

class AssignPromotionSearchForm(forms.Form):
    promotion_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),  # Default option for no filter
            ('Trade Sales', 'Trade Sales'),
            ('Consumer Sales', 'Consumer Sales'),
            # Add other types as needed
        ],
        required=False,
        label='Promotion Type'
    )
    search_date = forms.DateField(
        required=False,
        label='Search Date',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    filter_type = forms.ChoiceField(
        choices=[('users', 'Users'), ('clients', 'Clients')],
        label='Filter by',
        required=True
    )

    def get_promotion_choices(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT Promotion_ID, Promotion_Description FROM Promo_Headers")
            promotions = cursor.fetchall()
        return [(promo[0], promo[1]) for promo in promotions]

class BasketForm(forms.ModelForm):
    class Meta:
        model = PromoItemBasketHeaders
        fields = ['item_basket_id'
            ,'item_basket_description']
class PromotionSearchForm(forms.Form):
    promotion_id = forms.IntegerField(required=False, label='Promotion ID')
    promotion_description = forms.CharField(max_length=100, required=False, label='Description')
    start_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}), required=False)
    end_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}), required=False)


class NewPromotionForm(forms.Form):
    promotion_description = forms.CharField(
        label='Promotion Description',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    priority = forms.IntegerField(
        label='Priority',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    max_applied = forms.IntegerField(
        label='Max Applied',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    is_active = forms.ChoiceField(
        label='Active',
        choices=[(1, 'Yes'), (0, 'No')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_forced = forms.ChoiceField(
        label='Forced',
        choices=[(1, 'Yes'), (0, 'No')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    promotion_type = forms.ChoiceField(
        label='Promotion Type',
        choices=[('Trade Sales', 'Trade Sales'), ('Consumer Sales', 'Consumer Sales')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    promotion_apply = forms.ChoiceField(
        label='Apply',
        choices=[('ISELL', 'ISELL'), ('E-Ordering', 'E-Ordering'), ('Other', 'Other')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
