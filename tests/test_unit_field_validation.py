"""Unit tests for field coordinate validation and signing service field logic."""

import pytest
from pydantic import ValidationError

from dataseal.schemas.field import FieldCreate, FieldUpdate, FieldValueUpdate


class TestFieldCreateValidation:
    def _valid_field(self, **overrides):
        defaults = {
            "recipient_id": "00000000-0000-0000-0000-000000000001",
            "type": "signature",
            "page_number": 1,
            "x_position": 10.0,
            "y_position": 20.0,
            "width": 15.0,
            "height": 5.0,
        }
        defaults.update(overrides)
        return defaults

    def test_valid_field_passes(self):
        field = FieldCreate(**self._valid_field())
        assert field.type == "signature"
        assert field.x_position == 10.0

    def test_all_valid_types_accepted(self):
        valid_types = ["signature", "initials", "date_signed", "text", "checkbox", "dropdown"]
        for t in valid_types:
            field = FieldCreate(**self._valid_field(type=t))
            assert field.type == t

    def test_invalid_type_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(type="invalid_type"))

    def test_x_position_zero_is_valid(self):
        field = FieldCreate(**self._valid_field(x_position=0.0))
        assert field.x_position == 0.0

    def test_x_position_100_is_valid(self):
        field = FieldCreate(**self._valid_field(x_position=100.0))
        assert field.x_position == 100.0

    def test_x_position_negative_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(x_position=-1.0))

    def test_x_position_over_100_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(x_position=100.1))

    def test_y_position_zero_is_valid(self):
        field = FieldCreate(**self._valid_field(y_position=0.0))
        assert field.y_position == 0.0

    def test_y_position_100_is_valid(self):
        field = FieldCreate(**self._valid_field(y_position=100.0))
        assert field.y_position == 100.0

    def test_y_position_negative_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(y_position=-0.1))

    def test_y_position_over_100_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(y_position=101.0))

    def test_width_zero_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(width=0.0))

    def test_width_over_100_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(width=100.1))

    def test_height_zero_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(height=0.0))

    def test_page_number_zero_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(page_number=0))

    def test_page_number_one_is_valid(self):
        field = FieldCreate(**self._valid_field(page_number=1))
        assert field.page_number == 1

    def test_page_number_negative_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(page_number=-1))

    def test_is_required_defaults_to_true(self):
        field = FieldCreate(**self._valid_field())
        assert field.is_required is True

    def test_is_required_can_be_false(self):
        field = FieldCreate(**self._valid_field(is_required=False))
        assert field.is_required is False

    def test_dropdown_options_accepted(self):
        field = FieldCreate(**self._valid_field(type="dropdown", dropdown_options=["Yes", "No"]))
        assert field.dropdown_options == ["Yes", "No"]

    def test_placeholder_max_length_255(self):
        long_placeholder = "x" * 255
        field = FieldCreate(**self._valid_field(placeholder=long_placeholder))
        assert len(field.placeholder) == 255

    def test_placeholder_over_max_length_raises(self):
        with pytest.raises(ValidationError):
            FieldCreate(**self._valid_field(placeholder="x" * 256))


class TestFieldValueUpdate:
    def test_valid_value(self):
        update = FieldValueUpdate(value="signed")
        assert update.value == "signed"

    def test_empty_value_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldValueUpdate(value="")
