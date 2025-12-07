from django import forms
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth import get_user_model

from .models import Profile, User, PasswordResetOTP

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="We'll never share your email.")
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, required=True)
    phone = forms.CharField(max_length=15, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered. Please sign in instead.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.phone = self.cleaned_data.get("phone") or ""
        if commit:
            user.save()
            profile = getattr(user, "profile", None) or Profile.objects.create(user=user)
            profile.role = self.cleaned_data["role"]
            profile.save()
        else:
            user._profile_role = self.cleaned_data["role"]
        return user


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, label="First Name")
    last_name = forms.CharField(max_length=150, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email")
    # Profile fields
    date_of_birth = forms.DateField(
        required=False, 
        label="Date of Birth",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        choices=[
            ('', 'Select Gender'),
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('prefer_not_to_say', 'Prefer not to say'),
        ],
        required=True,
        label="Gender",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    course_year = forms.CharField(
        max_length=100, 
        required=False, 
        label="Course / Year",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., B.Tech CSE 3rd Year'})
    )
    profile_photo = forms.ImageField(
        required=False,
        label="Profile Photo",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['email'].initial = self.instance.email
            # Set profile fields initial values
            try:
                if hasattr(self.instance, 'profile'):
                    profile = self.instance.profile
                    # Safely get profile fields (in case migration hasn't run yet)
                    self.fields['date_of_birth'].initial = getattr(profile, 'date_of_birth', None)
                    self.fields['gender'].initial = getattr(profile, 'gender', None)
                    self.fields['course_year'].initial = getattr(profile, 'course_year', None)
            except Exception:
                # If profile doesn't exist or fields don't exist yet, just skip
                pass

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"].lower()
        if commit:
            user.save()
            # Update profile fields
            try:
                # Get or create profile to ensure it exists
                profile, created = Profile.objects.get_or_create(user=user)
                # Update profile fields
                profile.date_of_birth = self.cleaned_data.get('date_of_birth') or None
                profile.gender = self.cleaned_data.get('gender') or None
                profile.course_year = self.cleaned_data.get('course_year') or None
                # Save profile photo if provided
                if 'profile_photo' in self.cleaned_data and self.cleaned_data['profile_photo']:
                    profile.profile_photo = self.cleaned_data['profile_photo']
                profile.save()
            except Exception as e:
                # Log error for debugging but don't break the form
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving profile: {e}")
        return user


class PasswordResetRequestForm(forms.Form):
    """Form to request OTP for password reset"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address'}),
        help_text="We'll send an OTP to this email address."
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("No account found with this email address.")
        return email


class OTPVerificationForm(forms.Form):
    """Form to verify OTP"""
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter 6-digit OTP', 'maxlength': '6', 'pattern': '[0-9]{6}'}),
        help_text="Enter the 6-digit OTP sent to your email."
    )
    email = forms.EmailField(widget=forms.HiddenInput())
    
    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        if not otp.isdigit():
            raise forms.ValidationError("OTP must contain only numbers.")
        return otp
    
    def clean(self):
        cleaned_data = super().clean()
        otp = cleaned_data.get('otp')
        email = cleaned_data.get('email')
        
        if otp and email:
            # Get the most recent unverified OTP for this email
            otp_obj = PasswordResetOTP.objects.filter(
                email=email,
                otp=otp,
                is_verified=False
            ).order_by('-created_at').first()
            
            if not otp_obj:
                raise forms.ValidationError("Invalid OTP. Please check and try again.")
            
            if otp_obj.is_expired():
                raise forms.ValidationError("OTP has expired. Please request a new one.")
        
        return cleaned_data


class PasswordResetForm(SetPasswordForm):
    """Form to set new password after OTP verification"""
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password'}),
        help_text="Your password must contain at least 8 characters."
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'}),
        help_text="Enter the same password as before, for verification."
    )
