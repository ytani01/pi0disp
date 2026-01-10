import pytest

from pi0disp.utils.sprite import Sprite


class MockSprite(Sprite):
    __slots__ = ()

    def update(self, delta_t):
        pass

    def draw(self, draw):
        draw.rectangle(self.bbox, fill=(255, 255, 255))


def test_sprite_slots():
    sprite = MockSprite(0, 0, 10, 10)
    with pytest.raises(AttributeError):
        sprite.new_attr = 1  # type: ignore[attr-defined] # __slots__ should prevent this


def test_sprite_dirty_logic():
    sprite = MockSprite(10, 10, 20, 20)

    # Initially dirty (prev_bbox is None)
    # Added 2-pixel margin
    assert sprite.get_dirty_region() == (8, 8, 32, 32)

    sprite.record_current_bbox()
    # Now not dirty
    assert sprite.get_dirty_region() is None

    # Move sprite
    sprite.x = 15
    # merged (10,10,30,30) and (15,10,35,30) = (10, 10, 35, 30)
    # plus 2-pixel margin = (8, 8, 37, 32)
    assert sprite.get_dirty_region() == (
        8,
        8,
        37,
        32,
    )

    sprite.record_current_bbox()
    assert sprite.get_dirty_region() is None


def test_sprite_properties():
    sprite = MockSprite(0, 0, 10, 10)
    sprite.x = 5
    sprite.y = 5
    sprite.width = 20
    sprite.height = 20
    assert sprite.bbox == (5, 5, 25, 25)
    assert sprite._dirty is True


def test_circle_sprite():
    from pi0disp.utils.sprite import CircleSprite

    class MockCircle(CircleSprite):
        __slots__ = ()

        def update(self, delta_t):
            pass

        def draw(self, draw):
            pass

    circle = MockCircle(cx=100, cy=100, radius=20)
    # bbox should be (80, 80, 120, 120)
    assert circle.bbox == (80, 80, 120, 120)

    # cx, cy, radius properties
    circle.cx = 150
    assert circle.x == 130
    assert circle.cx == 150

    circle.radius = 30
    assert circle.bbox == (120, 70, 180, 130)
    assert circle._dirty is True


def test_sprite_no_change_no_dirty():
    sprite = MockSprite(0, 0, 10, 10)
    sprite.record_current_bbox()

    # Setting the same value should not trigger dirty
    sprite.x = 0
    assert sprite._dirty is False
    assert sprite.get_dirty_region() is None

    sprite.x = 1  # change
    assert sprite._dirty is True
    assert sprite.get_dirty_region() is not None
