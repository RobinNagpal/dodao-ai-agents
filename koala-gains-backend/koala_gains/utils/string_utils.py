import re


# Exactly same as the typescript implementation we have here
# https://github.com/RobinNagpal/dodao-ui/blob/main/shared/web-core/src/utils/auth/slugify.ts
def slugify(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^\w-]+", "", s)
    s = re.sub(r"-+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s
