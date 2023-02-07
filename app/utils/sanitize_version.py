async def sanitize_version(version: str) -> str:
    parts = []
    for part in version.split('.'):
        if part.isdigit():
            parts.append(part)
        elif part[0].isdigit():
            parts.append(part[0])
        else:
            parts.append('0')
    return '.'.join(parts)