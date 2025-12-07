from __future__ import annotations

from decimal import Decimal

from django import forms

from .models import Course


class CourseForm(forms.ModelForm):
    """Validated form for creating/updating courses with user-friendly widgets."""

    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "learning_outcomes",
            "category",
            "level",
            "thumbnail",
            "promo_video_url",
            "status",
            "price",
            "discounted_price",
            "duration",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg",
                    "maxlength": 200,
                    "placeholder": "e.g., Complete Python Mastery: From Zero to Hero",
                    "required": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control description-textarea",
                    "rows": 10,
                    "placeholder": (
                        "Describe what students will learn, what skills they'll gain, "
                        "and why this course is valuable."
                    ),
                    "required": False,
                }
            ),
            "learning_outcomes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": (
                        "List the key learning outcomes (one per line):\n"
                        "• Master Python fundamentals\n"
                        "• Build real-world applications\n"
                        "• Understand advanced concepts"
                    ),
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-select form-select-lg",
                    "required": True,
                }
            ),
            "level": forms.Select(
                attrs={
                    "class": "form-select form-select-lg",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select form-select-lg",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                    "placeholder": "Enter price (required)",
                    "required": True,
                }
            ),
            "discounted_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "duration": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 6 weeks, 10 hours, 4 months",
                }
            ),
            "promo_video_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID",
                }
            ),
        }

    def clean_title(self) -> str:
        title = (self.cleaned_data.get("title") or "").strip()
        if len(title) < 10:
            raise forms.ValidationError(
                "Course titles should be at least 10 characters so students understand the topic."
            )
        return title

    def clean_description(self) -> str:
        description = (self.cleaned_data.get("description") or "").strip()
        # Make description optional - only validate if provided
        if description and len(description) < 50:
            raise forms.ValidationError(
                "If provided, description should be at least 50 characters so learners know what to expect from the course."
            )
        return description

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get("thumbnail")
        if thumbnail and thumbnail.size > 2 * 1024 * 1024:  # 2MB
            raise forms.ValidationError("Thumbnails must be 2MB or smaller.")
        return thumbnail

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        discounted_price = cleaned_data.get("discounted_price")

        # Price is required and must be greater than 0
        if price is None:
            self.add_error("price", "Price is required and must be greater than $0.00. All courses must be paid courses.")
        elif isinstance(price, Decimal) and price <= Decimal("0"):
            self.add_error("price", "Price is required and must be greater than $0.00. All courses must be paid courses.")
        else:
            cleaned_data["price"] = price
            
        if discounted_price is None:
            discounted_price = price
            cleaned_data["discounted_price"] = discounted_price

        if price and isinstance(price, Decimal) and price < Decimal("0"):
            self.add_error("price", "Price cannot be negative.")

        if discounted_price and isinstance(discounted_price, Decimal) and discounted_price < Decimal("0"):
            self.add_error("discounted_price", "Discounted price cannot be negative.")

        if discounted_price and price and isinstance(discounted_price, Decimal) and isinstance(price, Decimal) and discounted_price > price:
            self.add_error(
                "discounted_price",
                "Discounted price must be less than or equal to the regular price.",
            )

        return cleaned_data



