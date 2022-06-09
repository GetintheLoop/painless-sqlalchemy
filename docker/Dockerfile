FROM public.ecr.aws/sam/build-python3.9

WORKDIR /user

RUN yum install git vi dbus-python -y

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