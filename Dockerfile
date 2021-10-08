# Pull the base image with python 3.8 as a runtime for your Lambda
FROM public.ecr.aws/lambda/python:3.8

# Replace "Neptune.ai technical guide" with your name and email address
LABEL maintainer="Stephen Oladele <steve.deve89@gmail.com>"
LABEL version="1.0"
LABEL description="Demo flower classification application for serverless deployment."

# Install OS packages for Pillow-SIMD
RUN yum -y install tar gzip zlib freetype-devel \
    gcc \
    ghostscript \
    lcms2-devel \
    libffi-devel \
    libimagequant-devel \
    libjpeg-devel \
    libraqm-devel \
    libtiff-devel \
    libwebp-devel \
    make \
    openjpeg2-devel \
    rh-python36 \
    rh-python36-python-virtualenv \
    sudo \
    tcl-devel \
    tk-devel \
    tkinter \
    which \
    xorg-x11-server-Xvfb \
    zlib-devel \
    && yum clean all

# Copy the earlier created requirements.txt file to the container
COPY requirements.txt ./

# Install the python requirements from requirements.txt
RUN python3.8 -m pip install -r requirements.txt
# Replace Pillow with Pillow-SIMD to take advantage of AVX2
RUN pip uninstall -y pillow && CC="cc -mavx2" pip install -U --force-reinstall pillow-simd

# Copy the earlier created app.py file to the container
COPY app.py ./

# Download the model from the public object store (S3) and save it inor ./model as model.tar.gz
# Extract it to the model/ directoty
# Remove the compressed file from the directory leaving only the extracted files
RUN mkdir model
RUN curl -L https://flower-app-serverless.s3.us-east-2.amazonaws.com/model/model.tar.gz -o ./model/model.tar.gz
RUN tar -xf model/model.tar.gz -C model/
RUN rm -r model/model.tar.gz


# Set the CMD to your handler
CMD ["app.lambda_handler"]