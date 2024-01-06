## Getting Started

First, we have to install **virtualenv** to start the project in command prompt.
```
pip install virtualenv
```

Then, we need to create virtualenv by running below code:
```
virtualenv <name_of_your_environment>
```

After installation we need to activate virtualenv by running:
```
.\env\Scripts\activate
```

Once virtualenv is activated.
Execute these commands to build your Django project

```
pip install django
django-admin startproject <project_name>
python manage.py startapp <app_name>
python manage.py createsuperuser
```

FInally, after executing all these steps you should keep your file structure similar to these project.
Then run these command to **migarte** all the changes/
```
python manage.py migrate
```

Now, to start with running your application run this command:
```
python manage.py runserver
```

## Start your development 

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) with your browser to see the result and [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) to access the database.

## Glimpse of Django-App

![image](https://github.com/sundaram-rai/django-erp-attendance/assets/98939843/f4e8f83b-ab57-4127-b87c-f7c7a4307e48) 
![image](https://github.com/sundaram-rai/django-erp-attendance/assets/98939843/cb06b294-d73a-4d1f-9c18-ec58b294eb29)
![image](https://github.com/sundaram-rai/django-erp-attendance/assets/98939843/1fff7ab7-3e44-45a1-bde8-b554e44e1ab7)
![image](https://github.com/sundaram-rai/django-erp-attendance/assets/98939843/799bb8ab-45a9-482c-ba1c-42ae8d88640d)



