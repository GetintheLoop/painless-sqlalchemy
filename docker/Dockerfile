FROM lambci/lambda:build-python3.6

WORKDIR /user

ENV NVM_DIR /user/.nvm

# prevent npm update notifications
ENV NO_UPDATE_NOTIFIER 0

RUN yum install git vi -y \
  && curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.6/install.sh | bash \
  && . /user/.nvm/nvm.sh \
  && nvm install 9 \
  && npm install -g grunt serverless npm-check-updates npm-manager \
  && npm install -g npm@6.1.0

# allow npm cache access for user
RUN mkdir /.npm
RUN chmod -R 757 /.npm

# set home directory allow access to "user" folder
ENV HOME /user
ENV USERPROFILE /user
RUN chmod 757 /user

# set correct execution env
ENV LAMBDA_TASK_ROOT /user/project

COPY requirements.txt /user/requirements.txt
RUN pip install -r /user/requirements.txt
RUN rm /user/requirements.txt

ENTRYPOINT (. /user/.nvm/nvm.sh && cd /user/project && bash)