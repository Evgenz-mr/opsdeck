FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd -r -m -u 10001 -g users opsdeck
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY config ./config
COPY actions ./actions
COPY runbooks ./runbooks
RUN mkdir -p /data /home/opsdeck/.kube /home/opsdeck/.ssh \
    && chown -R opsdeck:users /data /app /home/opsdeck
USER opsdeck
EXPOSE 8080
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
