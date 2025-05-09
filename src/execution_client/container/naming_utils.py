def generate_container_name(purpose: str, language: str = None, index: int = None, prefix: str = "cph") -> str:
    parts = [prefix, purpose]
    if language:
        parts.append(language)
    if index is not None:
        parts.append(str(index))
    return "_".join(parts) 