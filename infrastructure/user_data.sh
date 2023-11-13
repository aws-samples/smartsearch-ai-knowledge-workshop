#!/bin/sh

#install httpd
yum install httpd -y

#enable and start httpd
systemctl enable httpd
systemctl start httpd
echo "<html><head><title> Example Web Server</title></head>" >  /var/www/html/index.html
echo "<body>" >>  /var/www/html/index.html
echo "<div><center><h2>Welcome AWS $(hostname -f) </h2>" >>  /var/www/html/index.html
echo "<hr/>" >>  /var/www/html/index.html
curl http://169.254.169.254/latest/meta-data/instance-id >> /var/www/html/index.html
echo "</center></div></body></html>" >>  /var/www/html/index.html


##!/bin/sh
#
#REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
#account=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .accountId)
#
### login
#docker login --username AWS --password $(aws ecr get-login-password --region ${REGION}) ${account}.dkr.ecr.${REGION}.amazonaws.com
#aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${account}.dkr.ecr.${REGION}.amazonaws.com
#
### pull image
#docker pull ${account}.dkr.ecr.${REGION}.amazonaws.com/llm_smart_search:latest
#
### run the image
#docker run --gpus '"device=0"' -p 5000:5000 -it -d --restart=on-failure ${account}.dkr.ecr.${REGION}.amazonaws.com/llm_smart_search:latest
#
#
#
## -------------
## #!/bin/sh
#
## REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
## account=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .accountId)
## docker login --username AWS --password $(aws ecr get-login-password --region ${REGION}) 727897471807.dkr.ecr.${REGION}.amazonaws.com.cn
## aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${account}.dkr.ecr.${REGION}.amazonaws.com.cn
#
## docker pull --verbose ${account}.dkr.ecr.${REGION}.amazonaws.com.cn/llm_smart_search:latest
#
## docker run --gpus '"device=0"' -p 5000:5000 -it -d --restart=on-failure ${account}.dkr.ecr.${REGION}.amazonaws.com.cn/llm_smart_search:latest
