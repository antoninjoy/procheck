from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomSignUpForm(UserCreationForm):
    # 1. Add First Name and Last Name
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # 2. Your Email and Phone fields
    email = forms.EmailField(required=True, help_text='Required. Inform a valid email address.')
    phone = forms.CharField(max_length=10, required=True, help_text='Required. 10 digit phone number.')

    # 3. FORCE THE EXACT FIELD ORDER HERE:
    # Django will automatically put the password and password confirmation fields at the very end.
    field_order = ['first_name', 'last_name', 'username', 'email', 'phone']

    class Meta(UserCreationForm.Meta):
        model = User
        # Tell Django's User model about the built-in fields we are using
        fields = ('first_name', 'last_name', 'username', 'email') 

    def save(self, commit=True):
        # Save the basic user data first
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # NOTE: The phone number is extracted here, but it requires a custom 
            # Profile model in your database to actually save it permanently.
            phone_number = self.cleaned_data['phone']
            
        return user