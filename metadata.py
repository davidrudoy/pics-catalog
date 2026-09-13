"""
Step 2: EXIF extraction. Uses exifread, which parses the TIFF-based tag
structure shared by JPEG and RAW formats (ARW/RW2 are both TIFF-based) —
no need for a separate RAW-specific metadata reader.
"""
import exifread


def _to_str(tags, key):
    value = tags.get(key)
    return str(value) if value is not None else None


def _to_int(tags, key):
    value = tags.get(key)
    if value is None:
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def extract_exif(path) -> dict:
    with open(path, "rb") as f:
        tags = exifread.process_file(f, details=False)

    return {
        "date_taken": _to_str(tags, "EXIF DateTimeOriginal") or _to_str(tags, "Image DateTime"),
        "camera_make": _to_str(tags, "Image Make"),
        "camera_model": _to_str(tags, "Image Model"),
        "lens": _to_str(tags, "EXIF LensModel"),
        "exposure_time": _to_str(tags, "EXIF ExposureTime"),
        "aperture": _to_str(tags, "EXIF FNumber"),
        "iso": _to_int(tags, "EXIF ISOSpeedRatings"),
        "focal_length": _to_str(tags, "EXIF FocalLength"),
    }
