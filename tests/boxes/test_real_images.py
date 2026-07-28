from pathlib import Path

import cv2
import pytest

from boxes.detect_boxes import detect_boxes


SAMPLES = Path(__file__).parents[2] / "images_samples"


@pytest.mark.parametrize(
    ("relative_path", "expected_boxes", "expected_signed"),
    [
        ("both_signed.jpeg", 2, 2),
        ("one_signed.jpeg", 2, 1),
        ("one_signed_worst_quality.jpeg", 2, 1),
        ("not_signed.jpeg", 2, 0),
        ("weird_angles/4_boxes_2_signed_1.jpeg", 4, 2),
        ("weird_angles/4_boxes_2_signed_2.jpeg", 4, 2),
        ("weird_angles/4_boxes_2_signed_3.jpeg", 4, 2),
        ("weird_angles/4_boxes_2_signed_4.jpeg", 4, 2),
    ],
)
async def test_real_photo_detection(relative_path, expected_boxes, expected_signed):
    image = cv2.imread(str(SAMPLES / relative_path), cv2.IMREAD_COLOR)
    assert image is not None

    boxes = await detect_boxes(image)

    assert len(boxes) == expected_boxes
    assert sum(box["is_signed"] for box in boxes) == expected_signed
    assert all(box["box_id"] is not None for box in boxes)


async def test_random_photo_has_no_boxes():
    image = cv2.imread(str(SAMPLES / "random_image.jpg"), cv2.IMREAD_COLOR)
    assert image is not None

    assert await detect_boxes(image) == []
