## 本地部署

+ 前提本地安装python3.9以上版本、mysql数据库、redis数据库

### 创建虚拟环境
+ 虚拟环境创建、进入
```shell
python3 -m venv venv

source venv/bin/activate
```
+ 安装依赖
```shell
pip install -r requirement.txt
```

### 创建配置文件
+ 在项目根目录下创建一个`config.yaml`文件
+ 配置文件内容如下，需要修改的只是本机数据库的用户名密码，Django的密码, AI_API密钥
```yaml
database:
  engine: 'django.db.backends.mysql'
  name: 'aijc'
  host: 'localhost'
  port: '3306'
  user: ''
  password: ''

openai:
    api_key: ""
    base_url: "https://aihubmix.com/v1"

aliyun_sms:
    access_key_id: ''
    access_key_secret: ''
    sign_name: '数据库大作业'
    template_code: 'SMS_475910001'

django_secret_key: ''
```

### 迁移数据库
+ 现在本地mysql建立数据库aijc
```sql
CREATE DATABASE aijc;
```

+ 在项目根目录下运行，会自动创建数据表，可在本地查看下
```shell
python manage.py makemigrations
python manage.py migrate
```

### 运行项目
+ 在项目根目录下运行
```shell
python manage.py runserver
```

