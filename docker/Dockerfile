FROM lambci/lambda:build-python3.6

WORKDIR /user

RUN yum install git vi -y

# set home directory allow access to "user" folder
ENV HOME /user
ENV USERPROFILE /user
RUN chmod 757 /user

# set correct execution env
ENV LAMBDA_TASK_ROOT /user/project

COPY requirements.txt /user/requirements.txt
RUN pip install -r /user/requirements.txt
RUN rm /user/requirements.txt

ENTRYPOINT (cd /user/project && bash)