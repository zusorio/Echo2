FROM python:3
ADD ./ /bot/
WORKDIR /bot
RUN pip install -r requirements.txt
CMD ["python3", "main.py"]