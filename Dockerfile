FROM python:3.8

# update pip
RUN pip install --upgrade pip

# copy in local files
ADD . .

# install dependencies
RUN pip install -r requirements.txt

# initialize DB
RUN python init_db.py

# expose port
EXPOSE 3111

CMD ["python", "app.py"]