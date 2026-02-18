"""Marshmallow schemas for validation and serialization."""

from marshmallow import Schema, fields, validate, validates, ValidationError


class UserSchema(Schema):
    """Schema for User model."""

    id = fields.Int(dump_only=True)
    email = fields.Email(required=True, validate=validate.Length(max=255))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    created_at = fields.DateTime(dump_only=True)

    @validates("email")
    def validate_email_format(self, value, **kwargs):
        """Ensure email is valid format."""
        if not value or not value.strip():
            raise ValidationError("Email cannot be empty.")
        return value

    @validates("name")
    def validate_name(self, value, **kwargs):
        """Ensure name is not empty or whitespace-only."""
        if not value or not value.strip():
            raise ValidationError("Name cannot be empty.")
        return value.strip()


class UserCreateSchema(Schema):
    """Schema for creating a user (no id, created_at)."""

    email = fields.Email(required=True, validate=validate.Length(max=255))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))

    @validates("name")
    def validate_name(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Name cannot be empty.")
        return value.strip()


class UserUpdateSchema(Schema):
    """Schema for updating a user (all fields optional)."""

    email = fields.Email(validate=validate.Length(max=255))
    name = fields.Str(validate=validate.Length(min=1, max=255))

    @validates("name")
    def validate_name(self, value, **kwargs):
        if value is not None and (not value or not value.strip()):
            raise ValidationError("Name cannot be empty.")
        return value.strip() if value else value
