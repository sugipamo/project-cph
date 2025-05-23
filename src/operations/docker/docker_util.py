class DockerUtil:
    @staticmethod
    def build_docker_cmd(base_cmd, options=None, positional_args=None):
        """
        base_cmd: list[str] 例 ["docker", "run"]
        options: dict 例 {"name": "mycontainer", "d": None}
        positional_args: list[str] 例 ["ubuntu:latest"]
        """
        cmd = list(base_cmd)
        if options:
            for k, v in options.items():
                if len(k) == 1:
                    cmd.append(f"-{k}")
                else:
                    cmd.append(f"--{k.replace('_','-')}")
                if v is not None:
                    cmd.append(str(v))
        if positional_args:
            cmd += positional_args
        return cmd

    @staticmethod
    def parse_image_tag(image):
        """
        イメージ名:タグを分離して返す
        """
        if ':' in image:
            return image.split(':', 1)
        return image, None 