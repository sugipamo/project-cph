FROM python:3.11-slim

RUN pip install --no-cache-dir online-judge-tools

RUN useradd -m -u 1000 oj-user && \
    mkdir -p /home/oj-user/.local/share/online-judge-tools && \
    echo "#LWP-Cookies-2.0" > /home/oj-user/.local/share/online-judge-tools/cookie.jar && \
    chown -R oj-user:oj-user /home/oj-user && \
    chmod 600 /home/oj-user/.local/share/online-judge-tools/cookie.jar

WORKDIR /workspace

USER oj-user