from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse


# Главная страница
def index(request):
    print()
    print('Hello!!!!!')
    print()
    
    return HttpResponse('<h1 style="color: green;">Главная страница!!!</h1>')


# Страница со списком мороженого
def group_posts(request, pk):
    print()
    print(f'Мы в группах!!! {pk}')
    print()
    print(request, '8888888888')
    print()
    
    
    return HttpResponse(f'Группа {pk}')
