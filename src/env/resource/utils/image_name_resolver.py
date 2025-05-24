import hashlib

class ImageNameResolver:
    def __init__(self, config):
        self.config = config

    @property
    def image_name(self) -> str:
        language = self.config.language
        dockerfile_text = self.config.dockerfile
        if not dockerfile_text:
            return language
        hash_str = hashlib.sha256(dockerfile_text.encode("utf-8")).hexdigest()[:12]
        return f"{language}_{hash_str}"

    @property
    def container_name(self) -> str:
        return f"cph_{self.image_name}"

    @property
    def base_image_name(self) -> str:
        return self.config.language

    @property
    def base_oj_image_name(self) -> str:
        return "ojtools"

    @property
    def oj_image_name(self) -> str:
        oj_dockerfile_text = self.config.oj_dockerfile
        if not oj_dockerfile_text:
            return self.base_oj_image_name
        hash_str = hashlib.sha256(oj_dockerfile_text.encode("utf-8")).hexdigest()[:12]
        return f"{self.base_oj_image_name}_{hash_str}"

    @property
    def oj_container_name(self) -> str:
        return f"cph_{self.oj_image_name}"

    @property
    def dockerfile_text(self) -> str:
        return self.config.dockerfile

    @property
    def oj_dockerfile_text(self) -> str:
        return self.config.oj_dockerfile 