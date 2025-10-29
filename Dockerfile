#---------BASE IMAGE---------
    FROM ubuntu:20.04

    #---------LABELS---------
    LABEL maintainer="Aditya Kale"
    LABEL image="digitaltiranga:1.0"
    LABEL version="2.0"
    LABEL description="Dockerfile for jirasync"
    
    #---------ENVIRONMENT VARIABLES---------
    ENV DEBIAN_FRONTEND=noninteractive
    ENV HOME_DIR=/var/www/FLASKAPPS/digital
    
    #---------COPY FOLDERS---------
    COPY requirements.txt /tmp/
    COPY ./ /var/www/FLASKAPPS/digital
    
    #---------APP DEPENDENCIES---------
    RUN apt-get clean && apt-get update -y \
        && apt-get install -y python3 python3-pip apache2 libapache2-mod-wsgi-py3 libpq-dev \
        && ln -s /usr/bin/python3 /usr/bin/python
    
    # Install basic fonts (e.g., DejaVu fonts which are commonly used)
    RUN apt-get install -y fontconfig ttf-dejavu
    
    # Additional Python dependencies
    RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python3-dev
    RUN pip install flask flask-socketio textblob reportlab requests Pillow pygame
    
    #---------SET WORKING DIRECTORY---------
    WORKDIR /var/www/FLASKAPPS/digital
    
    #---------RUN THE APPLICATION---------
    # Ensure proper permissions
    RUN chmod -R 755 /var/www/FLASKAPPS/digital
    
    # Expose port 80 for incoming traffic
    EXPOSE 80
    
    # Start the app using Python
    CMD ["python", "app.py"]
    
    # To build the Docker image:
    # docker build --tag digital:1.3 -f Dockerfile .
    
